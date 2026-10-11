from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.deps.questionnaire_response_deps import resolve_questionnaire_response
from app.core.content_negotiation import format_response, format_paginated_response
from app.core.schema_utils import inline_schema
from app.di.dependencies.questionnaire_response import get_questionnaire_response_service
from app.models.questionnaire_response.questionnaire_response import QuestionnaireResponseModel
from app.repository.questionnaire_response_repository import QRSearch
from app.schemas.fhir import (
    FHIRQuestionnaireResponseSchema,
    FHIRQuestionnaireResponseBundle,
    PaginatedQuestionnaireResponseResponse,
    PlainQuestionnaireResponse,
)
from app.schemas.questionnaire_response import (
    QuestionnaireResponseCreateSchema,
    QuestionnaireResponsePatchSchema,
)
from app.services.questionnaire_response_service import QuestionnaireResponseService

router = APIRouter()

_CONTENT_NEG = (
    "Set `Accept: application/fhir+json` to receive the full FHIR R4 representation; "
    "omit or use `Accept: application/json` for the simplified plain-JSON form."
)

_ERR_NOT_FOUND = {404: {"description": "QuestionnaireResponse not found"}}
_ERR_VALIDATION = {422: {"description": "Validation error — request body failed schema validation"}}

# Pre-computed inline schemas (evaluated once at import time)
_SINGLE_200 = {
    200: {
        "content": {
            "application/json": {"schema": inline_schema(PlainQuestionnaireResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRQuestionnaireResponseSchema.model_json_schema())},
        }
    }
}
_SINGLE_201 = {201: _SINGLE_200[200]}
_LIST_200 = {
    200: {
        "description": "Paginated list of questionnaire responses",
        "content": {
            "application/json": {"schema": inline_schema(PaginatedQuestionnaireResponseResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRQuestionnaireResponseBundle.model_json_schema())},
        },
    }
}


# ── Create QuestionnaireResponse ───────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_questionnaire_response",
    summary="Create a new QuestionnaireResponse resource",
    description=(
        "Records a completed set of answers to a Questionnaire (FHIR R4 QuestionnaireResponse). "
        "Supports nested item groups, repeating items, and all FHIR R4 answer value types "
        "(string, integer, decimal, boolean, date, dateTime, time, url, Coding, Quantity, Attachment, Reference). "
        "Link to source context using public IDs: `Patient/10001`, `Encounter/20001`, `Practitioner/30001`. "
        "The `questionnaire` field should be a canonical URL or resource reference identifying the Questionnaire being answered. "
        "The caller's `sub` and `activeOrganizationId` JWT claims are automatically bound to the record. "
        + _CONTENT_NEG
    ),
    response_description="The newly created QuestionnaireResponse resource",
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_questionnaire_response(
    payload: QuestionnaireResponseCreateSchema,
    request: Request,
    qr_service: QuestionnaireResponseService = Depends(get_questionnaire_response_service),
):
    created_by = payload.created_by
    qr = await qr_service.create_questionnaire_response(payload, payload.user_id, payload.org_id, created_by)
    return format_response(
        qr_service._to_fhir(qr),
        qr_service._to_plain(qr),
        request,
    )


