from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.core.content_negotiation import format_paginated_response, format_response
from app.core.schema_utils import inline_schema
from app.deps.risk_assessment_deps import resolve_risk_assessment
from app.di.dependencies.risk_assessment import get_risk_assessment_service
from app.models.risk_assessment.risk_assessment import RiskAssessmentModel
from app.repository.risk_assessment_repository import RiskAssessmentSearch
from app.schemas.risk_assessment import RiskAssessmentCreateSchema, RiskAssessmentPatchSchema
from app.schemas.risk_assessment.response import (
    FHIRRiskAssessmentBundle,
    FHIRRiskAssessmentSchema,
    PaginatedRiskAssessmentResponse,
    PlainRiskAssessmentResponse,
)
from app.services.risk_assessment_service import RiskAssessmentService

router = APIRouter()

_CONTENT_NEG = (
    "Set `Accept: application/fhir+json` to receive the full FHIR R4 representation; "
    "omit or use `Accept: application/json` for the simplified plain-JSON form."
)

_ERR_NOT_FOUND = {404: {"description": "RiskAssessment not found"}}
_ERR_VALIDATION = {422: {"description": "Validation error — request body or query params failed validation"}}

_SINGLE_200 = {
    200: {
        "content": {
            "application/json": {"schema": inline_schema(PlainRiskAssessmentResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRRiskAssessmentSchema.model_json_schema())},
        }
    }
}
_SINGLE_201 = {201: _SINGLE_200[200]}
_LIST_200 = {
    200: {
        "description": "Paginated list of risk assessments",
        "content": {
            "application/json": {"schema": inline_schema(PaginatedRiskAssessmentResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRRiskAssessmentBundle.model_json_schema())},
        },
    }
}


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_risk_assessment",
    summary="Create a new RiskAssessment resource",
    description=(
        "Records an assessment of the likely outcome(s) for a patient or group. `status` and `subject` are required. "
        "Provide `subject` as `'Patient/10001'` (or `Group/<id>`); optionally link an Encounter via `encounter_id` "
        "(public encounter_id), a `condition`, and a `performer` (Practitioner|PractitionerRole|Device). "
        "`occurrence_datetime` OR `occurrence_period_*`. Each `prediction` carries an outcome, a probability "
        "(`probability_decimal` ≤ 100, or `probability_range_*` in %), an optional `qualitative_risk`, `relative_risk`, "
        "`when_period_*` or `when_range_*`, and a `rationale`. All child arrays (identifier, reason_code, "
        "reason_reference, basis, prediction, note) are submitted in the single request body. " + _CONTENT_NEG
    ),
    response_description="The newly created RiskAssessment resource",
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_risk_assessment(
    payload: RiskAssessmentCreateSchema,
    request: Request,
    service: RiskAssessmentService = Depends(get_risk_assessment_service),
):
    ra = await service.create_risk_assessment(payload, payload.user_id, payload.org_id, payload.created_by)
    return format_response(service._to_fhir(ra), service._to_plain(ra), request)


