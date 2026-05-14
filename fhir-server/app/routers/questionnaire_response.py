from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth.dependencies import require_permission
from app.auth.questionnaire_response_deps import get_authorized_questionnaire_response
from app.core.content_negotiation import format_response, format_list_response
from app.di.dependencies.questionnaire_response import (
    get_questionnaire_response_service,
)
from app.models.questionnaire_response.questionnaire_response import (
    QuestionnaireResponseModel,
)
from app.schemas.questionnaire_response import (
    QuestionnaireResponseCreateSchema,
    QuestionnaireResponsePatchSchema,
    QuestionnaireResponseResponseSchema,
)
from app.services.questionnaire_response_service import QuestionnaireResponseService

router = APIRouter()

_CONTENT_NEG = (
    "Set `Accept: application/fhir+json` to receive the full FHIR R4 representation; "
    "omit or use `Accept: application/json` for the simplified plain-JSON form."
)

_ERR_AUTH = {
    401: {"description": "Not authenticated — Bearer token missing or expired"},
    403: {"description": "Forbidden — caller lacks the required permission"},
}
_ERR_NOT_FOUND = {404: {"description": "QuestionnaireResponse not found"}}
_ERR_VALIDATION = {422: {"description": "Validation error — request body failed schema validation"}}


# ── Create QuestionnaireResponse ───────────────────────────────────────────


@router.post(
    "/",
    response_model=QuestionnaireResponseResponseSchema,
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("questionnaire_response", "create"))],
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
    responses={**_ERR_AUTH, **_ERR_VALIDATION},
)
async def create_questionnaire_response(
    payload: QuestionnaireResponseCreateSchema,
    request: Request,
    qr_service: QuestionnaireResponseService = Depends(
        get_questionnaire_response_service
    ),
):
    created_by: str = request.state.user.get("sub")
    qr = await qr_service.create_questionnaire_response(payload, payload.user_id, payload.org_id, created_by)
    return format_response(
        qr_service._to_fhir(qr),
        qr_service._to_plain(qr),
        request,
    )


# ── Get own QuestionnaireResponses (/me) ───────────────────────────────────
# Declared before /{questionnaire_response_id} to avoid routing conflicts.


@router.get(
    "/me",
    response_model=list[QuestionnaireResponseResponseSchema],
    response_model_exclude_none=True,
    dependencies=[Depends(require_permission("questionnaire_response", "read"))],
    operation_id="get_my_questionnaire_responses",
    summary="List all QuestionnaireResponse resources for the currently authenticated user",
    description=(
        "Returns all QuestionnaireResponse records authored by or linked to the authenticated user's "
        "`sub` claim and `activeOrganizationId`. "
        + _CONTENT_NEG
    ),
    response_description="Array of QuestionnaireResponse resources for the current user",
    responses={**_ERR_AUTH},
)
async def get_my_questionnaire_responses(
    request: Request,
    qr_service: QuestionnaireResponseService = Depends(
        get_questionnaire_response_service
    ),
):
    user_id: str = request.state.user.get("sub")
    org_id: str = request.state.user.get("activeOrganizationId")
    responses = await qr_service.get_me(user_id, org_id)
    return format_list_response(
        [qr_service._to_fhir(qr) for qr in responses],
        [qr_service._to_plain(qr) for qr in responses],
        request,
    )


# ── Get QuestionnaireResponse by public id ─────────────────────────────────


@router.get(
    "/{questionnaire_response_id}",
    response_model=QuestionnaireResponseResponseSchema,
    response_model_exclude_none=True,
    dependencies=[Depends(require_permission("questionnaire_response", "read"))],
    operation_id="get_questionnaire_response_by_id",
    summary="Retrieve a QuestionnaireResponse resource by public questionnaire_response_id",
    description=(
        "Fetches a single QuestionnaireResponse by its public integer `questionnaire_response_id`. "
        "Access is subject to organization-scoped authorization. "
        + _CONTENT_NEG
    ),
    response_description="The requested QuestionnaireResponse resource",
    responses={
        **_ERR_AUTH,
        403: {"description": "Forbidden — caller lacks `questionnaire_response:read` permission or the resource belongs to a different organization"},
        **_ERR_NOT_FOUND,
    },
)
async def get_questionnaire_response(
    request: Request,
    qr: QuestionnaireResponseModel = Depends(get_authorized_questionnaire_response),
    qr_service: QuestionnaireResponseService = Depends(
        get_questionnaire_response_service
    ),
):
    return format_response(
        qr_service._to_fhir(qr),
        qr_service._to_plain(qr),
        request,
    )


# ── Patch QuestionnaireResponse ────────────────────────────────────────────


@router.patch(
    "/{questionnaire_response_id}",
    response_model=QuestionnaireResponseResponseSchema,
    response_model_exclude_none=True,
    dependencies=[Depends(require_permission("questionnaire_response", "update"))],
    operation_id="patch_questionnaire_response",
    summary="Partially update a QuestionnaireResponse resource",
    description=(
        "Only lifecycle fields are patchable: `status` (e.g. `in-progress` → `completed`), `authored`. "
        "To correct or replace item answers, delete and re-create the QuestionnaireResponse. "
        + _CONTENT_NEG
    ),
    response_description="The updated QuestionnaireResponse resource",
    responses={**_ERR_AUTH, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_questionnaire_response(
    payload: QuestionnaireResponsePatchSchema,
    request: Request,
    qr: QuestionnaireResponseModel = Depends(get_authorized_questionnaire_response),
    qr_service: QuestionnaireResponseService = Depends(
        get_questionnaire_response_service
    ),
):
    updated_by: str = request.state.user.get("sub")
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
    response_model=list[QuestionnaireResponseResponseSchema],
    response_model_exclude_none=True,
    dependencies=[Depends(require_permission("questionnaire_response", "read"))],
    operation_id="list_questionnaire_responses",
    summary="List all QuestionnaireResponse resources",
    description=(
        "Returns all QuestionnaireResponse resources accessible to the caller. "
        "Optionally filter by `?patient_id={patient_id}` or `?encounter_id={encounter_id}` (public integer IDs). "
        "Results are scoped to the caller's active organization. "
        + _CONTENT_NEG
    ),
    response_description="Array of QuestionnaireResponse resources",
    responses={**_ERR_AUTH},
)
async def list_questionnaire_responses(
    request: Request,
    patient_id: Optional[int] = None,
    encounter_id: Optional[int] = None,
    qr_service: QuestionnaireResponseService = Depends(
        get_questionnaire_response_service
    ),
):
    responses = await qr_service.list_questionnaire_responses(
        patient_id=patient_id, encounter_id=encounter_id
    )
    return format_list_response(
        [qr_service._to_fhir(qr) for qr in responses],
        [qr_service._to_plain(qr) for qr in responses],
        request,
    )


# ── Delete QuestionnaireResponse ───────────────────────────────────────────


@router.delete(
    "/{questionnaire_response_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("questionnaire_response", "delete"))],
    operation_id="delete_questionnaire_response",
    summary="Delete a QuestionnaireResponse resource",
    description=(
        "Permanently deletes the QuestionnaireResponse and all its nested item/answer records. "
        "This operation is irreversible. Returns 204 No Content on success."
    ),
    responses={**_ERR_AUTH, **_ERR_NOT_FOUND},
)
async def delete_questionnaire_response(
    qr: QuestionnaireResponseModel = Depends(get_authorized_questionnaire_response),
    qr_service: QuestionnaireResponseService = Depends(
        get_questionnaire_response_service
    ),
):
    await qr_service.delete_questionnaire_response(qr.questionnaire_response_id)
    return None
