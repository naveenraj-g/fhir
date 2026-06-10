"""
FastAPI router for Practitioner resources.

Exposes the standard CRUD surface for Practitioner:
  POST   /practitioners/                — create a new Practitioner
  GET    /practitioners/{resource_id}   — fetch a single Practitioner by integer ID
  GET    /practitioners/                — paginated list with optional filters
  PATCH  /practitioners/{resource_id}   — partial update (scalar fields only)
  DELETE /practitioners/{resource_id}   — permanent delete (cascades to child records)

Child sub-resources (name, identifier, telecom, address, photo, qualification,
communication) are managed via separate fhir-server sub-routes. This middleware
only exposes the top-level Practitioner CRUD.

All routes support content negotiation:
  - `Accept: application/json`      → plain snake_case JSON (default)
  - `Accept: application/fhir+json` → FHIR R4 resource / Bundle

RBAC is enforced via require_permission() for the ("practitioner", <action>) pair.
"""

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response, get_accept_header
from app.core.schema_utils import inline_schema
from app.di.dependencies.practitioner import get_practitioner_service
from app.schemas.practitioner.fhir_schemas import FhirBundleResponse, FhirPractitionerResponse
from app.schemas.practitioner.input import ListPractitionersSchema, PractitionerCreateSchema, PractitionerPatchSchema
from app.schemas.practitioner.response import PaginatedPractitionerResponse, PractitionerResponse
from app.services.practitioner_service import PractitionerService

# All practitioner routes are prefixed with /practitioners; tagged for Swagger grouping.
router = APIRouter(prefix="/practitioners", tags=["Practitioners"])

# ── Shared error response descriptors ────────────────────────────────────────

_ERR_NOT_FOUND = {404: {"description": "Practitioner not found"}}
_ERR_VALIDATION = {422: {"description": "Validation error — request body or query params failed schema validation"}}

# ── Shared success response descriptors ──────────────────────────────────────
# inline_schema() resolves Pydantic v2 $defs/$ref pointers so nested sub-model
# references (e.g. PlainQualification → PlainQualificationIdentifier) render
# correctly in the Swagger UI schema resolver.

_SINGLE_201 = {
    201: {
        "description": "Practitioner created successfully",
        "content": {
            "application/json": {
                "schema": inline_schema(PractitionerResponse.model_json_schema())
            },
            "application/fhir+json": {
                "schema": inline_schema(FhirPractitionerResponse.model_json_schema())
            },
        },
    }
}

_SINGLE_200 = {
    200: {
        "description": "Practitioner retrieved or updated successfully",
        "content": {
            "application/json": {
                "schema": inline_schema(PractitionerResponse.model_json_schema())
            },
            "application/fhir+json": {
                "schema": inline_schema(FhirPractitionerResponse.model_json_schema())
            },
        },
    }
}

_LIST_200 = {
    200: {
        "description": "Paginated list of Practitioner resources",
        "content": {
            "application/json": {
                "schema": inline_schema(PaginatedPractitionerResponse.model_json_schema())
            },
            "application/fhir+json": {
                "schema": inline_schema(FhirBundleResponse.model_json_schema())
            },
        },
    }
}


# ── POST /practitioners/ ─────────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_practitioner",
    summary="Create a Practitioner",
    description=(
        "Creates a new Practitioner record with top-level scalar fields. "
        "Child sub-resources (name, identifier, telecom, address, photo, "
        "qualification, communication) are added via separate fhir-server sub-routes. "
        "Stamps `created_by` from the caller's JWT — do not supply this field. "
        "Send `Accept: application/fhir+json` to receive the result in FHIR R4 format."
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
    dependencies=[Depends(require_permission("practitioner", "create"))],
)
async def create_practitioner(
    dto: PractitionerCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("practitioner", "create")),
    service: PractitionerService = Depends(get_practitioner_service),
) -> JSONResponse:
    """Create a new Practitioner resource and return the persisted record."""
    data = await service.create(dto, actor, accept=get_accept_header(request))
    return format_response(data, request)


