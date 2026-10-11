"""
FastAPI router for RiskAssessment resources.

Endpoints:
  POST   /risk-assessments/        — record an assessment with predictions in the body
  GET    /risk-assessments/{id}    — fetch a single RiskAssessment by public ID
  GET    /risk-assessments/        — paginated FHIR R4 search (patient, condition, probability, risk, ...)
  PATCH  /risk-assessments/{id}    — partial update (scalar + reference fields only)
  DELETE /risk-assessments/{id}    — permanent delete (cascades to all child records)

All routes support content negotiation:
  - `Accept: application/json`      → plain snake_case JSON (default)
  - `Accept: application/fhir+json` → FHIR R4 resource / Bundle

RBAC is enforced via require_permission() for the ("risk_assessment", <action>) pair.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response, get_accept_header
from app.core.schema_utils import inline_schema
from app.di.dependencies.risk_assessment import get_risk_assessment_service
from app.schemas.risk_assessment.input import (
    ListRiskAssessmentsSchema,
    RiskAssessmentCreateSchema,
    RiskAssessmentPatchSchema,
)
from app.schemas.risk_assessment.response import (
    FhirBundleResponse,
    FhirRiskAssessmentResponse,
    PaginatedRiskAssessmentResponse,
    RiskAssessmentRecord,
)
from app.services.risk_assessment_service import RiskAssessmentService

# All routes are prefixed with /risk-assessments; tagged for Swagger grouping.
router = APIRouter(prefix="/risk-assessments", tags=["RiskAssessments"])

# ── Shared error response descriptors ────────────────────────────────────────

_ERR_NOT_FOUND = {404: {"description": "RiskAssessment not found"}}
_ERR_VALIDATION = {422: {"description": "Validation error — request body or query params failed validation"}}

# ── Shared success response descriptors ──────────────────────────────────────
# inline_schema() resolves Pydantic's $defs/$ref pointers so both content types
# render in Swagger UI without resolver errors.

_SINGLE_201 = {
    201: {
        "description": "RiskAssessment created successfully",
        "content": {
            "application/json": {"schema": inline_schema(RiskAssessmentRecord.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FhirRiskAssessmentResponse.model_json_schema())},
        },
    }
}

_SINGLE_200 = {
    200: {
        "description": "RiskAssessment retrieved or updated successfully",
        "content": {
            "application/json": {"schema": inline_schema(RiskAssessmentRecord.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FhirRiskAssessmentResponse.model_json_schema())},
        },
    }
}

_LIST_200 = {
    200: {
        "description": "Paginated list of RiskAssessment resources",
        "content": {
            "application/json": {"schema": inline_schema(PaginatedRiskAssessmentResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FhirBundleResponse.model_json_schema())},
        },
    }
}


# ── POST /risk-assessments/ ──────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_risk_assessment",
    summary="Create a RiskAssessment",
    description=(
        "Records an assessment of the likely outcome(s) for a patient or group. `status` and `subject` are required. "
        "Provide `subject` as `'Patient/10001'` (or `Group/<id>`); optionally link an Encounter via `encounter_id`, "
        "a `condition`, and a `performer` (Practitioner|PractitionerRole|Device). Supply `occurrence_datetime` OR "
        "`occurrence_period_*`. Each `prediction` carries an outcome, a probability (`probability_decimal` ≤ 100, or "
        "`probability_range_*` in %), an optional `qualitative_risk`, `relative_risk`, `when_period_*` or "
        "`when_range_*`, and a `rationale`. All child arrays (identifier, reason_code, reason_reference, basis, "
        "prediction, note) are submitted in the single request body. References are `Type/id` strings — only their "
        "format is validated. Send `Accept: application/fhir+json` to receive the result in FHIR R4 format."
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
    dependencies=[Depends(require_permission("risk_assessment", "create"))],
)
async def create_risk_assessment(
    dto: RiskAssessmentCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("risk_assessment", "create")),
    service: RiskAssessmentService = Depends(get_risk_assessment_service),
) -> JSONResponse:
    """Record a new RiskAssessment and return the persisted record."""
    data = await service.create(dto, actor, accept=get_accept_header(request))
    return format_response(data, request)


# ── GET /risk-assessments/{resource_id} ──────────────────────────────────────


@router.get(
    "/{resource_id}",
    operation_id="get_risk_assessment",
    summary="Get a RiskAssessment by ID",
    description=(
        "Fetch a single RiskAssessment (including predictions, basis and notes) by its public integer ID. "
        "Send `Accept: application/fhir+json` for FHIR R4 format."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
    dependencies=[Depends(require_permission("risk_assessment", "read"))],
)
async def get_risk_assessment(
    resource_id: int,
    request: Request,
    actor: AuthUser = Depends(require_permission("risk_assessment", "read")),
    service: RiskAssessmentService = Depends(get_risk_assessment_service),
) -> JSONResponse:
    """Fetch a single RiskAssessment by its public ID."""
    data = await service.get_by_id(resource_id, actor, accept=get_accept_header(request))
    return format_response(data, request)


# ── GET /risk-assessments/ ───────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_risk_assessments",
    summary="Search RiskAssessments",
    description=(
        "Searches RiskAssessments using the FHIR R4 search parameters "
        "(https://www.hl7.org/fhir/R4/riskassessment.html#search). "
        "Token params (`status`, `identifier`, `method`, `risk`) accept `code`, `system|code`, `|code` or `system|`; "
        "comma = OR. Reference params (`patient`, `subject`, `encounter`, `condition`, `performer`) accept `Type/id` "
        "or a bare numeric id. `date` (occurrence) and `_lastUpdated` take an optional prefix "
        "eq|ne|gt|lt|ge|le|sa|eb|ap; `probability` is a number with an optional prefix (e.g. `ge20`) matched "
        "against prediction probabilities. Repeat `date` / `probability` / `_lastUpdated` for AND. "
        "`org_id` is mandatory on every search (tenant scope) and `user_id` is optional; paginate with `limit` / `offset`. "
        "Send `Accept: application/fhir+json` to receive a FHIR Bundle searchset."
    ),
    responses={**_LIST_200, **_ERR_VALIDATION},
    dependencies=[Depends(require_permission("risk_assessment", "read"))],
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
    user_id: Optional[str] = Query(None, description="Optional: restrict to records owned by this user (JWT subject)."),
    org_id: str = Query(..., min_length=1, description="Tenant organization ID — mandatory scope of every search."),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    actor: AuthUser = Depends(require_permission("risk_assessment", "read")),
    service: RiskAssessmentService = Depends(get_risk_assessment_service),
) -> JSONResponse:
    """
    Search RiskAssessments with FHIR R4 search parameters.

    Parameters are declared explicitly (with aliases) because `_id` and
    `_lastUpdated` are not valid Python identifiers. They are gathered into
    ListRiskAssessmentsSchema, whose validators (e.g. the status code check) run
    here; a failure is surfaced as a 422, not a 500.
    """
    try:
        filters = ListRiskAssessmentsSchema(
            id=id_, identifier=identifier, status=ra_status, method=method, subject=subject,
            patient=patient, encounter=encounter, condition=condition, performer=performer,
            date=date, probability=probability, risk=risk, last_updated=last_updated,
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


# ── PATCH /risk-assessments/{resource_id} ────────────────────────────────────


@router.patch(
    "/{resource_id}",
    operation_id="update_risk_assessment",
    summary="Partially update a RiskAssessment",
    description=(
        "Update scalar and reference fields on a RiskAssessment. At least one field must be provided. "
        "Patchable fields: `status`, `method_*`, `code_*`, `subject` (Patient/Group), `encounter_id`, "
        "`occurrence_datetime` / `occurrence_period_*`, `mitigation`, and the references `based_on`, `parent`, "
        "`condition`, `performer` (as `Type/id`) with their `*_display`. "
        "Child lists (identifier, reason_code, reason_reference, basis, prediction, note) are also patchable with "
        "REPLACE semantics: a list that is sent replaces the stored list in full, `[]` clears it, and an omitted "
        "list is left untouched (e.g. a corrected `prediction` list together with `status: amended`). "
        "Send `Accept: application/fhir+json` for FHIR R4 format."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
    dependencies=[Depends(require_permission("risk_assessment", "update"))],
)
async def update_risk_assessment(
    resource_id: int,
    dto: RiskAssessmentPatchSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("risk_assessment", "update")),
    service: RiskAssessmentService = Depends(get_risk_assessment_service),
) -> JSONResponse:
    """Partially update a RiskAssessment. Returns 422 if the body is empty."""
    data = await service.update(resource_id, dto, actor, accept=get_accept_header(request))
    return format_response(data, request)


# ── DELETE /risk-assessments/{resource_id} ───────────────────────────────────


@router.delete(
    "/{resource_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_risk_assessment",
    summary="Delete a RiskAssessment",
    description=(
        "Permanently deletes the RiskAssessment and all its child records (identifier, reasonCode, reasonReference, "
        "basis, prediction, note). This operation is irreversible. Returns 204 No Content on success."
    ),
    responses={**_ERR_NOT_FOUND},
    dependencies=[Depends(require_permission("risk_assessment", "delete"))],
)
async def delete_risk_assessment(
    resource_id: int,
    actor: AuthUser = Depends(require_permission("risk_assessment", "delete")),
    service: RiskAssessmentService = Depends(get_risk_assessment_service),
) -> None:
    """Permanently delete a RiskAssessment and cascade to all child records."""
    await service.delete(resource_id, actor)
