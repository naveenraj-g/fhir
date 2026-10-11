from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.deps.procedure_deps import resolve_procedure
from app.core.content_negotiation import format_response, format_paginated_response
from app.core.schema_utils import inline_schema
from app.di.dependencies.procedure import get_procedure_service
from app.models.procedure.procedure import ProcedureModel
from app.schemas.procedure import ProcedureCreateSchema, ProcedurePatchSchema
from app.schemas.procedure.response import (
    FHIRProcedureSchema,
    FHIRProcedureBundle,
    PaginatedProcedureResponse,
    PlainProcedureResponse,
)
from app.repository.procedure_repository import ProcedureSearch
from app.services.procedure_service import ProcedureService

router = APIRouter()

_CONTENT_NEG = (
    "Set `Accept: application/fhir+json` to receive the full FHIR R4 representation; "
    "omit or use `Accept: application/json` for the simplified plain-JSON form."
)

_ERR_NOT_FOUND = {404: {"description": "Procedure not found"}}
_ERR_VALIDATION = {422: {"description": "Validation error — request body failed schema validation"}}

_SINGLE_200 = {
    200: {
        "content": {
            "application/json": {"schema": inline_schema(PlainProcedureResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRProcedureSchema.model_json_schema())},
        }
    }
}
_SINGLE_201 = {201: _SINGLE_200[200]}
_LIST_200 = {
    200: {
        "description": "Paginated list of procedures",
        "content": {
            "application/json": {"schema": inline_schema(PaginatedProcedureResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRProcedureBundle.model_json_schema())},
        },
    }
}


# ── Create Procedure ───────────────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_procedure",
    summary="Create a new Procedure resource",
    description=(
        "Records an action that is or was performed on or for a patient. "
        "Requires `status`. Provide `subject` as a FHIR reference e.g. `'Patient/10001'`. "
        "Optionally link to an Encounter via `encounter_id` (public encounter_id). "
        "Supply `performed[x]` via one of: `performed_datetime`, `performed_period_*`, "
        "`performed_string`, `performed_age_*`, or `performed_range_*`. "
        + _CONTENT_NEG
    ),
    response_description="The newly created Procedure resource",
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_procedure(
    payload: ProcedureCreateSchema,
    request: Request,
    proc_service: ProcedureService = Depends(get_procedure_service),
):
    created_by = payload.created_by
    proc = await proc_service.create_procedure(
        payload, payload.user_id, payload.org_id, created_by
    )
    return format_response(
        proc_service._to_fhir(proc),
        proc_service._to_plain(proc),
        request,
    )


