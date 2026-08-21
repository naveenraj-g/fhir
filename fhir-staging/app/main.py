from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError, ResponseValidationError

from app.core.config import settings
from app.core.database import Database
from app.core.logging import get_logger, setup_logging
from app.di.container import Container
from app.errors.base import ApplicationError
from app.errors.handlers import (
    application_error_handler,
    http_exception_handler,
    request_validation_exception_handler,
    response_validation_exception_handler,
    unhandled_exception_handler,
)
from app.middleware import AccessLogMiddleware, request_context_middleware
from app.routers import discover_routers

setup_logging()
logger = get_logger(__name__)

container = Container()
db: Database = container.core.database()

OPENAPI_TAGS = [
    {
        "name": "Staging Medical Records",
        "description": (
            "A staging area for medical-record documents and the FHIR R4 "
            "Observations an AI agent extracts from them. Documents arrive with "
            "a filenest file handle and clinical context; the agent fetches the "
            "file, reads it, and writes the observations back here for review "
            "before anything is promoted into the FHIR server."
        ),
    }
]


async def log_route_entry(request: Request) -> None:
    """DEBUG-level route-handler entry line — the top of the per-request flow
    trace, above the service/repository lines that trace_methods emits.
    Applied once as a router-level dependency, so it covers every route with
    no per-handler code. Silent at INFO."""
    if not logger.isEnabledFor(10):  # logging.DEBUG
        return
    route = request.scope.get("route")
    logger.debug(
        "Route entered",
        extra={
            "event": "route.entered",
            "operation_id": getattr(route, "operation_id", None)
            or getattr(route, "name", None),
            "path_params": dict(request.path_params),
            "query_params": dict(request.query_params),
        },
    )


def mount_routers(app: FastAPI) -> None:
    """Mount every router named in configs/config.yaml's routes.enabled.

    Called from lifespan() at real ASGI startup rather than at module-import
    time. Kept as a standalone sync function (not inlined into lifespan) so
    tests/conftest.py can call it directly once — httpx's ASGITransport does
    not run the ASGI lifespan protocol on its own.
    """
    enabled = set(settings.routes.enabled)
    api_router = APIRouter()
    discovered = discover_routers()

    unknown = enabled - set(discovered)
    if unknown:
        # Fail loudly: a typo here silently serves 404s for a resource the
        # operator believes is live.
        raise RuntimeError(
            f"routes.enabled names unknown routers: {sorted(unknown)}. "
            f"Available: {sorted(discovered)}."
        )

    for name, router in discovered.items():
        if name in enabled:
            api_router.include_router(router)

    logger.info(
        "Mounted routers",
        extra={
            "event": "startup.routes_mounted",
            "count": len(enabled),
            "routes": sorted(enabled),
        },
    )
    app.include_router(
        api_router,
        prefix="/api/v1",
        dependencies=[Depends(log_route_entry)],
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # One config summary at startup — answers most "why is this environment
    # behaving differently" questions straight from the log stream.
    logger.info(
        "🟢 Starting up fhir-staging",
        extra={
            "event": "startup.begin",
            "environment": settings.ENVIRONMENT,
            "log_level": settings.logging.level,
            "log_format": settings.logging.format,
            "debug_payloads": settings.logging.debug_payloads,
            "slow_query_ms": settings.logging.slow_query_ms,
        },
    )

    if settings.logging.debug_payloads:
        logger.warning(
            "debug_payloads is ENABLED — full request payloads are being "
            "written to the log stream. The documents staged here are medical "
            "records. Local development only.",
            extra={"event": "startup.phi_logging_enabled"},
        )

    mount_routers(app)

    yield

    logger.info("🔴 Shutting down fhir-staging", extra={"event": "shutdown.begin"})
    await db.disconnect()


app = FastAPI(
    title="fhir-staging",
    version="0.1.0",
    description=(
        "Staging area for AI-extracted FHIR R4 Observations.\n\n"
        "Every response is plain snake_case JSON. There is deliberately no "
        "`application/fhir+json` representation: the FHIR R4 standard governs "
        "the *table shape* here (the staging_observation model is a flattened R4 "
        "Observation, column-for-column identical to the FHIR server's, so a "
        "staged row promotes without translation) — not the wire format, which "
        "is internal."
    ),
    openapi_tags=OPENAPI_TAGS,
    lifespan=lifespan,
)

app.middleware("http")(request_context_middleware)
app.add_middleware(AccessLogMiddleware)

app.add_exception_handler(ApplicationError, application_error_handler)
app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
app.add_exception_handler(
    ResponseValidationError, response_validation_exception_handler
)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)


@app.get("/health", tags=["Health"], operation_id="health")
async def health():
    return {"status": "ok"}
