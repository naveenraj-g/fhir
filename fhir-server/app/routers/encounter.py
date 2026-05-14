from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth.dependencies import require_permission
from app.auth.encounter_deps import get_authorized_encounter
from app.core.content_negotiation import format_response, format_list_response
from app.di.dependencies.encounter import get_encounter_service
from app.models.encounter.encounter import EncounterModel
from app.schemas.encounter import (
    EncounterCreateSchema,
    EncounterPatchSchema,
    EncounterResponseSchema,
)
from app.services.encounter_service import EncounterService

router = APIRouter()

_CONTENT_NEG = (
    "Set `Accept: application/fhir+json` to receive the full FHIR R4 representation; "
    "omit or use `Accept: application/json` for the simplified plain-JSON form."
)

_ERR_AUTH = {
    401: {"description": "Not authenticated — Bearer token missing or expired"},
    403: {"description": "Forbidden — caller lacks the required permission"},
}
_ERR_NOT_FOUND = {404: {"description": "Encounter not found"}}
_ERR_VALIDATION = {422: {"description": "Validation error — request body failed schema validation"}}


# ── Create Encounter ───────────────────────────────────────────────────────


@router.post(
    "/",
    response_model=EncounterResponseSchema,
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("encounter", "create"))],
    operation_id="create_encounter",
    summary="Create a new Encounter resource",
    description=(
        "Creates an Encounter — a clinical interaction between a patient and one or more providers "
        "(e.g. outpatient visit, inpatient admission, telehealth session, emergency visit). "
        "All sub-resources (encounter types, participants, reason codes, diagnoses, locations) "
        "are submitted as part of a single document in the request body. "
        "References use public IDs: `Patient/10001`, `Practitioner/30001`. "
        "The caller's `sub` and `activeOrganizationId` JWT claims are automatically bound to the record. "
        + _CONTENT_NEG
    ),
    response_description="The newly created Encounter resource",
    responses={**_ERR_AUTH, **_ERR_VALIDATION},
)
async def create_encounter(
    payload: EncounterCreateSchema,
    request: Request,
    encounter_service: EncounterService = Depends(get_encounter_service),
):
    created_by: str = request.state.user.get("sub")
    encounter = await encounter_service.create_encounter(payload, payload.user_id, payload.org_id, created_by)
    return format_response(
        encounter_service._to_fhir(encounter),
        encounter_service._to_plain(encounter),
        request,
    )


# ── Get own Encounters (/me) ───────────────────────────────────────────────
# Declared before /{encounter_id} to avoid routing conflicts.


@router.get(
    "/me",
    response_model=list[EncounterResponseSchema],
    response_model_exclude_none=True,
    dependencies=[Depends(require_permission("encounter", "read"))],
    operation_id="get_my_encounters",
    summary="List all Encounter resources for the currently authenticated user",
    description=(
        "Returns all Encounter records linked to the authenticated user's `sub` claim "
        "and `activeOrganizationId`. "
        "Includes encounters where the user is a subject (patient) or participant (practitioner). "
        + _CONTENT_NEG
    ),
    response_description="Array of Encounter resources for the current user",
    responses={**_ERR_AUTH},
)
async def get_my_encounters(
    request: Request,
    encounter_service: EncounterService = Depends(get_encounter_service),
):
    user_id: str = request.state.user.get("sub")
    org_id: str = request.state.user.get("activeOrganizationId")
    encounters = await encounter_service.get_me(user_id, org_id)
    return format_list_response(
        [encounter_service._to_fhir(e) for e in encounters],
        [encounter_service._to_plain(e) for e in encounters],
        request,
    )


# ── Get Encounter by public encounter_id ──────────────────────────────────


