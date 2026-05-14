from contextlib import asynccontextmanager
from typing import Any, cast
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import Response

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.routers.vitals import router as vitals_router
from app.core.database import Database
from app.core.logging import get_logger, setup_logging
from app.core.redis import redis_client
from app.core.request_context import request_context_middleware
from app.di.container import Container
from app.errors.base import ApplicationError
from app.errors.handlers import (
    application_error_handler,
    http_exception_handler,
    request_validation_exception_handler,
    response_validation_exception_handler,
    unhandled_exception_handler,
)
from app.middleware import (
    RateLimitMiddleware,
)
from app.routers import api_router
from app.schemas.base import HealthResponseSchema

setup_logging()
logger = get_logger(__name__)

container = Container()
db: Database = container.core.database()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🟢 Starting up the application")

    # Startup event to create tables if they don't exist (for demo purposes)
    # In production, use Alembic migrations.
    if settings.ENVIRONMENT == "development":
        logger.info("Creating database tables (development mode)...")
        await db.connect()
        # async with db.engine.connect() as conn:
        #     await conn.execute(
        #         text("""
        #         ALTER TABLE appointment
        #         ADD COLUMN IF NOT EXISTS recurrence_id INTEGER,
        #         ADD COLUMN IF NOT EXISTS occurrence_changed BOOLEAN;
        #     """)
        #     )
        #     await conn.commit()
        logger.info("Database tables ensured.")

    try:
        await cast(Any, redis_client.ping())
        app.state.redis = redis_client
        logger.info("Connected to Redis successfully.")
    except Exception as e:
        logger.error("Failed to connect to Redis.", exc_info=e)
        app.state.redis = None
    yield

    logger.info("🔴 Shutting down application...")
    await db.disconnect()

    logger.info("Database engine disposed.")


app: FastAPI = FastAPI(
    title="FHIR Server",
    version="1.0.0",
    description="""
A FHIR R4-compliant REST API server for managing healthcare resources.

This server provides CRUD operations for core FHIR resources including Patient,
Practitioner, and Encounter. All resources are validated against the HL7 FHIR R4
specification using the `fhir.resources` library.

Designed for integration with AI agents via FastMCP dynamic tool generation.
""",
    openapi_tags=[
        {
            "name": "Patients",
            "description": "Operations for managing FHIR Patient resources — individuals receiving care. Supports create, read, update, list, and delete.",
        },
        {
            "name": "Practitioners",
            "description": "Operations for managing FHIR Practitioner resources — healthcare providers such as physicians, nurses, and therapists. Supports create, read, update, list, and delete.",
        },
        {
            "name": "Encounters",
            "description": "Operations for managing FHIR Encounter resources — clinical interactions between patients and providers (visits, admissions, telehealth). Supports create, read, update, list, and delete.",
        },
        {
            "name": "Appointments",
            "description": "Operations for managing FHIR Appointment resources — scheduled healthcare events for patients and practitioners at a specific date and time. Supports create, read, update, list, and delete.",
        },
        {
            "name": "Vitals",
            "description": "Operations for storing and retrieving user vitals data — activity, heart rate, sleep, and demographic metrics from wearable devices. Not a FHIR resource.",
        },
        {
            "name": "QuestionnaireResponses",
            "description": "Operations for managing FHIR QuestionnaireResponse resources — structured sets of answers to a Questionnaire, supporting nested items and all FHIR R4 answer value types. Supports create, read, update, list, and delete.",
        },
        {
            "name": "Health",
            "description": "Server liveness probe. No authentication required.",
        },
    ],
    lifespan=lifespan,
)

app.add_exception_handler(ApplicationError, application_error_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)
app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
app.add_exception_handler(
    ResponseValidationError, response_validation_exception_handler
)
app.add_exception_handler(HTTPException, http_exception_handler)

app.container = container

app.add_middleware(RateLimitMiddleware)
app.middleware("http")(request_context_middleware)

app.include_router(
    api_router, prefix="/api/fhir/v1", dependencies=[Depends(get_current_user)]
)

app.include_router(
    vitals_router,
    prefix="/api/v1/vitals",
    tags=["Vitals"],
    dependencies=[Depends(get_current_user)],
)


@app.get(
    "/health",
    response_model=HealthResponseSchema,
    operation_id="health_check",
    summary="Health check",
    description=(
        "Returns the liveness status of the server. "
        "Use this endpoint to verify the API is reachable and running. "
        "No authentication required. Returns `req_id` for request tracing."
    ),
    response_description="Server is healthy",
    tags=["Health"],
    responses={503: {"description": "Service unavailable — server is starting up or shutting down"}},
)
async def health_check(request: Request):
    return {"status": "ok", "req_id": request.state.request_id}


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


"""
Common Mertics:
 - CPU Usage
 - Memory Usage
 - Response Time
 - Server Load
 - Network Traffic
 - Database Queries

Observability:
 - Logs
 - Metrics
 _ Traces
"""
# python.analysis.typeCheckingMode
