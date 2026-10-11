from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.core.content_negotiation import format_paginated_response, format_response
from app.core.schema_utils import inline_schema
from app.deps.care_team_deps import resolve_care_team
from app.di.dependencies.care_team import get_care_team_service
from app.models.care_team.care_team import CareTeamModel
from app.repository.care_team_repository import CareTeamSearch
from app.schemas.care_team import CareTeamCreateSchema, CareTeamPatchSchema
from app.schemas.care_team.response import (
    FHIRCareTeamBundle,
    FHIRCareTeamSchema,
    PaginatedCareTeamResponse,
    PlainCareTeamResponse,
)
from app.services.care_team_service import CareTeamService

router = APIRouter()

_CONTENT_NEG = (
    "Set `Accept: application/fhir+json` to receive the full FHIR R4 representation; "
    "omit or use `Accept: application/json` for the simplified plain-JSON form."
)

_ERR_NOT_FOUND = {404: {"description": "CareTeam not found"}}
_ERR_VALIDATION = {422: {"description": "Validation error — request body or query params failed validation"}}

_SINGLE_200 = {
    200: {
        "content": {
            "application/json": {"schema": inline_schema(PlainCareTeamResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRCareTeamSchema.model_json_schema())},
        }
    }
}
_SINGLE_201 = {201: _SINGLE_200[200]}
_LIST_200 = {
    200: {
        "description": "Paginated list of care teams",
        "content": {
            "application/json": {"schema": inline_schema(PaginatedCareTeamResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRCareTeamBundle.model_json_schema())},
        },
    }
}


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_care_team",
    summary="Create a new CareTeam resource",
    description=(
        "Creates a CareTeam — the people and organizations planned to participate in coordinating a patient's care. "
        "Every element is optional: `status` (proposed|active|suspended|inactive|entered-in-error), `name`, "
        "`subject` (Patient|Group reference, e.g. `'Patient/10001'`), `encounter`, `period_start` / `period_end`, and "
        "the child lists `identifier`, `category`, `participant` (each with `role[]`, `member`, `on_behalf_of`, "
        "`period_*`), `reason_code`, `reason_reference` (Condition), `managing_organization` (Organization), "
        "`telecom` and `note`. Invariant ctm-1: a participant's `on_behalf_of` is only allowed when its `member` is a "
        "Practitioner. References are `Type/id` strings — only their format is validated. " + _CONTENT_NEG
    ),
    response_description="The newly created CareTeam resource",
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_care_team(
    payload: CareTeamCreateSchema,
    request: Request,
    service: CareTeamService = Depends(get_care_team_service),
):
    ct = await service.create_care_team(payload, payload.user_id, payload.org_id, payload.created_by)
    return format_response(service._to_fhir(ct), service._to_plain(ct), request)


@router.get(
    "/{care_team_id}",
    operation_id="get_care_team_by_id",
    summary="Retrieve a CareTeam resource by public care_team_id",
    description="Fetches a single CareTeam by its public integer `care_team_id`. " + _CONTENT_NEG,
    response_description="The requested CareTeam resource",
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_care_team(
    request: Request,
    care_team: CareTeamModel = Depends(resolve_care_team),
    service: CareTeamService = Depends(get_care_team_service),
):
    return format_response(service._to_fhir(care_team), service._to_plain(care_team), request)


@router.patch(
    "/{care_team_id}",
    operation_id="patch_care_team",
    summary="Partially update a CareTeam resource",
    description=(
        "Scalar fields (`status`, `name`, `period_*`, `subject`, `encounter` and their `*_display`) are updated when "
        "present; references are `Type/id` and null clears them. The child lists `identifier`, `category`, "
        "`participant`, `reason_code`, `reason_reference`, `managing_organization`, `telecom` and `note` use REPLACE "
        "semantics: a list that is sent replaces the stored list in full, `[]`/null clears it, and an omitted list is "
        "left untouched. " + _CONTENT_NEG
    ),
    response_description="The updated CareTeam resource",
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_care_team(
    payload: CareTeamPatchSchema,
    request: Request,
    care_team: CareTeamModel = Depends(resolve_care_team),
    service: CareTeamService = Depends(get_care_team_service),
):
    updated = await service.patch_care_team(care_team.care_team_id, payload, payload.updated_by)
    if not updated:
        raise HTTPException(status_code=404, detail="CareTeam not found")
    return format_response(service._to_fhir(updated), service._to_plain(updated), request)


@router.get(
    "/",
    operation_id="list_care_teams",
    summary="Search CareTeam resources",
    description=(
        "Searches CareTeams using the FHIR R4 CareTeam search parameters "
        "(https://www.hl7.org/fhir/R4/careteam.html#search): `category`, `date`, `encounter`, `identifier`, "
        "`participant`, `patient`, `status`, `subject` — plus `_id` and `_lastUpdated`. "
        "Token params (`identifier`, `status`, `category`) accept `code`, `system|code`, `|code` or `system|`; comma = "
        "OR. Reference params (`subject`, `patient`, `encounter`, `participant`) accept `Type/id` or a bare numeric id. "
        "`date` matches the team period and, like `_lastUpdated`, takes an optional prefix eq|ne|gt|lt|ge|le|sa|eb|ap "
        "(repeat for AND). `org_id` is mandatory on every search (tenant scope) and `user_id` is optional; paginate "
        "with `limit` / `offset`. " + _CONTENT_NEG
    ),
    response_description="Paginated CareTeam resources",
    responses={**_LIST_200, **_ERR_VALIDATION},
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
    user_id: Optional[str] = Query(None, description="Optional: restrict to records owned by this user."),
    org_id: str = Query(..., min_length=1, description="Tenant organization id — mandatory scope of every search."),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: CareTeamService = Depends(get_care_team_service),
):
    search = CareTeamSearch(
        id=id_, identifier=identifier, ct_status=ct_status, category=category, subject=subject, patient=patient,
        encounter=encounter, participant=participant, date=date or [], last_updated=last_updated or [],
    )
    items, total = await service.list_care_teams(user_id=user_id, org_id=org_id, search=search, limit=limit, offset=offset)
    return format_paginated_response(
        [service._to_fhir(i) for i in items],
        [service._to_plain(i) for i in items],
        total, limit, offset, request,
    )


@router.delete(
    "/{care_team_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_care_team",
    summary="Delete a CareTeam resource",
    description=(
        "Permanently deletes the CareTeam and its child records (participants, identifiers, categories, ...). "
        "This operation is irreversible. Returns 204 No Content on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_care_team(
    care_team: CareTeamModel = Depends(resolve_care_team),
    service: CareTeamService = Depends(get_care_team_service),
):
    await service.delete_care_team(care_team.care_team_id)
    return None
