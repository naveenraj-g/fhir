from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.auth.medication_request_deps import get_authorized_medication_request
from app.auth.dependencies import require_permission
from app.core.content_negotiation import format_response, format_paginated_response
from app.core.schema_utils import inline_schema
from app.di.dependencies.medication_request import get_medication_request_service
from app.models.medication_request.medication_request import MedicationRequestModel
from app.schemas.medication_request import MedicationRequestCreateSchema, MedicationRequestPatchSchema
from app.schemas.medication_request.response import (
    FHIRMedicationRequestSchema,
    FHIRMedicationRequestBundle,
    PaginatedMedicationRequestResponse,
    PlainMedicationRequestResponse,
)
from app.services.medication_request_service import MedicationRequestService

router = APIRouter()

_CONTENT_NEG = (
    "Set `Accept: application/fhir+json` to receive the full FHIR R4 representation; "
    "omit or use `Accept: application/json` for the simplified plain-JSON form."
)

_ERR_AUTH = {
    401: {"description": "Not authenticated — Bearer token missing or expired"},
    403: {"description": "Forbidden — caller lacks the required permission"},
}
_ERR_NOT_FOUND = {404: {"description": "MedicationRequest not found"}}
_ERR_VALIDATION = {422: {"description": "Validation error — request body failed schema validation"}}

_SINGLE_200 = {
    200: {
        "content": {
            "application/json": {"schema": inline_schema(PlainMedicationRequestResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRMedicationRequestSchema.model_json_schema())},
        }
    }
}
_SINGLE_201 = {201: _SINGLE_200[200]}
_LIST_200 = {
    200: {
        "description": "Paginated list of medication requests",
        "content": {
            "application/json": {"schema": inline_schema(PaginatedMedicationRequestResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRMedicationRequestBundle.model_json_schema())},
        },
    }
}


# ── Create MedicationRequest ───────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("medication_request", "create"))],
    operation_id="create_medication_request",
    summary="Create a new MedicationRequest resource",
    description=(
        "Records an order or request for medication for a patient. "
        "Provide `subject` as a FHIR reference string e.g. `'Patient/10001'`. "
        "Optionally link to an Encounter via `encounter_id` (public encounter_id). "
        "Both `status` and `intent` are required. "
        "Specify medication via `medication_code_*` (CodeableConcept) or `medication_reference` (Reference). "
        + _CONTENT_NEG
    ),
    response_description="The newly created MedicationRequest resource",
    responses={**_SINGLE_201, **_ERR_AUTH, **_ERR_VALIDATION},
)
async def create_medication_request(
    payload: MedicationRequestCreateSchema,
    request: Request,
    mr_service: MedicationRequestService = Depends(get_medication_request_service),
):
    created_by: str = request.state.user.get("sub")
    mr = await mr_service.create_medication_request(
        payload, payload.user_id, payload.org_id, created_by
    )
    return format_response(
        mr_service._to_fhir(mr),
        mr_service._to_plain(mr),
        request,
    )


# ── Get own MedicationRequests (/me) ──────────────────────────────────────────
# Declared before /{medication_request_id} to avoid routing conflicts.


@router.get(
    "/me",
    dependencies=[Depends(require_permission("medication_request", "read"))],
    operation_id="get_my_medication_requests",
    summary="List MedicationRequest resources for the currently authenticated user",
    description=(
        "Returns a paginated list of MedicationRequest records belonging to the authenticated user "
        "(identified by `sub` and `activeOrganizationId`). "
        "Filter by `status`, `patient_id`, `authored_from`, or `authored_to`. "
        + _CONTENT_NEG
    ),
    response_description="Paginated MedicationRequest resources for the current user",
    responses={**_LIST_200, **_ERR_AUTH},
)
async def get_my_medication_requests(
    request: Request,
    mr_status: Optional[str] = Query(None, alias="status", description="Filter by status e.g. 'active'."),
    patient_id: Optional[int] = Query(None, description="Filter by patient subject_id."),
    authored_from: Optional[datetime] = Query(None),
    authored_to: Optional[datetime] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    mr_service: MedicationRequestService = Depends(get_medication_request_service),
):
    user_id: str = request.state.user.get("sub")
    org_id: str = request.state.user.get("activeOrganizationId")
    items, total = await mr_service.get_me(
        user_id, org_id,
        mr_status=mr_status,
        patient_id=patient_id,
        authored_from=authored_from,
        authored_to=authored_to,
        limit=limit,
        offset=offset,
    )
    return format_paginated_response(
        [mr_service._to_fhir(mr) for mr in items],
        [mr_service._to_plain(mr) for mr in items],
        total, limit, offset, request,
    )


# ── Get MedicationRequest by public medication_request_id ─────────────────────


