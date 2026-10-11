from typing import Optional

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Request, status

from app.deps.episode_of_care_deps import resolve_episode_of_care
from app.core.content_negotiation import format_paginated_response, format_response
from app.core.schema_utils import inline_schema
from app.di.dependencies.episode_of_care import get_episode_of_care_service
from app.models.episode_of_care.enums import EpisodeOfCareStatus
from app.models.episode_of_care.episode_of_care import EpisodeOfCareModel
from app.schemas.episode_of_care.input import EpisodeOfCareCreateSchema, EpisodeOfCarePatchSchema
from app.schemas.episode_of_care.response import (
    FHIREpisodeOfCareBundle,
    FHIREpisodeOfCareSchema,
    PaginatedEpisodeOfCareResponse,
    PlainEpisodeOfCareResponse,
)
from app.repository.episode_of_care_repository import EpisodeOfCareSearch
from app.services.episode_of_care_service import EpisodeOfCareService

router = APIRouter()

_CONTENT_NEG = (
    "Set `Accept: application/fhir+json` to receive the full FHIR R4 representation; "
    "omit or use `Accept: application/json` for the simplified plain-JSON form."
)

_ERR_NOT_FOUND = {404: {"description": "EpisodeOfCare not found"}}
_ERR_VALIDATION = {422: {"description": "Validation error"}}

_SINGLE_200 = {
    200: {
        "content": {
            "application/json": {"schema": inline_schema(PlainEpisodeOfCareResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIREpisodeOfCareSchema.model_json_schema())},
        }
    }
}
_SINGLE_201 = {201: _SINGLE_200[200]}
_LIST_200 = {
    200: {
        "description": "Paginated list of EpisodeOfCare resources",
        "content": {
            "application/json": {"schema": inline_schema(PaginatedEpisodeOfCareResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIREpisodeOfCareBundle.model_json_schema())},
        },
    }
}


# ── Create ────────────────────────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_episode_of_care",
    summary="Create a new EpisodeOfCare resource",
    description=(
        "Creates a FHIR R4 EpisodeOfCare resource grouping encounters for a patient "
        "around a specific care issue. " + _CONTENT_NEG
    ),
    response_description="The newly created EpisodeOfCare resource",
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_episode_of_care(
    payload: EpisodeOfCareCreateSchema,
    request: Request,
    service: EpisodeOfCareService = Depends(get_episode_of_care_service),
):
    created_by = payload.created_by
    eoc = await service.create_episode_of_care(payload, created_by)
    return format_response(
        service._to_fhir(eoc),
        service._to_plain(eoc),
        request,
    )





@router.get(
    "/{episode_of_care_id}",
    operation_id="get_episode_of_care",
    summary="Retrieve an EpisodeOfCare by public identifier",
    description="Fetches a single EpisodeOfCare resource by its public `episode_of_care_id`. " + _CONTENT_NEG,
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_episode_of_care(
    request: Request,
    eoc: EpisodeOfCareModel = Depends(resolve_episode_of_care),
    service: EpisodeOfCareService = Depends(get_episode_of_care_service),
):
    return format_response(
        service._to_fhir(eoc),
        service._to_plain(eoc),
        request,
    )


# ── Patch ─────────────────────────────────────────────────────────────────────


@router.patch(
    "/{episode_of_care_id}",
    operation_id="patch_episode_of_care",
    summary="Partially update an EpisodeOfCare",
    description=(
        "Updates an EpisodeOfCare resource. Only supplied fields are changed; `status` and `patient` cannot be null. "
        "`managing_organization` and `care_manager` are `Type/id` references (null clears them). Child lists "
        "(identifiers, status_history, types, diagnoses, referral_requests, team, accounts) use REPLACE semantics: "
        "a list that is sent replaces the stored list in full, `[]` clears it, an omitted list is left untouched. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_episode_of_care(
    payload: EpisodeOfCarePatchSchema,
    request: Request,
    eoc: EpisodeOfCareModel = Depends(resolve_episode_of_care),
    service: EpisodeOfCareService = Depends(get_episode_of_care_service),
):
    updated_by = payload.updated_by
    updated = await service.patch_episode_of_care(eoc, payload, updated_by)
    return format_response(
        service._to_fhir(updated),
        service._to_plain(updated),
        request,
    )


# ── List ──────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_episode_of_cares",
    summary="Search EpisodeOfCare resources",
    description=(
        "Searches EpisodeOfCares using the FHIR R4 EpisodeOfCare search parameters "
        "(https://www.hl7.org/fhir/R4/episodeofcare.html#search): `care-manager`, `condition`, `date`, `identifier`, "
        "`incoming-referral`, `organization`, `patient`, `status`, `type` — plus `_id` and `_lastUpdated`. "
        "Token params (`identifier`, `status`, `type`) accept `code`, `system|code`, `|code` or `system|`; comma = OR. "
        "Reference params (`patient`, `organization`, `care-manager`, `condition`, `incoming-referral`) accept "
        "`Type/id` or a bare numeric id. `date` matches the episode period (an open end means ongoing) and, like "
        "`_lastUpdated`, takes an optional prefix eq|ne|gt|lt|ge|le|sa|eb|ap; repeat for AND. "
        "`org_id` is mandatory on every search (tenant scope) and `user_id` is optional; paginate with `limit` / "
        "`offset`. " + _CONTENT_NEG
    ),
    responses={**_LIST_200, **_ERR_VALIDATION},
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
    patient_id: Optional[int] = Query(None, description="Legacy: public patient_id. Same as `patient`."),
    user_id: Optional[str] = Query(None, description="Optional: restrict to records owned by this user."),
    org_id: str = Query(..., min_length=1, description="Tenant organization id — mandatory scope of every search."),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: EpisodeOfCareService = Depends(get_episode_of_care_service),
):
    search = EpisodeOfCareSearch(
        id=id_, identifier=identifier, eoc_status=episode_status, type=type_,
        patient=patient or (str(patient_id) if patient_id is not None else None),
        organization=organization, care_manager=care_manager, condition=condition,
        incoming_referral=incoming_referral, date=date or [], last_updated=last_updated or [],
    )
    total, rows = await service.list_episode_of_cares(
        user_id=user_id, org_id=org_id, search=search, limit=limit, offset=offset,
    )
    return format_paginated_response(
        [service._to_fhir(e) for e in rows],
        [service._to_plain(e) for e in rows],
        total, limit, offset, request,
    )


# ── Delete ────────────────────────────────────────────────────────────────────


@router.delete(
    "/{episode_of_care_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_episode_of_care",
    summary="Delete an EpisodeOfCare resource",
    description="Permanently deletes an EpisodeOfCare and all its related child records.",
    responses={**_ERR_NOT_FOUND},
)
async def delete_episode_of_care(
    eoc: EpisodeOfCareModel = Depends(resolve_episode_of_care),
    service: EpisodeOfCareService = Depends(get_episode_of_care_service),
):
    await service.delete_episode_of_care(eoc)