# ── GET /practitioners/{resource_id} ─────────────────────────────────────────


@router.get(
    "/{resource_id}",
    operation_id="get_practitioner",
    summary="Get a Practitioner by ID",
    description=(
        "Fetch a single Practitioner by its integer ID. "
        "The response includes all child sub-resources (name, identifier, telecom, etc.). "
        "Send `Accept: application/fhir+json` for FHIR R4 format."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
    dependencies=[Depends(require_permission("practitioner", "read"))],
)
async def get_practitioner(
    resource_id: int,
    request: Request,
    actor: AuthUser = Depends(require_permission("practitioner", "read")),
    service: PractitionerService = Depends(get_practitioner_service),
) -> JSONResponse:
    """Fetch a single Practitioner resource by its primary key."""
    data = await service.get_by_id(resource_id, actor, accept=get_accept_header(request))
    return format_response(data, request)


# ── GET /practitioners/ ───────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_practitioners",
    summary="List Practitioners",
    description=(
        "Returns a paginated list of Practitioner resources. "
        "Filter by `family_name` or `given_name` (partial, case-insensitive name search), "
        "`active`, `user_id`, or `org_id`. "
        "Send `Accept: application/fhir+json` to receive a FHIR Bundle searchset."
    ),
    responses={**_LIST_200},
    dependencies=[Depends(require_permission("practitioner", "read"))],
)
async def list_practitioners(
    request: Request,
    filters: ListPractitionersSchema = Depends(),
    actor: AuthUser = Depends(require_permission("practitioner", "read")),
    service: PractitionerService = Depends(get_practitioner_service),
) -> JSONResponse:
    """Return a paginated list of Practitioners, optionally filtered by name or status."""
    data = await service.list(filters, actor, accept=get_accept_header(request))
    return format_paginated_response(data, request)


# ── PATCH /practitioners/{resource_id} ───────────────────────────────────────


@router.patch(
    "/{resource_id}",
    operation_id="update_practitioner",
    summary="Partially update a Practitioner",
    description=(
        "Update specific scalar fields on a Practitioner. At least one field must be provided. "
        "Patchable fields: `active`, `gender`, `birth_date`, `deceased_boolean`, `deceased_datetime`. "
        "Child arrays (name, identifier, telecom, address, photo, qualification, communication) "
        "are managed via separate fhir-server sub-routes and cannot be patched here. "
        "Stamps `updated_by` from the caller's JWT automatically. "
        "Send `Accept: application/fhir+json` for FHIR R4 format."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
    dependencies=[Depends(require_permission("practitioner", "update"))],
)
async def update_practitioner(
    resource_id: int,
    dto: PractitionerPatchSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("practitioner", "update")),
    service: PractitionerService = Depends(get_practitioner_service),
) -> JSONResponse:
    """Partially update a Practitioner resource. Returns 422 if the body is empty."""
    data = await service.update(resource_id, dto, actor, accept=get_accept_header(request))
    return format_response(data, request)


# ── DELETE /practitioners/{resource_id} ──────────────────────────────────────


@router.delete(
    "/{resource_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_practitioner",
    summary="Delete a Practitioner",
    description=(
        "Permanently deletes the Practitioner and all its child records "
        "(name, identifier, telecom, address, photo, qualification, communication). "
        "This operation is irreversible. Returns 204 No Content on success."
    ),
    responses={**_ERR_NOT_FOUND},
    dependencies=[Depends(require_permission("practitioner", "delete"))],
)
async def delete_practitioner(
    resource_id: int,
    actor: AuthUser = Depends(require_permission("practitioner", "delete")),
    service: PractitionerService = Depends(get_practitioner_service),
) -> None:
    """Permanently delete a Practitioner and cascade to all child records."""
    await service.delete(resource_id, actor)