@router.get(
    "/{encounter_id}",
    response_model=EncounterResponseSchema,
    response_model_exclude_none=True,
    dependencies=[Depends(require_permission("encounter", "read"))],
    operation_id="get_encounter_by_id",
    summary="Retrieve an Encounter resource by public encounter_id",
    description=(
        "Fetches a single Encounter by its public integer `encounter_id`. "
        "Access is subject to organization-scoped authorization — the encounter must belong to the caller's active organization. "
        + _CONTENT_NEG
    ),
    response_description="The requested Encounter resource",
    responses={
        **_ERR_AUTH,
        403: {"description": "Forbidden — caller lacks `encounter:read` permission or the encounter belongs to a different organization"},
        **_ERR_NOT_FOUND,
    },
)
async def get_encounter(
    request: Request,
    encounter: EncounterModel = Depends(get_authorized_encounter),
    encounter_service: EncounterService = Depends(get_encounter_service),
):
    return format_response(
        encounter_service._to_fhir(encounter),
        encounter_service._to_plain(encounter),
        request,
    )


# ── Patch Encounter ────────────────────────────────────────────────────────


@router.patch(
    "/{encounter_id}",
    response_model=EncounterResponseSchema,
    response_model_exclude_none=True,
    dependencies=[Depends(require_permission("encounter", "update"))],
    operation_id="patch_encounter",
    summary="Partially update an Encounter resource",
    description=(
        "Only lifecycle fields are patchable: `status`, `period_end`, `priority`. "
        "Structural data (subject, participants, types, diagnoses, locations) cannot be changed after creation — "
        "delete and re-create the Encounter to correct structural errors. "
        + _CONTENT_NEG
    ),
    response_description="The updated Encounter resource",
    responses={**_ERR_AUTH, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_encounter(
    payload: EncounterPatchSchema,
    request: Request,
    encounter: EncounterModel = Depends(get_authorized_encounter),
    encounter_service: EncounterService = Depends(get_encounter_service),
):
    updated_by: str = request.state.user.get("sub")
    updated = await encounter_service.patch_encounter(encounter.encounter_id, payload, updated_by)
    if not updated:
        raise HTTPException(status_code=404, detail="Encounter not found")
    return format_response(
        encounter_service._to_fhir(updated),
        encounter_service._to_plain(updated),
        request,
    )


# ── List Encounters ────────────────────────────────────────────────────────


@router.get(
    "/",
    response_model=list[EncounterResponseSchema],
    response_model_exclude_none=True,
    dependencies=[Depends(require_permission("encounter", "read"))],
    operation_id="list_encounters",
    summary="List all Encounter resources",
    description=(
        "Returns all Encounter resources accessible to the caller. "
        "Optionally filter by subject patient using `?patient_id={patient_id}` (public integer patient_id). "
        "Results are scoped to the caller's active organization. "
        + _CONTENT_NEG
    ),
    response_description="Array of Encounter resources",
    responses={**_ERR_AUTH},
)
async def list_encounters(
    request: Request,
    patient_id: Optional[int] = None,
    encounter_service: EncounterService = Depends(get_encounter_service),
):
    encounters = await encounter_service.list_encounters(patient_id=patient_id)
    return format_list_response(
        [encounter_service._to_fhir(e) for e in encounters],
        [encounter_service._to_plain(e) for e in encounters],
        request,
    )


# ── Delete Encounter ───────────────────────────────────────────────────────


@router.delete(
    "/{encounter_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("encounter", "delete"))],
    operation_id="delete_encounter",
    summary="Delete an Encounter resource",
    description=(
        "Permanently deletes the Encounter and all its sub-resources "
        "(types, participants, reason codes, diagnoses, locations). "
        "This operation is irreversible. Returns 204 No Content on success."
    ),
    responses={**_ERR_AUTH, **_ERR_NOT_FOUND},
)
async def delete_encounter(
    encounter: EncounterModel = Depends(get_authorized_encounter),
    encounter_service: EncounterService = Depends(get_encounter_service),
):
    await encounter_service.delete_encounter(encounter.encounter_id)
    return None
