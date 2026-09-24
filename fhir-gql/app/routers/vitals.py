"""
FastAPI router for Vitals resources.

Vitals captures wearable/manual health and activity metrics — steps, calories,
heart rate, blood pressure, sleep stages, weight/height, etc. It is a custom
resource, not part of the FHIR R4 spec, so unlike the FHIR resource routers:
  - There is no `Accept: application/fhir+json` content negotiation — the
    fhir-server always returns plain JSON for vitals.
  - The dedicated VitalsClient talks to its own base URL (/api/v1/vitals) rather
    than the shared FhirClient.

Endpoints:
  POST   /vitals/         — record a new vitals entry
  GET    /vitals/{id}     — fetch a single vitals entry by public vitals_id
  GET    /vitals/         — paginated list with optional filters
  PATCH  /vitals/{id}     — partial update (metric fields only)
  DELETE /vitals/{id}     — permanent delete

RBAC is enforced via require_permission() for the ("vitals", <action>) pair.
"""

from fastapi import APIRouter, Depends, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.schema_utils import inline_schema
from app.di.dependencies.vitals import get_vitals_service
from app.schemas.vitals.input import ListVitalsSchema, VitalsCreateSchema, VitalsPatchSchema
from app.schemas.vitals.response import PaginatedVitalsResponse, VitalsResponse
from app.services.vitals_service import VitalsService

# All vitals routes are prefixed with /vitals; tagged for Swagger grouping.
router = APIRouter(prefix="/vitals", tags=["Vitals"])

# ── Shared error response descriptors ────────────────────────────────────────

_ERR_NOT_FOUND = {404: {"description": "Vitals entry not found"}}
_ERR_VALIDATION = {422: {"description": "Validation error — request body or query params failed schema validation"}}

# ── Shared success response descriptors ──────────────────────────────────────
# Single content type only — vitals has no FHIR R4 representation.

_SINGLE_200 = {
    200: {
        "description": "Vitals entry retrieved or updated successfully",
        "content": {
            "application/json": {"schema": inline_schema(VitalsResponse.model_json_schema())}
        },
    }
}
_SINGLE_201 = {
    201: {
        "description": "Vitals entry created successfully",
        "content": {
            "application/json": {"schema": inline_schema(VitalsResponse.model_json_schema())}
        },
    }
}
_LIST_200 = {
    200: {
        "description": "Paginated list of Vitals entries",
        "content": {
            "application/json": {"schema": inline_schema(PaginatedVitalsResponse.model_json_schema())}
        },
    }
}


# ── POST /vitals/ ──────────────────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_vitals",
    summary="Record a new vitals entry",
    description=(
        "Creates a vitals record capturing health and activity metrics from a wearable device or manual entry. "
        "Supported metric categories: activity (steps, calories, distance, active minutes, exercise), "
        "heart (resting heart rate, heart rate, HRV, stress score), "
        "blood pressure (systolic, diastolic), "
        "sleep (total, REM, deep, light, awake minutes; bed/wake times; stage percentages), "
        "and body metrics (weight, height, age, gender). "
        "Supply `user_id` and `org_id` in the payload to bind the record. "
        "The caller's JWT `sub` claim is recorded as `created_by`. "
        "The linked patient is resolved by the fhir-server from the user's `sub` claim "
        "if `patient_id` is not provided."
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
    dependencies=[Depends(require_permission("vitals", "create"))],
)
async def create_vitals(
    dto: VitalsCreateSchema,
    actor: AuthUser = Depends(require_permission("vitals", "create")),
    service: VitalsService = Depends(get_vitals_service),
) -> JSONResponse:
    """Create a new Vitals entry and return the persisted record."""
    data = await service.create(dto, actor)
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=jsonable_encoder(data))


# ── GET /vitals/{vitals_id} ─────────────────────────────────────────────────────


@router.get(
    "/{vitals_id}",
    operation_id="get_vitals",
    summary="Get a vitals entry by ID",
    description=(
        "Fetches a single vitals record by its public integer `vitals_id`. "
        "Access is subject to organization-scoped authorization on the fhir-server."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
    dependencies=[Depends(require_permission("vitals", "read"))],
)
async def get_vitals(
    vitals_id: int,
    actor: AuthUser = Depends(require_permission("vitals", "read")),
    service: VitalsService = Depends(get_vitals_service),
) -> JSONResponse:
    """Fetch a single Vitals entry by its public vitals_id."""
    data = await service.get_by_id(vitals_id, actor)
    return JSONResponse(content=jsonable_encoder(data))


# ── GET /vitals/ ─────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_vitals",
    summary="List vitals entries with optional filters",
    description=(
        "Returns a paginated list of vitals entries accessible to the caller. "
        "Filter by `user_id`, `patient_id`, `org_id`, exact `date` (YYYY-MM-DD), "
        "or a `recorded_at` datetime range (`recorded_at_from` / `recorded_at_to`). "
        "Results are ordered by `recorded_at` descending (newest first)."
    ),
    responses={**_LIST_200},
    dependencies=[Depends(require_permission("vitals", "read"))],
)
async def list_vitals(
    filters: ListVitalsSchema = Depends(),
    actor: AuthUser = Depends(require_permission("vitals", "read")),
    service: VitalsService = Depends(get_vitals_service),
) -> JSONResponse:
    """Return a paginated list of Vitals entries, optionally filtered."""
    data = await service.list(filters, actor)
    return JSONResponse(content=jsonable_encoder(data))


# ── PATCH /vitals/{vitals_id} ────────────────────────────────────────────────────


@router.patch(
    "/{vitals_id}",
    operation_id="patch_vitals",
    summary="Partially update a vitals entry",
    description=(
        "Only supplied metric fields are written; omitted fields are left unchanged. "
        "All metric fields in VitalsCreateSchema are patchable. "
        "`user_id`, `patient_id`, `org_id`, and `recorded_at` cannot be changed after creation. "
        "The caller's JWT `sub` claim is recorded as `updated_by`."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
    dependencies=[Depends(require_permission("vitals", "update"))],
)
async def patch_vitals(
    vitals_id: int,
    dto: VitalsPatchSchema,
    actor: AuthUser = Depends(require_permission("vitals", "update")),
    service: VitalsService = Depends(get_vitals_service),
) -> JSONResponse:
    """Partially update a Vitals entry. Returns 422 if the body is empty."""
    data = await service.update(vitals_id, dto, actor)
    return JSONResponse(content=jsonable_encoder(data))


# ── DELETE /vitals/{vitals_id} ───────────────────────────────────────────────────


@router.delete(
    "/{vitals_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_vitals",
    summary="Delete a vitals entry",
    description=(
        "Permanently deletes the vitals record. "
        "This operation is irreversible. Returns 204 No Content on success."
    ),
    responses={**_ERR_NOT_FOUND},
    dependencies=[Depends(require_permission("vitals", "delete"))],
)
async def delete_vitals(
    vitals_id: int,
    actor: AuthUser = Depends(require_permission("vitals", "delete")),
    service: VitalsService = Depends(get_vitals_service),
) -> None:
    """Permanently delete a Vitals entry."""
    await service.delete(vitals_id, actor)