@router.get(
    "/{questionnaire_response_id}",
    operation_id="get_questionnaire_response_by_id",
    summary="Retrieve a QuestionnaireResponse resource by public questionnaire_response_id",
    description=(
        "Fetches a single QuestionnaireResponse by its public integer `questionnaire_response_id`. "
        + _CONTENT_NEG
    ),
    response_description="The requested QuestionnaireResponse resource",
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_questionnaire_response(
    request: Request,
    qr: QuestionnaireResponseModel = Depends(resolve_questionnaire_response),
    qr_service: QuestionnaireResponseService = Depends(get_questionnaire_response_service),
):
    return format_response(
        qr_service._to_fhir(qr),
        qr_service._to_plain(qr),
        request,
    )


# ── Patch QuestionnaireResponse ────────────────────────────────────────────


@router.patch(
    "/{questionnaire_response_id}",
    operation_id="patch_questionnaire_response",
    summary="Partially update a QuestionnaireResponse resource",
    description=(
        "Patchable fields: `status` (cannot be null), `questionnaire`, `authored`, and the references `subject`, "
        "`encounter`, `author`, `source` (as `Type/id`; null clears) with their `*_display`. "
        "The child lists `based_on`, `part_of` and the item/answer tree `item` are also patchable with REPLACE "
        "semantics: a list that is sent replaces the stored list in full, `[]` clears it, an omitted list is left "
        "untouched. To correct answers send the corrected `item` tree (and typically `status: amended`). "
        + _CONTENT_NEG
    ),
    response_description="The updated QuestionnaireResponse resource",
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_questionnaire_response(
    payload: QuestionnaireResponsePatchSchema,
    request: Request,
    qr: QuestionnaireResponseModel = Depends(resolve_questionnaire_response),
    qr_service: QuestionnaireResponseService = Depends(get_questionnaire_response_service),
):
    updated_by = payload.updated_by
    updated = await qr_service.patch_questionnaire_response(
        qr.questionnaire_response_id, payload, updated_by
    )
    if not updated:
        raise HTTPException(status_code=404, detail="QuestionnaireResponse not found")
    return format_response(
        qr_service._to_fhir(updated),
        qr_service._to_plain(updated),
        request,
    )


# ── List QuestionnaireResponses ────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_questionnaire_responses",
    summary="Search QuestionnaireResponse resources",
    description=(
        "Searches QuestionnaireResponses using the FHIR R4 search parameters "
        "(https://www.hl7.org/fhir/R4/questionnaireresponse.html#search). "
        "Token params (`status`, `identifier`) accept `code`, `system|code`, `|code` or `system|`; comma = OR. "
        "Reference params (`subject`, `patient`, `encounter`, `author`, `source`, `based-on`, `part-of`) accept "
        "`Type/id` or a bare numeric id. `questionnaire` matches the stored canonical URL or `Questionnaire/<id>`. "
        "Date params (`authored`, `_lastUpdated`) take an optional prefix eq|ne|gt|lt|ge|le|sa|eb|ap; repeat for AND "
        "(e.g. `authored=ge2024-01-01&authored=lt2024-02-01`). "
        "`org_id` is mandatory on every search (tenant scope) and `user_id` is optional; paginate with `limit` / `offset`. "
        + _CONTENT_NEG
    ),
    response_description="Paginated QuestionnaireResponse resources",
    responses={**_LIST_200, **_ERR_VALIDATION},
)
async def list_questionnaire_responses(
    request: Request,
    id_: Optional[str] = Query(None, alias="_id", description="Public questionnaire_response_id(s), comma-separated."),
    identifier: Optional[str] = Query(None, description="Token `[system|]value` of QuestionnaireResponse.identifier."),
    questionnaire: Optional[str] = Query(None, description="Canonical URL, or `Questionnaire/<id>`, of the answered Questionnaire."),
    qr_status: Optional[str] = Query(
        None, alias="status",
        description="Token: in-progress|completed|amended|entered-in-error|stopped (comma = OR).",
    ),
    subject: Optional[str] = Query(None, description="Subject reference (any type), e.g. `Patient/10001`."),
    patient: Optional[str] = Query(None, description="Subject patient reference: `Patient/10001` or `10001`."),
    encounter: Optional[str] = Query(None, description="Encounter reference: `Encounter/20001` or `20001`."),
    author: Optional[str] = Query(None, description="Author reference: Device|Practitioner|PractitionerRole|Patient|RelatedPerson|Organization."),
    source: Optional[str] = Query(None, description="Source reference: Patient|Practitioner|PractitionerRole|RelatedPerson."),
    based_on: Optional[str] = Query(None, alias="based-on", description="basedOn reference: CarePlan|ServiceRequest."),
    part_of: Optional[str] = Query(None, alias="part-of", description="partOf reference: Observation|Procedure."),
    authored: Optional[List[str]] = Query(None, description="Authored date with optional prefix, e.g. `ge2024-01-01`. Repeat for AND."),
    last_updated: Optional[List[str]] = Query(None, alias="_lastUpdated", description="Last-updated instant with optional prefix. Repeat for AND."),
    patient_id: Optional[int] = Query(None, description="Legacy: public patient_id. Same as `patient`."),
    authored_from: Optional[datetime] = Query(None, description="Legacy: authored >= this value."),
    authored_to: Optional[datetime] = Query(None, description="Legacy: authored <= this value."),
    user_id: Optional[str] = Query(None, description="Optional: restrict to records owned by this user."),
    org_id: str = Query(..., min_length=1, description="Tenant organization id — mandatory scope of every search."),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    qr_service: QuestionnaireResponseService = Depends(get_questionnaire_response_service),
):
    search = QRSearch(
        id=id_, identifier=identifier, questionnaire=questionnaire, q_status=qr_status,
        subject=subject,
        patient=patient or (str(patient_id) if patient_id is not None else None),
        encounter=encounter, author=author, source=source, based_on=based_on, part_of=part_of,
        authored=authored or [], last_updated=last_updated or [],
        authored_from=authored_from, authored_to=authored_to,
    )
    responses, total = await qr_service.list_questionnaire_responses(
        user_id=user_id, org_id=org_id, search=search, limit=limit, offset=offset,
    )
    return format_paginated_response(
        [qr_service._to_fhir(qr) for qr in responses],
        [qr_service._to_plain(qr) for qr in responses],
        total, limit, offset, request,
    )


# ── Delete QuestionnaireResponse ───────────────────────────────────────────


@router.delete(
    "/{questionnaire_response_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_questionnaire_response",
    summary="Delete a QuestionnaireResponse resource",
    description=(
        "Permanently deletes the QuestionnaireResponse and all its nested item/answer records. "
        "This operation is irreversible. Returns 204 No Content on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_questionnaire_response(
    qr: QuestionnaireResponseModel = Depends(resolve_questionnaire_response),
    qr_service: QuestionnaireResponseService = Depends(get_questionnaire_response_service),
):
    await qr_service.delete_questionnaire_response(qr.questionnaire_response_id)
    return None