@router.get(
    "/{risk_assessment_id}",
    operation_id="get_risk_assessment_by_id",
    summary="Retrieve a RiskAssessment resource by public risk_assessment_id",
    description="Fetches a single RiskAssessment by its public integer `risk_assessment_id`. " + _CONTENT_NEG,
    response_description="The requested RiskAssessment resource",
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_risk_assessment(
    request: Request,
    ra: RiskAssessmentModel = Depends(resolve_risk_assessment),
    service: RiskAssessmentService = Depends(get_risk_assessment_service),
):
    return format_response(service._to_fhir(ra), service._to_plain(ra), request)


@router.patch(
    "/{risk_assessment_id}",
    operation_id="patch_risk_assessment",
    summary="Partially update a RiskAssessment resource",
    description=(
        "Patchable fields: `status` (cannot be null), `method_*`, `code_*`, `subject` (Patient/Group, cannot be null), "
        "`encounter_id`, `occurrence_datetime` / `occurrence_period_*`, `mitigation`, and the references `based_on`, "
        "`parent`, `condition`, `performer` (as `Type/id`; null clears) with their `*_display`. "
        "Child lists (identifier, reason_code, reason_reference, basis, prediction, note) are also patchable with "
        "REPLACE semantics: a list that is sent replaces the stored list in full, `[]` clears it, and an omitted "
        "list is left untouched (e.g. send a corrected `prediction` list together with `status: amended`). " + _CONTENT_NEG
    ),
    response_description="The updated RiskAssessment resource",
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_risk_assessment(
    payload: RiskAssessmentPatchSchema,
    request: Request,
    ra: RiskAssessmentModel = Depends(resolve_risk_assessment),
    service: RiskAssessmentService = Depends(get_risk_assessment_service),
):
    updated = await service.patch_risk_assessment(ra.risk_assessment_id, payload, payload.updated_by)
    if not updated:
        raise HTTPException(status_code=404, detail="RiskAssessment not found")
    return format_response(service._to_fhir(updated), service._to_plain(updated), request)


@router.get(
    "/",
    operation_id="list_risk_assessments",
    summary="Search RiskAssessment resources",
    description=(
        "Searches RiskAssessments using the FHIR R4 search parameters "
        "(https://www.hl7.org/fhir/R4/riskassessment.html#search). "
        "Token params (`status`, `identifier`, `method`, `risk`) accept `code`, `system|code`, `|code` or `system|`; "
        "comma = OR. Reference params (`patient`, `subject`, `encounter`, `condition`, `performer`) accept `Type/id` "
        "or a bare numeric id. `date` (occurrence) and `_lastUpdated` take an optional prefix "
        "eq|ne|gt|lt|ge|le|sa|eb|ap; `probability` is a number with an optional prefix (e.g. `ge20`) matched "
        "against prediction probabilities. Repeat `date` / `probability` / `_lastUpdated` for AND. "
        "`org_id` is mandatory on every search (tenant scope) and `user_id` is optional; paginate with `limit` / `offset`. " + _CONTENT_NEG
    ),
    response_description="Paginated RiskAssessment resources",
    responses={**_LIST_200, **_ERR_VALIDATION},
)
async def list_risk_assessments(
    request: Request,
    id_: Optional[str] = Query(None, alias="_id", description="Public risk_assessment_id(s), comma-separated."),
    identifier: Optional[str] = Query(None, description="Token `[system|]value` of RiskAssessment.identifier."),
    ra_status: Optional[str] = Query(
        None, alias="status",
        description="Token: registered|preliminary|final|amended|corrected|cancelled|entered-in-error|unknown (comma = OR).",
    ),
    method: Optional[str] = Query(None, description="Token `[system|]code` of RiskAssessment.method."),
    subject: Optional[str] = Query(None, description="Subject reference (Patient or Group), e.g. `Patient/10001`."),
    patient: Optional[str] = Query(None, description="Subject patient reference: `Patient/10001` or `10001`."),
    encounter: Optional[str] = Query(None, description="Encounter reference: `Encounter/20001` or `20001`."),
    condition: Optional[str] = Query(None, description="Condition reference: `Condition/120001` or `120001`."),
    performer: Optional[str] = Query(None, description="Performer reference: Practitioner|PractitionerRole|Device."),
    date: Optional[List[str]] = Query(None, description="Occurrence date with optional prefix, e.g. `ge2024-01-01`. Repeat for AND."),
    probability: Optional[List[str]] = Query(None, description="Prediction probability (number) with optional prefix, e.g. `ge20`. Repeat for AND."),
    risk: Optional[str] = Query(None, description="Token of prediction.qualitativeRisk, e.g. `high`."),
    last_updated: Optional[List[str]] = Query(None, alias="_lastUpdated", description="Last-updated instant with optional prefix."),
    user_id: Optional[str] = Query(None, description="Optional: restrict to records owned by this user."),
    org_id: str = Query(..., min_length=1, description="Tenant organization id — mandatory scope of every search."),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: RiskAssessmentService = Depends(get_risk_assessment_service),
):
    search = RiskAssessmentSearch(
        id=id_, identifier=identifier, ra_status=ra_status, method=method, subject=subject, patient=patient,
        encounter=encounter, condition=condition, performer=performer, date=date or [],
        probability=probability or [], risk=risk, last_updated=last_updated or [],
    )
    items, total = await service.list_risk_assessments(
        user_id=user_id, org_id=org_id, search=search, limit=limit, offset=offset,
    )
    return format_paginated_response(
        [service._to_fhir(i) for i in items],
        [service._to_plain(i) for i in items],
        total, limit, offset, request,
    )


@router.delete(
    "/{risk_assessment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_risk_assessment",
    summary="Delete a RiskAssessment resource",
    description=(
        "Permanently deletes the RiskAssessment and all its child records (identifier, reasonCode, reasonReference, "
        "basis, prediction, note). This operation is irreversible. Returns 204 No Content on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_risk_assessment(
    ra: RiskAssessmentModel = Depends(resolve_risk_assessment),
    service: RiskAssessmentService = Depends(get_risk_assessment_service),
):
    await service.delete_risk_assessment(ra.risk_assessment_id)
    return None