@router.get(
    "/{medication_request_id}",
    dependencies=[Depends(require_permission("medication_request", "read"))],
    operation_id="get_medication_request_by_id",
    summary="Retrieve a MedicationRequest resource by public medication_request_id",
    description=(
        "Fetches a single MedicationRequest by its public integer `medication_request_id`. "
        + _CONTENT_NEG
    ),
    response_description="The requested MedicationRequest resource",
    responses={**_SINGLE_200, **_ERR_AUTH, **_ERR_NOT_FOUND},
)
async def get_medication_request(
    request: Request,
    mr: MedicationRequestModel = Depends(get_authorized_medication_request),
    mr_service: MedicationRequestService = Depends(get_medication_request_service),
):
    return format_response(
        mr_service._to_fhir(mr),
        mr_service._to_plain(mr),
        request,
    )


# ── Patch MedicationRequest ────────────────────────────────────────────────────


@router.patch(
    "/{medication_request_id}",
    dependencies=[Depends(require_permission("medication_request", "update"))],
    operation_id="patch_medication_request",
    summary="Partially update a MedicationRequest resource",
    description=(
        "Patchable fields: `status`, `intent`, `priority`, `do_not_perform`, `status_reason_*`, "
        "`medication_code_*`, `subject_display`, `encounter_display`, `authored_on`, "
        "`reported_boolean`, `reported_reference_display`, `requester_display`, `performer_display`, "
        "`performer_type_*`, `recorder_display`, `course_of_therapy_type_*`, "
        "`dispense_number_of_repeats_allowed`, `dispense_validity_period_*`, `dispense_quantity_*`, "
        "`substitution_allowed_boolean`, `substitution_reason_*`, `instantiates_canonical`, `instantiates_uri`. "
        "Child arrays (identifier, category, supportingInformation, reasonCode, reasonReference, basedOn, "
        "insurance, note, dosageInstruction, detectedIssue, eventHistory) cannot be changed via PATCH — "
        "delete and re-create the MedicationRequest to correct those. "
        + _CONTENT_NEG
    ),
    response_description="The updated MedicationRequest resource",
    responses={**_SINGLE_200, **_ERR_AUTH, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_medication_request(
    payload: MedicationRequestPatchSchema,
    request: Request,
    mr: MedicationRequestModel = Depends(get_authorized_medication_request),
    mr_service: MedicationRequestService = Depends(get_medication_request_service),
):
    updated_by: str = request.state.user.get("sub")
    updated = await mr_service.patch_medication_request(
        mr.medication_request_id, payload, updated_by
    )
    if not updated:
        raise HTTPException(status_code=404, detail="MedicationRequest not found")
    return format_response(
        mr_service._to_fhir(updated),
        mr_service._to_plain(updated),
        request,
    )


# ── List MedicationRequests ────────────────────────────────────────────────────


@router.get(
    "/",
    dependencies=[Depends(require_permission("medication_request", "read"))],
    operation_id="list_medication_requests",
    summary="List all MedicationRequest resources",
    description=(
        "Returns a paginated list of MedicationRequest resources. "
        "Filter by `status`, `patient_id`, `authored_from`, `authored_to`, `user_id`, or `org_id`. "
        "Use `limit` and `offset` for pagination. "
        + _CONTENT_NEG
    ),
    response_description="Paginated MedicationRequest resources",
    responses={**_LIST_200, **_ERR_AUTH},
)
async def list_medication_requests(
    request: Request,
    mr_status: Optional[str] = Query(None, alias="status", description="Filter by status e.g. 'active'."),
    patient_id: Optional[int] = Query(None, description="Filter by patient subject_id."),
    authored_from: Optional[datetime] = Query(None),
    authored_to: Optional[datetime] = Query(None),
    user_id: Optional[str] = Query(None),
    org_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    mr_service: MedicationRequestService = Depends(get_medication_request_service),
):
    items, total = await mr_service.list_medication_requests(
        user_id=user_id,
        org_id=org_id,
        mr_status=mr_status,
        patient_id=patient_id,
        authored_from=authored_from,
        authored_to=authored_to,
        limit=limit,
        offset=offset,
    )
    return format_paginated_response(
        [mr_service._to_fhir(mr) for mr in items],
        [mr_service._to_plain(mr) for mr in items],
        total, limit, offset, request,
    )


# ── Delete MedicationRequest ───────────────────────────────────────────────────


@router.delete(
    "/{medication_request_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("medication_request", "delete"))],
    operation_id="delete_medication_request",
    summary="Delete a MedicationRequest resource",
    description=(
        "Permanently deletes the MedicationRequest and all its associated child records "
        "(identifier, category, supportingInformation, reasonCode, reasonReference, basedOn, "
        "insurance, note, dosageInstruction, detectedIssue, eventHistory). "
        "This operation is irreversible. Returns 204 No Content on success."
    ),
    responses={**_ERR_AUTH, **_ERR_NOT_FOUND},
)
async def delete_medication_request(
    mr: MedicationRequestModel = Depends(get_authorized_medication_request),
    mr_service: MedicationRequestService = Depends(get_medication_request_service),
):
    await mr_service.delete_medication_request(mr.medication_request_id)
    return None
