"""One log line per HTTP request — the record that a request happened at all.

Deliberately metadata-only: no request/response bodies. Reading the body here
would consume Starlette's single-shot request stream and risks breaking every
downstream route. Payload logging happens at the router layer instead (see
app.core.logging.log_payload), where the *validated* Pydantic model is already
in hand, is trivially redactable, and costs nothing extra to serialize.

request_id comes from the formatter (ContextVar), which is set by
request_context_middleware above this one in the stack.
"""

import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger

logger = get_logger(__name__)

# Probes and docs — high frequency, zero diagnostic value.
_EXCLUDED_PATHS = {"/health", "/health/ready", "/openapi.json", "/favicon.ico"}
_EXCLUDED_PREFIXES = ("/docs", "/redoc")


class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if path in _EXCLUDED_PATHS or path.startswith(_EXCLUDED_PREFIXES):
            return await call_next(request)

        started = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            # The exception handlers log the failure in detail; this line
            # exists so the request still gets an access record with timing
            # rather than vanishing from the request stream entirely.
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            logger.error(
                f"{request.method} {path} -> 500",
                extra={
                    "event": "http.request",
                    "method": request.method,
                    "path": path,
                    "status": 500,
                    "duration_ms": duration_ms,
                },
            )
            raise

        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        status = response.status_code

        # 5xx is our fault, 4xx is the caller's, everything else is routine.
        if status >= 500:
            level = "error"
        elif status >= 400:
            level = "warning"
        else:
            level = "info"

        route = request.scope.get("route")

        getattr(logger, level)(
            f"{request.method} {path} -> {status}",
            extra={
                "event": "http.request",
                "method": request.method,
                "path": path,
                "status": status,
                "duration_ms": duration_ms,
                "client_ip": request.client.host if request.client else None,
                "operation_id": getattr(route, "operation_id", None)
                or getattr(route, "name", None),
            },
        )

        return response
