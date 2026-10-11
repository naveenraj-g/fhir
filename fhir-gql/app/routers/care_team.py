"""
FastAPI router for CareTeam resources.

Endpoints:
  POST   /care-teams/       — create a CareTeam (participants, reasons, managing organizations, ...)
  GET    /care-teams/{id}   — fetch a single CareTeam by public ID
  GET    /care-teams/       — paginated FHIR R4 search (patient, status, participant, category, ...)
  PATCH  /care-teams/{id}   — partial update; every child list is replaced when sent
  DELETE /care-teams/{id}   — permanent delete (cascades to all child records)

All routes support content negotiation:
  - `Accept: application/json`      → plain snake_case JSON (default)
  - `Accept: application/fhir+json` → FHIR R4 resource / Bundle

RBAC is enforced via require_permission() for the ("care_team", <action>) pair.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response, get_accept_header
from app.core.schema_utils import inline_schema
from app.di.dependencies.care_team import get_care_team_service
from app.schemas.care_team.input import CareTeamCreateSchema, CareTeamPatchSchema, ListCareTeamsSchema
from app.schemas.care_team.response import FHIRCareTeamBundle, FHIRCareTeamSchema, PlainCareTeamResponse, PaginatedCareTeamResponse
from app.services.care_team_service import CareTeamService

# All routes are prefixed with /care-teams; tagged for Swagger grouping.
router = APIRouter(prefix="/care-teams", tags=["CareTeams"])

# ── Shared error response descriptors ────────────────────────────────────────

_ERR_NOT_FOUND = {404: {"description": "CareTeam not found"}}
_ERR_VALIDATION = {422: {"description": "Validation error — request body or query params failed validation"}}

# ── Shared success response descriptors ──────────────────────────────────────
# inline_schema() resolves Pydantic's $defs/$ref pointers so both content types
# render in Swagger UI without resolver errors.

_SINGLE_201 = {
    201: {
        "description": "CareTeam created successfully",
        "content": {
            "application/json": {"schema": inline_schema(PlainCareTeamResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRCareTeamSchema.model_json_schema())},
        },
    }
}

_SINGLE_200 = {
    200: {
        "description": "CareTeam retrieved or updated successfully",
        "content": {
            "application/json": {"schema": inline_schema(PlainCareTeamResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRCareTeamSchema.model_json_schema())},
        },
    }
}

_LIST_200 = {
    200: {
        "description": "Paginated list of CareTeam resources",
        "content": {
            "application/json": {"schema": inline_schema(PaginatedCareTeamResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRCareTeamBundle.model_json_schema())},
        },
    }
}


# ── POST /care-teams/ ─────────────────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_care_team",
    summary="Create a CareTeam",
    description=(
        "Creates a CareTeam — the people and organizations planned to participate in coordinating a patient's care. "
        "Every element is optional: `status` (proposed|active|suspended|inactive|entered-in-error), `name`, "
        "`subject` (Patient|Group reference, e.g. `'Patient/10001'`), `encounter`, `period_start` / `period_end`, and "
        "the child lists `identifier`, `category`, `participant` (each with `role[]`, `member`, `on_behalf_of`, "
        "`period_*`), `reason_code`, `reason_reference` (Condition), `managing_organization` (Organization), `telecom` "
        "and `note`. Invariant ctm-1: a participant's `on_behalf_of` is only allowed when its `member` is a "
        "Practitioner. References are `Type/id` strings — only their format is validated. Send "
        "`Accept: application/fhir+json` to receive the result in FHIR R4 format."
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
    dependencies=[Depends(require_permission("care_team", "create"))],
)
async def create_care_team(
    dto: CareTeamCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("care_team", "create")),
    service: CareTeamService = Depends(get_care_team_service),
) -> JSONResponse:
    """Raise a new CareTeam and return the persisted record."""
    data = await service.create(dto, actor, accept=get_accept_header(request))
    return format_response(data, request)


# ── GET /care-teams/{resource_id} ─────────────────────────────────────────────────


@router.get(
    "/{resource_id}",
    operation_id="get_care_team",
    summary="Get a CareTeam by ID",
    description=(
        "Fetch a single CareTeam by its public integer ID. Send `Accept: application/fhir+json` for FHIR R4 format."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
    dependencies=[Depends(require_permission("care_team", "read"))],
)
async def get_care_team(
    resource_id: int,
    request: Request,
    actor: AuthUser = Depends(require_permission("care_team", "read")),
    service: CareTeamService = Depends(get_care_team_service),
) -> JSONResponse:
    """Fetch a single CareTeam by its public ID."""
    data = await service.get_by_id(resource_id, actor, accept=get_accept_header(request))
    return format_response(data, request)


# ── GET /care-teams/ ──────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_care_teams",
    summary="Search CareTeams",
    description=(
        "Searches CareTeams using the FHIR R4 CareTeam search parameters "
        "(https://www.hl7.org/fhir/R4/careteam.html#search): `category`, `date`, `encounter`, `identifier`, "
        "`participant`, `patient`, `status`, `subject` — plus `_id` and `_lastUpdated`. Token params accept `code`, "
        "`system|code`, `|code` or `system|`; comma = OR. Reference params accept `Type/id` or a bare numeric id. "
        "`date` matches the team period and, like `_lastUpdated`, takes an optional prefix eq|ne|gt|lt|ge|le|sa|eb|ap "
        "(repeat for AND). `org_id` is mandatory on every search (tenant scope) and `user_id` is optional; paginate "
        "with `limit` / `offset`. Send `Accept: application/fhir+json` to receive a FHIR Bundle searchset."
    ),
    responses={**_LIST_200, **_ERR_VALIDATION},
    dependencies=[Depends(require_permission("care_team", "read"))],
)
async def list_care_teams(
    request: Request,
    id_: Optional[str] = Query(None, alias="_id", description="Public care_team_id(s), comma-separated."),
    identifier: Optional[str] = Query(None, description="Token `[system|]value` of CareTeam.identifier."),
    ct_status: Optional[str] = Query(None, alias="status", description="Token: proposed|active|suspended|inactive|entered-in-error (comma = OR)."),
    category: Optional[str] = Query(None, description="Token `[system|]code` of CareTeam.category."),
    subject: Optional[str] = Query(None, description="Subject reference (Patient|Group), e.g. `Patient/10001`."),
    patient: Optional[str] = Query(None, description="Subject patient reference: `Patient/10001` or `10001`."),
    encounter: Optional[str] = Query(None, description="Encounter reference: `Encounter/20001` or `20001`."),
    participant: Optional[str] = Query(None, description="participant.member reference: Practitioner|PractitionerRole|RelatedPerson|Patient|Organization|CareTeam."),
    date: Optional[List[str]] = Query(None, description="Team period with optional prefix, e.g. `ge2024-01-01`. Repeat for AND."),
    last_updated: Optional[List[str]] = Query(None, alias="_lastUpdated", description="Last-updated instant with optional prefix."),
    user_id: Optional[str] = Query(None, description="Optional: restrict to records owned by this user (JWT subject)."),
    org_id: str = Query(..., min_length=1, description="Tenant organization ID — mandatory scope of every search."),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    actor: AuthUser = Depends(require_permission("care_team", "read")),
    service: CareTeamService = Depends(get_care_team_service),
) -> JSONResponse:
    """
    Search CareTeams with FHIR R4 search parameters.

    Parameters are declared explicitly (with aliases) because `_id` and `_lastUpdated`
    are not valid Python identifiers. They are gathered into ListCareTeamsSchema, whose
    validators (e.g. the status code check) run here; a failure is surfaced as a 422.
    """
    try:
        filters = ListCareTeamsSchema(
            id=id_, identifier=identifier, status=ct_status, category=category, subject=subject, patient=patient,
            encounter=encounter, participant=participant, date=date, last_updated=last_updated,
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


# ── PATCH /care-teams/{resource_id} ───────────────────────────────────────────────


@router.patch(
    "/{resource_id}",
    operation_id="update_care_team",
    summary="Partially update a CareTeam",
    description=(
        "Update fields on a CareTeam. At least one field must be provided. Scalar fields (`status`, `name`, "
        "`period_*`, `subject`, `encounter` and their `*_display`) are updated when present; references are "
        "`Type/id`. The child lists `identifier`, `category`, `participant`, `reason_code`, `reason_reference`, "
        "`managing_organization`, `telecom` and `note` use REPLACE semantics: a list that is sent replaces the stored "
        "list in full, `[]` clears it, and an omitted list is left untouched. Send `Accept: application/fhir+json` for "
        "FHIR R4 format."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
    dependencies=[Depends(require_permission("care_team", "update"))],
)
async def update_care_team(
    resource_id: int,
    dto: CareTeamPatchSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("care_team", "update")),
    service: CareTeamService = Depends(get_care_team_service),
) -> JSONResponse:
    """Partially update a CareTeam. Returns 422 if the body is empty."""
    data = await service.update(resource_id, dto, actor, accept=get_accept_header(request))
    return format_response(data, request)


# ── DELETE /care-teams/{resource_id} ──────────────────────────────────────────────


@router.delete(
    "/{resource_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_care_team",
    summary="Delete a CareTeam",
    description=(
        "Permanently deletes the CareTeam and its child records (identifier, category). "
        "This operation is irreversible. Returns 204 No Content on success."
    ),
    responses={**_ERR_NOT_FOUND},
    dependencies=[Depends(require_permission("care_team", "delete"))],
)
async def delete_care_team(
    resource_id: int,
    actor: AuthUser = Depends(require_permission("care_team", "delete")),
    service: CareTeamService = Depends(get_care_team_service),
) -> None:
    """Permanently delete a CareTeam and cascade to its child records."""
    await service.delete(resource_id, actor)
