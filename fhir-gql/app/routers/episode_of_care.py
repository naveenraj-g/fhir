"""
FastAPI router for EpisodeOfCare resources.

Endpoints:
  POST   /episode-of-cares/        — create an EpisodeOfCare (with its child lists in the body)
  GET    /episode-of-cares/{id}    — fetch a single EpisodeOfCare by public ID
  GET    /episode-of-cares/        — paginated FHIR R4 search (patient, status, type, date, ...); org_id mandatory
  PATCH  /episode-of-cares/{id}    — partial update; child lists are replaced when sent
  DELETE /episode-of-cares/{id}    — permanent delete (cascades to all child records)

All routes support content negotiation:
  - `Accept: application/json`      → plain snake_case JSON (default)
  - `Accept: application/fhir+json` → FHIR R4 resource / Bundle

RBAC is enforced via require_permission() for the ("episode_of_care", <action>) pair.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response, get_accept_header
from app.core.schema_utils import inline_schema
from app.di.dependencies.episode_of_care import get_episode_of_care_service
from app.schemas.episode_of_care.input import (
    EpisodeOfCareCreateSchema,
    EpisodeOfCarePatchSchema,
    ListEpisodeOfCaresSchema,
)
from app.schemas.episode_of_care.response import (
    EpisodeOfCareRecord,
    FhirBundleResponse,
    FhirEpisodeOfCareResponse,
    PaginatedEpisodeOfCareResponse,
)
from app.services.episode_of_care_service import EpisodeOfCareService

# All routes are prefixed with /episode-of-cares; tagged for Swagger grouping.
router = APIRouter(prefix="/episode-of-cares", tags=["EpisodeOfCares"])

# ── Shared error response descriptors ────────────────────────────────────────

_ERR_NOT_FOUND = {404: {"description": "EpisodeOfCare not found"}}
_ERR_VALIDATION = {422: {"description": "Validation error — request body or query params failed validation"}}

# ── Shared success response descriptors ──────────────────────────────────────
# inline_schema() resolves Pydantic's $defs/$ref pointers so both content types
# render in Swagger UI without resolver errors.

_SINGLE_201 = {
    201: {
        "description": "EpisodeOfCare created successfully",
        "content": {
            "application/json": {"schema": inline_schema(EpisodeOfCareRecord.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FhirEpisodeOfCareResponse.model_json_schema())},
        },
    }
}

_SINGLE_200 = {
    200: {
        "description": "EpisodeOfCare retrieved or updated successfully",
        "content": {
            "application/json": {"schema": inline_schema(EpisodeOfCareRecord.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FhirEpisodeOfCareResponse.model_json_schema())},
        },
    }
}

_LIST_200 = {
    200: {
        "description": "Paginated list of EpisodeOfCare resources",
        "content": {
            "application/json": {"schema": inline_schema(PaginatedEpisodeOfCareResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FhirBundleResponse.model_json_schema())},
        },
    }
}


# ── POST /episode-of-cares/ ──────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_episode_of_care",
    summary="Create an EpisodeOfCare",
    description=(
        "Creates an episode of care — the association between a patient and an organization/care team for a "
        "particular health condition or programme. `status` and `patient` are required. Optionally set the "
        "`period`, a `managing_organization` (`'Organization/190001'`), a `care_manager` (Practitioner or "
        "PractitionerRole) and the child lists: identifiers, status_history (each with a status and a period), "
        "types, diagnoses (each with a required `condition` reference), referral_requests, team and accounts. "
        "References are `Type/id` strings — only their format is validated. "
        "Send `Accept: application/fhir+json` to receive the result in FHIR R4 format."
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
    dependencies=[Depends(require_permission("episode_of_care", "create"))],
)
async def create_episode_of_care(
    dto: EpisodeOfCareCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("episode_of_care", "create")),
    service: EpisodeOfCareService = Depends(get_episode_of_care_service),
) -> JSONResponse:
    """Create a new EpisodeOfCare and return the persisted record."""
    data = await service.create(dto, actor, accept=get_accept_header(request))
    return format_response(data, request)


# ── GET /episode-of-cares/{resource_id} ──────────────────────────────────────


@router.get(
    "/{resource_id}",
    operation_id="get_episode_of_care",
    summary="Get an EpisodeOfCare by ID",
    description=(
        "Fetch a single EpisodeOfCare by its public integer ID. Send `Accept: application/fhir+json` for FHIR R4 format."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
    dependencies=[Depends(require_permission("episode_of_care", "read"))],
)
async def get_episode_of_care(
    resource_id: int,
    request: Request,
    actor: AuthUser = Depends(require_permission("episode_of_care", "read")),
    service: EpisodeOfCareService = Depends(get_episode_of_care_service),
) -> JSONResponse:
    """Fetch a single EpisodeOfCare by its public ID."""
    data = await service.get_by_id(resource_id, actor, accept=get_accept_header(request))
    return format_response(data, request)


# ── GET /episode-of-cares/ ───────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_episode_of_cares",
    summary="Search EpisodeOfCares",
    description=(
        "Searches EpisodeOfCares using the FHIR R4 EpisodeOfCare search parameters "
        "(https://www.hl7.org/fhir/R4/episodeofcare.html#search): `care-manager`, `condition`, `date`, `identifier`, "
        "`incoming-referral`, `organization`, `patient`, `status`, `type` — plus `_id` and `_lastUpdated`. "
        "Token params (`identifier`, `status`, `type`) accept `code`, `system|code`, `|code` or `system|`; comma = OR. "
        "Reference params (`patient`, `organization`, `care-manager`, `condition`, `incoming-referral`) accept "
        "`Type/id` or a bare numeric id. `date` matches the episode period (an open end means ongoing) and, like "
        "`_lastUpdated`, takes an optional prefix eq|ne|gt|lt|ge|le|sa|eb|ap; repeat for AND. "
        "`org_id` is mandatory on every search (tenant scope) and `user_id` is optional; paginate with `limit` / "
        "`offset`. Send `Accept: application/fhir+json` to receive a FHIR Bundle searchset."
    ),
    responses={**_LIST_200, **_ERR_VALIDATION},
    dependencies=[Depends(require_permission("episode_of_care", "read"))],
)
async def list_episode_of_cares(
    request: Request,
    id_: Optional[str] = Query(None, alias="_id", description="Public episode_of_care_id(s), comma-separated."),
    identifier: Optional[str] = Query(None, description="Token `[system|]value` of EpisodeOfCare.identifier."),
    episode_status: Optional[str] = Query(
        None, alias="status",
        description="Token: planned|waitlist|active|onhold|finished|cancelled|entered-in-error (comma = OR).",
    ),
    type_: Optional[str] = Query(None, alias="type", description="Token `[system|]code` of EpisodeOfCare.type."),
    patient: Optional[str] = Query(None, description="Patient reference: `Patient/10001` or `10001`."),
    organization: Optional[str] = Query(None, description="managingOrganization reference: `Organization/190001` or `190001`."),
    care_manager: Optional[str] = Query(None, alias="care-manager", description="careManager reference: Practitioner|PractitionerRole."),
    condition: Optional[str] = Query(None, description="diagnosis.condition reference: `Condition/120001` or `120001`."),
    incoming_referral: Optional[str] = Query(None, alias="incoming-referral", description="referralRequest reference: `ServiceRequest/80001`."),
    date: Optional[List[str]] = Query(None, description="Episode period with optional prefix, e.g. `ge2024-01-01`. Repeat for AND."),
    last_updated: Optional[List[str]] = Query(None, alias="_lastUpdated", description="Last-updated instant with optional prefix."),
    user_id: Optional[str] = Query(None, description="Optional: restrict to records owned by this user (JWT subject)."),
    org_id: str = Query(..., min_length=1, description="Tenant organization ID — mandatory scope of every search."),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    actor: AuthUser = Depends(require_permission("episode_of_care", "read")),
    service: EpisodeOfCareService = Depends(get_episode_of_care_service),
) -> JSONResponse:
    """
    Search EpisodeOfCares with FHIR R4 search parameters.

    Parameters are declared explicitly (with aliases) because several FHIR names are hyphenated or
    underscore-prefixed. They are gathered into ListEpisodeOfCaresSchema, whose validators (e.g. the
    status code check) run here; a failure is surfaced as a 422, not a 500.
    """
    try:
        filters = ListEpisodeOfCaresSchema(
            id=id_, identifier=identifier, status=episode_status, type=type_, patient=patient,
            organization=organization, care_manager=care_manager, condition=condition,
            incoming_referral=incoming_referral, date=date, last_updated=last_updated,
            user_id=user_id, org_id=org_id, limit=limit, offset=offset,
        )
    except ValidationError as exc:
        # include_context=False keeps the detail JSON-serialisable (ctx can hold exceptions).
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.errors(include_url=False, include_context=False),
        ) from exc
    data = await service.list(filters, actor, accept=get_accept_header(request))
    return format_paginated_response(data, request)


# ── PATCH /episode-of-cares/{resource_id} ────────────────────────────────────


@router.patch(
    "/{resource_id}",
    operation_id="update_episode_of_care",
    summary="Partially update an EpisodeOfCare",
    description=(
        "Update fields on an EpisodeOfCare. At least one field must be provided; `status` and `patient` cannot be "
        "null. `patient`, `managing_organization` and `care_manager` are `Type/id` references and can be changed "
        "through this gateway. Child lists (identifiers, status_history, types, diagnoses, referral_requests, team, "
        "accounts) use REPLACE semantics: a list that is sent replaces the stored list in full, `[]` clears it, an "
        "omitted list is left untouched. Send `Accept: application/fhir+json` for FHIR R4 format."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
    dependencies=[Depends(require_permission("episode_of_care", "update"))],
)
async def update_episode_of_care(
    resource_id: int,
    dto: EpisodeOfCarePatchSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("episode_of_care", "update")),
    service: EpisodeOfCareService = Depends(get_episode_of_care_service),
) -> JSONResponse:
    """Partially update an EpisodeOfCare. Returns 422 if the body is empty."""
    data = await service.update(resource_id, dto, actor, accept=get_accept_header(request))
    return format_response(data, request)


# ── DELETE /episode-of-cares/{resource_id} ───────────────────────────────────


@router.delete(
    "/{resource_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_episode_of_care",
    summary="Delete an EpisodeOfCare",
    description=(
        "Permanently deletes the EpisodeOfCare and all its child records. "
        "This operation is irreversible. Returns 204 No Content on success."
    ),
    responses={**_ERR_NOT_FOUND},
    dependencies=[Depends(require_permission("episode_of_care", "delete"))],
)
async def delete_episode_of_care(
    resource_id: int,
    actor: AuthUser = Depends(require_permission("episode_of_care", "delete")),
    service: EpisodeOfCareService = Depends(get_episode_of_care_service),
) -> None:
    """Permanently delete an EpisodeOfCare and cascade to all child records."""
    await service.delete(resource_id, actor)
