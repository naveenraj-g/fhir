"""
FastAPI router for Flag resources.

Endpoints:
  POST   /flags/        — raise a Flag (with identifier / category lists)
  GET    /flags/{id}    — fetch a single Flag by public ID
  GET    /flags/        — paginated FHIR R4 search (patient, subject, author, date, ...)
  PATCH  /flags/{id}    — partial update; identifier / category lists are replaced when sent
  DELETE /flags/{id}    — permanent delete (cascades to the child lists)

All routes support content negotiation:
  - `Accept: application/json`      → plain snake_case JSON (default)
  - `Accept: application/fhir+json` → FHIR R4 resource / Bundle

RBAC is enforced via require_permission() for the ("flag", <action>) pair.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response, get_accept_header
from app.core.schema_utils import inline_schema
from app.di.dependencies.flag import get_flag_service
from app.schemas.flag.input import FlagCreateSchema, FlagPatchSchema, ListFlagsSchema
from app.schemas.flag.response import FhirBundleResponse, FhirFlagResponse, FlagRecord, PaginatedFlagResponse
from app.services.flag_service import FlagService

# All routes are prefixed with /flags; tagged for Swagger grouping.
router = APIRouter(prefix="/flags", tags=["Flags"])

# ── Shared error response descriptors ────────────────────────────────────────

_ERR_NOT_FOUND = {404: {"description": "Flag not found"}}
_ERR_VALIDATION = {422: {"description": "Validation error — request body or query params failed validation"}}

# ── Shared success response descriptors ──────────────────────────────────────
# inline_schema() resolves Pydantic's $defs/$ref pointers so both content types
# render in Swagger UI without resolver errors.

_SINGLE_201 = {
    201: {
        "description": "Flag created successfully",
        "content": {
            "application/json": {"schema": inline_schema(FlagRecord.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FhirFlagResponse.model_json_schema())},
        },
    }
}

_SINGLE_200 = {
    200: {
        "description": "Flag retrieved or updated successfully",
        "content": {
            "application/json": {"schema": inline_schema(FlagRecord.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FhirFlagResponse.model_json_schema())},
        },
    }
}

_LIST_200 = {
    200: {
        "description": "Paginated list of Flag resources",
        "content": {
            "application/json": {"schema": inline_schema(PaginatedFlagResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FhirBundleResponse.model_json_schema())},
        },
    }
}


# ── POST /flags/ ─────────────────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_flag",
    summary="Create a Flag",
    description=(
        "Raises a prospective warning about a potential issue when providing care (e.g. an allergy alert or a "
        "safety flag). `status`, `code` (`code_code` and/or `code_text`) and `subject` are required. `subject` is a "
        "FHIR reference: Patient|Location|Group|Organization|Practitioner|PlanDefinition|Medication|Procedure, e.g. "
        "`'Patient/10001'`. Optionally set the active `period_start` / `period_end` (an empty end means still "
        "active), an `encounter_id`, an `author` (Device|Organization|Patient|Practitioner|PractitionerRole) and the "
        "`identifier` / `category` lists. References are `Type/id` strings — only their format is validated. "
        "Send `Accept: application/fhir+json` to receive the result in FHIR R4 format."
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
    dependencies=[Depends(require_permission("flag", "create"))],
)
async def create_flag(
    dto: FlagCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("flag", "create")),
    service: FlagService = Depends(get_flag_service),
) -> JSONResponse:
    """Raise a new Flag and return the persisted record."""
    data = await service.create(dto, actor, accept=get_accept_header(request))
    return format_response(data, request)


# ── GET /flags/{resource_id} ─────────────────────────────────────────────────


@router.get(
    "/{resource_id}",
    operation_id="get_flag",
    summary="Get a Flag by ID",
    description=(
        "Fetch a single Flag by its public integer ID. Send `Accept: application/fhir+json` for FHIR R4 format."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
    dependencies=[Depends(require_permission("flag", "read"))],
)
async def get_flag(
    resource_id: int,
    request: Request,
    actor: AuthUser = Depends(require_permission("flag", "read")),
    service: FlagService = Depends(get_flag_service),
) -> JSONResponse:
    """Fetch a single Flag by its public ID."""
    data = await service.get_by_id(resource_id, actor, accept=get_accept_header(request))
    return format_response(data, request)


# ── GET /flags/ ──────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_flags",
    summary="Search Flags",
    description=(
        "Searches Flags using the FHIR R4 Flag search parameters (https://www.hl7.org/fhir/R4/flag.html#search): "
        "`author`, `date`, `encounter`, `identifier`, `patient`, `subject` — plus `_id`, `_lastUpdated` and the "
        "convenience filters `status`, `category` and `code`. "
        "Token params (`identifier`, `status`, `category`, `code`) accept `code`, `system|code`, `|code` or "
        "`system|`; comma = OR. Reference params (`patient`, `subject`, `encounter`, `author`) accept `Type/id` or a "
        "bare numeric id. `date` matches the flag's active period and, like `_lastUpdated`, takes an optional prefix "
        "eq|ne|gt|lt|ge|le|sa|eb|ap (repeat for AND, e.g. flags active during a window). "
        "`org_id` is mandatory on every search (tenant scope) and `user_id` is optional; paginate with `limit` / `offset`. "
        "Send `Accept: application/fhir+json` to receive a FHIR Bundle searchset."
    ),
    responses={**_LIST_200, **_ERR_VALIDATION},
    dependencies=[Depends(require_permission("flag", "read"))],
)
async def list_flags(
    request: Request,
    id_: Optional[str] = Query(None, alias="_id", description="Public flag_id(s), comma-separated."),
    identifier: Optional[str] = Query(None, description="Token `[system|]value` of Flag.identifier."),
    flag_status: Optional[str] = Query(None, alias="status", description="Token: active|inactive|entered-in-error (comma = OR)."),
    category: Optional[str] = Query(None, description="Token `[system|]code` of Flag.category."),
    code: Optional[str] = Query(None, description="Token `[system|]code` of Flag.code."),
    subject: Optional[str] = Query(None, description="Subject reference (Patient, Location, Group, ...), e.g. `Patient/10001`."),
    patient: Optional[str] = Query(None, description="Subject patient reference: `Patient/10001` or `10001`."),
    encounter: Optional[str] = Query(None, description="Encounter reference: `Encounter/20001` or `20001`."),
    author: Optional[str] = Query(None, description="Author reference: Device|Organization|Patient|Practitioner|PractitionerRole."),
    date: Optional[List[str]] = Query(None, description="Flag active period with optional prefix, e.g. `ge2024-01-01`. Repeat for AND."),
    last_updated: Optional[List[str]] = Query(None, alias="_lastUpdated", description="Last-updated instant with optional prefix."),
    user_id: Optional[str] = Query(None, description="Optional: restrict to records owned by this user (JWT subject)."),
    org_id: str = Query(..., min_length=1, description="Tenant organization ID — mandatory scope of every search."),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    actor: AuthUser = Depends(require_permission("flag", "read")),
    service: FlagService = Depends(get_flag_service),
) -> JSONResponse:
    """
    Search Flags with FHIR R4 search parameters.

    Parameters are declared explicitly (with aliases) because `_id` and `_lastUpdated`
    are not valid Python identifiers. They are gathered into ListFlagsSchema, whose
    validators (e.g. the status code check) run here; a failure is surfaced as a 422.
    """
    try:
        filters = ListFlagsSchema(
            id=id_, identifier=identifier, status=flag_status, category=category, code=code,
            subject=subject, patient=patient, encounter=encounter, author=author, date=date,
            last_updated=last_updated, user_id=user_id, org_id=org_id, limit=limit, offset=offset,
        )
    except ValidationError as exc:
        # include_context=False keeps the detail JSON-serialisable (ctx can hold exceptions).
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.errors(include_url=False, include_context=False),
        ) from exc
    data = await service.list(filters, actor, accept=get_accept_header(request))
    return format_paginated_response(data, request)


# ── PATCH /flags/{resource_id} ───────────────────────────────────────────────


@router.patch(
    "/{resource_id}",
    operation_id="update_flag",
    summary="Partially update a Flag",
    description=(
        "Update fields on a Flag. At least one field must be provided. Patchable fields: `status`, `code_*`, "
        "`subject`, `period_start` / `period_end`, `encounter_id`, `author` (references as `Type/id`) and their "
        "`*_display`. To retire a flag set `status: inactive` and/or `period_end`. "
        "The child lists `identifier` and `category` are also patchable with REPLACE semantics: a list that is "
        "sent replaces the stored list in full, `[]` clears it, and an omitted list is left untouched. "
        "Send `Accept: application/fhir+json` for FHIR R4 format."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
    dependencies=[Depends(require_permission("flag", "update"))],
)
async def update_flag(
    resource_id: int,
    dto: FlagPatchSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("flag", "update")),
    service: FlagService = Depends(get_flag_service),
) -> JSONResponse:
    """Partially update a Flag. Returns 422 if the body is empty."""
    data = await service.update(resource_id, dto, actor, accept=get_accept_header(request))
    return format_response(data, request)


# ── DELETE /flags/{resource_id} ──────────────────────────────────────────────


@router.delete(
    "/{resource_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_flag",
    summary="Delete a Flag",
    description=(
        "Permanently deletes the Flag and its child records (identifier, category). "
        "This operation is irreversible. Returns 204 No Content on success."
    ),
    responses={**_ERR_NOT_FOUND},
    dependencies=[Depends(require_permission("flag", "delete"))],
)
async def delete_flag(
    resource_id: int,
    actor: AuthUser = Depends(require_permission("flag", "delete")),
    service: FlagService = Depends(get_flag_service),
) -> None:
    """Permanently delete a Flag and cascade to its child records."""
    await service.delete(resource_id, actor)