@router.get(
    "/{procedure_id}",
    operation_id="get_procedure_by_id",
    summary="Retrieve a Procedure resource by public procedure_id",
    description=(
        "Fetches a single Procedure by its public integer `procedure_id`. "
        + _CONTENT_NEG
    ),
    response_description="The requested Procedure resource",
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_procedure(
    request: Request,
    proc: ProcedureModel = Depends(resolve_procedure),
    proc_service: ProcedureService = Depends(get_procedure_service),
):
    return format_response(
        proc_service._to_fhir(proc),
        proc_service._to_plain(proc),
        request,
    )


# ── Patch Procedure ────────────────────────────────────────────────────────────


@router.patch(
    "/{procedure_id}",
    operation_id="patch_procedure",
    summary="Partially update a Procedure resource",
    description=(
        "Patchable fields: `status`, `status_reason_*`, `category_*`, `code_*`, "
        "`subject` (Patient/Group reference), `subject_display`, `encounter_id` (null unlinks), `encounter_display`, "
        "`performed_datetime`, `performed_period_*`, `performed_string`, `performed_age_*`, `performed_range_*`, "
        "`recorder`, `asserter`, `location` (FHIR references; null clears) and their `*_display`, "
        "`outcome_*`, `instantiates_canonical`, `instantiates_uri`. "
        "Child lists (identifier, based_on, part_of, performer, reason_code, reason_reference, body_site, "
        "report, complication, complication_detail, follow_up, note, focal_device, used_reference, used_code) "
        "are also patchable with REPLACE semantics: a list that is sent replaces the stored list in full, "
        "`[]` clears it, and an omitted list is left untouched. "
        + _CONTENT_NEG
    ),
    response_description="The updated Procedure resource",
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_procedure(
    payload: ProcedurePatchSchema,
    request: Request,
    proc: ProcedureModel = Depends(resolve_procedure),
    proc_service: ProcedureService = Depends(get_procedure_service),
):
    updated_by = payload.updated_by
    updated = await proc_service.patch_procedure(
        proc.procedure_id, payload, updated_by
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Procedure not found")
    return format_response(
        proc_service._to_fhir(updated),
        proc_service._to_plain(updated),
        request,
    )


# ── List Procedures ────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_procedures",
    summary="Search Procedure resources",
    description=(
        "Searches Procedure resources using the FHIR R4 Procedure search parameters "
        "(https://www.hl7.org/fhir/R4/procedure.html#search). "
        "Token params (`status`, `code`, `category`, `identifier`, `reason-code`) accept `code`, `system|code`, "
        "`|code` or `system|`. Reference params (`patient`, `subject`, `encounter`, `performer`, `location`, "
        "`part-of`, `based-on`, `reason-reference`) accept `Type/id` or a bare numeric id. "
        "Comma-separated values are OR; repeat `date` / `_lastUpdated` for AND (e.g. a range). "
        "Date params take an optional prefix eq|ne|gt|lt|ge|le|sa|eb|ap, e.g. `date=ge2024-01-01&date=lt2024-02-01`; "
        "`date` matches performedDateTime or performedPeriod. "
        "`org_id` is mandatory on every search (tenant scope) and `user_id` is optional; paginate with `limit` and `offset`. "
        + _CONTENT_NEG
    ),
    response_description="Paginated Procedure resources",
    responses={**_LIST_200, **_ERR_VALIDATION},
)
async def list_procedures(
    request: Request,
    id_: Optional[str] = Query(None, alias="_id", description="Public procedure_id(s), comma-separated."),
    identifier: Optional[str] = Query(None, description="Token `[system|]value` of Procedure.identifier."),
    proc_status: Optional[str] = Query(
        None, alias="status",
        description="Token: preparation|in-progress|not-done|on-hold|stopped|completed|entered-in-error|unknown (comma = OR).",
    ),
    category: Optional[str] = Query(None, description="Token `[system|]code` of Procedure.category."),
    code: Optional[str] = Query(None, description="Token `[system|]code` of Procedure.code, e.g. `http://snomed.info/sct|80146002`."),
    patient: Optional[str] = Query(None, description="Subject patient reference: `Patient/10001` or `10001`."),
    subject: Optional[str] = Query(None, description="Subject reference (Patient or Group): `Patient/10001`, `Group/1`."),
    encounter: Optional[str] = Query(None, description="Encounter reference: `Encounter/20001` or `20001`."),
    date: Optional[List[str]] = Query(None, description="performed[x] date with optional prefix, e.g. `ge2024-01-01`. Repeat for AND."),
    performer: Optional[str] = Query(None, description="Performer.actor reference, e.g. `Practitioner/30001`."),
    location: Optional[str] = Query(None, description="Location reference, e.g. `Location/230001`."),
    part_of: Optional[str] = Query(None, alias="part-of", description="partOf reference: Procedure|Observation|MedicationAdministration."),
    based_on: Optional[str] = Query(None, alias="based-on", description="basedOn reference: CarePlan|ServiceRequest."),
    reason_code: Optional[str] = Query(None, alias="reason-code", description="Token `[system|]code` of Procedure.reasonCode."),
    reason_reference: Optional[str] = Query(None, alias="reason-reference", description="reasonReference: Condition|Observation|Procedure|DiagnosticReport|DocumentReference."),
    instantiates_canonical: Optional[str] = Query(None, alias="instantiates-canonical", description="Canonical URI of an instantiated protocol."),
    instantiates_uri: Optional[str] = Query(None, alias="instantiates-uri", description="URI of an instantiated external protocol."),
    last_updated: Optional[List[str]] = Query(None, alias="_lastUpdated", description="Last-updated instant with optional prefix. Repeat for AND."),
    patient_id: Optional[int] = Query(None, description="Legacy: public patient_id. Same as `patient`."),
    encounter_id: Optional[int] = Query(None, description="Legacy: public encounter_id. Same as `encounter`."),
    performed_from: Optional[datetime] = Query(None, description="Legacy: performed start >= this value."),
    performed_to: Optional[datetime] = Query(None, description="Legacy: performed start <= this value."),
    user_id: Optional[str] = Query(None, description="Optional: restrict to records owned by this user."),
    org_id: str = Query(..., min_length=1, description="Tenant organization id — mandatory scope of every search."),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    proc_service: ProcedureService = Depends(get_procedure_service),
):
    search = ProcedureSearch(
        id=id_,
        identifier=identifier,
        status=proc_status,
        category=category,
        code=code,
        patient=patient or (str(patient_id) if patient_id is not None else None),
        subject=subject,
        encounter=encounter or (str(encounter_id) if encounter_id is not None else None),
        date=date or [],
        performer=performer,
        location=location,
        part_of=part_of,
        based_on=based_on,
        reason_code=reason_code,
        reason_reference=reason_reference,
        instantiates_canonical=instantiates_canonical,
        instantiates_uri=instantiates_uri,
        last_updated=last_updated or [],
        performed_from=performed_from,
        performed_to=performed_to,
    )
    items, total = await proc_service.list_procedures(
        user_id=user_id, org_id=org_id, search=search, limit=limit, offset=offset,
    )
    return format_paginated_response(
        [proc_service._to_fhir(p) for p in items],
        [proc_service._to_plain(p) for p in items],
        total, limit, offset, request,
    )


# ── Delete Procedure ───────────────────────────────────────────────────────────


@router.delete(
    "/{procedure_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_procedure",
    summary="Delete a Procedure resource",
    description=(
        "Permanently deletes the Procedure and all its associated child records "
        "(identifier, basedOn, partOf, performer, reasonCode, reasonReference, bodySite, "
        "report, complication, complicationDetail, followUp, note, focalDevice, usedReference, usedCode). "
        "This operation is irreversible. Returns 204 No Content on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_procedure(
    proc: ProcedureModel = Depends(resolve_procedure),
    proc_service: ProcedureService = Depends(get_procedure_service),
):
    await proc_service.delete_procedure(proc.procedure_id)
    return None
