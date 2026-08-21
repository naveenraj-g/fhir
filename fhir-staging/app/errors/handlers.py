"""Exception handlers — every error leaves this service as the same JSON shape.

fhir-server renders errors as a FHIR `OperationOutcome`, because everything it
returns is FHIR. This service has no FHIR wire format at all (the standard
governs the *table* shape here, not the responses), so an OperationOutcome
would be the only FHIR object a caller ever saw. The envelope is plain instead:

    {"error": {"code": "NOT_FOUND", "message": "...", "metadata": {...}}}

`code` is the stable machine-readable string off ApplicationError; `message` is
for humans. Field-level validation failures add a `details` list, one entry per
bad field, so a caller can map failures back to their input.

Two rules carried over from fhir-server and worth keeping:
  - 5xx never leaks `exc.message` to the client — internal detail goes to the
    log, "Internal server error" goes over the wire.
  - Every response echoes X-Request-ID when there is one, so a caller can quote
    it and have the matching log line found instantly.
"""

from typing import Any

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import JSONResponse

from app.core.logging import get_logger
from app.core.request_context import request_id_ctx_var
from app.errors.base import ApplicationError
from app.errors.validation import InputValidationError

logger = get_logger(__name__)


def _base_log_payload(request: Request) -> dict[str, Any]:
    return {
        "method": request.method,
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "client_ip": request.client.host if request.client else None,
    }


def get_request_id(request: Request) -> str | None:
    """Prefers the ContextVar over request.state — an error handler must never
    itself raise, and request.state.request_id is unset whenever the
    request-context middleware didn't run (e.g. an exception raised in a
    middleware layered above it)."""
    return request_id_ctx_var.get() or getattr(request.state, "request_id", None)


def _error_response(
    status_code: int,
    code: str,
    message: str,
    request_id: str | None,
    *,
    metadata: dict | None = None,
    details: list[dict] | None = None,
) -> JSONResponse:
    error: dict[str, Any] = {"code": code, "message": message}
    if metadata:
        error["metadata"] = metadata
    if details:
        error["details"] = details
    return JSONResponse(
        status_code=status_code,
        content={"error": error},
        headers=({"X-Request-ID": request_id} if request_id else None),
    )


# -------------------------------------------------------
# ApplicationError (domain errors)
# -------------------------------------------------------
async def application_error_handler(request: Request, exc: ApplicationError):
    payload = _base_log_payload(request)
    is_server_error = exc.status_code >= 500
    request_id = get_request_id(request)

    payload.update(
        {
            "error_name": exc.name,
            "error_code": exc.code,
            "status_code": exc.status_code,
            "metadata": exc.metadata,
        }
    )

    if isinstance(exc, InputValidationError):
        logger.info(
            "Input validation failed",
            extra={**payload, "event": "error.input_validation"},
        )
        return _error_response(
            400,
            exc.code,
            exc.message,
            request_id,
            details=[
                {"field": error["field"], "message": error["message"]}
                for error in exc.errors
            ],
        )

    if exc.is_operational:
        logger.warning(
            "Operational application error",
            extra={**payload, "event": "error.operational"},
        )
    else:
        logger.error(
            "Non-operational application error",
            extra={**payload, "event": "error.non_operational"},
            exc_info=True,
        )

    return _error_response(
        exc.status_code,
        "INTERNAL_ERROR" if is_server_error else exc.code,
        "Internal server error" if is_server_error else exc.message,
        request_id,
        metadata=None if is_server_error else exc.metadata,
    )


# -------------------------------------------------------
# Request validation (Pydantic input schema errors)
# -------------------------------------------------------
async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    payload = _base_log_payload(request)
    request_id = get_request_id(request)

    logger.info(
        "Request schema validation failed",
        extra={
            **payload,
            "event": "error.schema_validation",
            "errors": exc.errors(),
        },
    )

    details = [
        {
            "field": ".".join(str(loc) for loc in err["loc"] if loc != "body"),
            "message": err["msg"],
        }
        for err in exc.errors()
    ]

    return _error_response(
        422,
        "SCHEMA_VALIDATION_ERROR",
        "Request body failed validation",
        request_id,
        details=details,
    )


# -------------------------------------------------------
# Response validation (server bug)
# -------------------------------------------------------
async def response_validation_exception_handler(
    request: Request, exc: ResponseValidationError
):
    payload = _base_log_payload(request)
    request_id = get_request_id(request)

    logger.critical(
        "Response validation failed",
        extra={**payload, "event": "error.response_validation"},
        exc_info=True,
    )

    return _error_response(
        500, "INTERNAL_ERROR", "Internal server error", request_id
    )


# -------------------------------------------------------
# Unhandled exceptions (crash)
# -------------------------------------------------------
async def unhandled_exception_handler(request: Request, exc: Exception):
    payload = _base_log_payload(request)
    request_id = get_request_id(request)

    payload["error_type"] = type(exc).__name__

    logger.critical(
        "Unhandled exception occurred",
        extra={**payload, "event": "error.unhandled"},
        exc_info=True,
    )

    return _error_response(
        500, "INTERNAL_ERROR", "Internal server error", request_id
    )


# -------------------------------------------------------
# FastAPI's own HTTPException
# -------------------------------------------------------
async def http_exception_handler(request: Request, exc: HTTPException):
    payload = _base_log_payload(request)
    request_id = get_request_id(request)

    logger.warning(
        "HTTP exception raised",
        extra={
            **payload,
            "event": "error.http_exception",
            "status_code": exc.status_code,
            "detail": exc.detail,
        },
    )

    return _error_response(
        exc.status_code,
        "HTTP_ERROR",
        str(exc.detail),
        request_id,
    )
