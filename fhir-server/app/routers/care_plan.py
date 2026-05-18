from fastapi import APIRouter, Depends, Query, Request, status

from app.auth.care_plan_deps import resolve_care_plan
from app.auth.dependencies import require_permission
from app.core.content_negotiation import format_paginated_response, format_response
from app.core.schema_utils import inline_schema
from app.di.dependencies.care_plan import get_care_plan_service
from app.models.care_plan.care_plan import CarePlanModel
from app.schemas.care_plan.input import CarePlanCreateSchema, CarePlanPatchSchema
from app.schemas.care_plan.response import (
    FHIRCarePlanBundle,
    FHIRCarePlanSchema,
    PaginatedCarePlanResponse,
    PlainCarePlanResponse,
)
from app.services.care_plan_service import CarePlanService

router = APIRouter()

_CONTENT_NEG = (
    "Set `Accept: application/fhir+json` to receive the full FHIR R4 representation; "
    "omit or use `Accept: application/json` for the simplified plain-JSON form."
)

_ERR_AUTH = {
    401: {"description": "Not authenticated — Bearer token missing or expired"},
    403: {"description": "Forbidden — caller lacks the required permission"},
}
_ERR_NOT_FOUND = {404: {"description": "CarePlan not found"}}
_ERR_VALIDATION = {422: {"description": "Validation error"}}

_SINGLE_200 = {
    200: {
        "content": {
            "application/json": {"schema": inline_schema(PlainCarePlanResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRCarePlanSchema.model_json_schema())},
        }
    }
}
_SINGLE_201 = {201: _SINGLE_200[200]}
_LIST_200 = {
    200: {
        "description": "Paginated list of CarePlan resources",
        "content": {
            "application/json": {"schema": inline_schema(PaginatedCarePlanResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRCarePlanBundle.model_json_schema())},
        },
    }
}


# ── Create ───────────────────────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("care_plan", "create"))],
    operation_id="create_care_plan",
    summary="Create a new CarePlan resource",
    description=(
        "Creates a FHIR R4 CarePlan resource. "
        "Required: `status`, `intent`. "
        "Optional: all other CarePlan fields including child arrays (identifiers, basedOn, replaces, "
        "partOf, category, contributor, careTeam, addresses, supportingInfo, goal, activity, note). "
        + _CONTENT_NEG
    ),
    response_description="The newly created CarePlan resource",
    responses={**_SINGLE_201, **_ERR_AUTH, **_ERR_VALIDATION},
)
async def create_care_plan(
    payload: CarePlanCreateSchema,
    request: Request,
    care_plan_service: CarePlanService = Depends(get_care_plan_service),
):
    created_by: str = request.state.user.get("sub")
    care_plan = await care_plan_service.create_care_plan(payload, payload.user_id, payload.org_id, created_by)
    return format_response(
        care_plan_service._to_fhir(care_plan),
        care_plan_service._to_plain(care_plan),
        request,
    )


# ── Get /me ──────────────────────────────────────────────────────────────────


@router.get(
    "/me",
    dependencies=[Depends(require_permission("care_plan", "read"))],
    operation_id="list_my_care_plans",
    summary="List CarePlans for the authenticated user",
    description=(
        "Returns a paginated list of CarePlan resources owned by the authenticated user "
        "within their active organisation. " + _CONTENT_NEG
    ),
    responses={**_LIST_200, **_ERR_AUTH},
)
async def get_me_care_plans(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    care_plan_service: CarePlanService = Depends(get_care_plan_service),
):
    user_id: str = request.state.user.get("sub")
    org_id: str = request.state.user.get("activeOrganizationId")
    rows, total = await care_plan_service.get_me(user_id, org_id, limit, offset)
    return format_paginated_response(
        [care_plan_service._to_fhir(cp) for cp in rows],
        [care_plan_service._to_plain(cp) for cp in rows],
        total, limit, offset, request,
    )


# ── Get by ID ─────────────────────────────────────────────────────────────────


@router.get(
    "/{care_plan_id}",
    dependencies=[Depends(require_permission("care_plan", "read"))],
    operation_id="get_care_plan",
    summary="Retrieve a CarePlan by public identifier",
    description="Fetches a single CarePlan resource by its public `care_plan_id`. " + _CONTENT_NEG,
    responses={**_SINGLE_200, **_ERR_AUTH, **_ERR_NOT_FOUND},
)
async def get_care_plan(
    request: Request,
    care_plan: CarePlanModel = Depends(resolve_care_plan),
    care_plan_service: CarePlanService = Depends(get_care_plan_service),
):
    return format_response(
        care_plan_service._to_fhir(care_plan),
        care_plan_service._to_plain(care_plan),
        request,
    )


# ── Patch ─────────────────────────────────────────────────────────────────────


@router.patch(
    "/{care_plan_id}",
    dependencies=[Depends(require_permission("care_plan", "update"))],
    operation_id="patch_care_plan",
    summary="Partially update a CarePlan",
    description=(
        "Updates a CarePlan resource. Only supplied fields are changed. "
        "Child arrays (activities, notes, etc.) replace the existing list when included. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_AUTH, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_care_plan(
    payload: CarePlanPatchSchema,
    request: Request,
    care_plan: CarePlanModel = Depends(resolve_care_plan),
    care_plan_service: CarePlanService = Depends(get_care_plan_service),
):
    updated_by: str = request.state.user.get("sub")
    updated = await care_plan_service.patch_care_plan(care_plan.care_plan_id, payload, updated_by)
    return format_response(
        care_plan_service._to_fhir(updated),
        care_plan_service._to_plain(updated),
        request,
    )


# ── List ──────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    dependencies=[Depends(require_permission("care_plan", "read"))],
    operation_id="list_care_plans",
    summary="List all CarePlan resources",
    description=(
        "Returns a paginated list of all CarePlan resources accessible to the caller. "
        + _CONTENT_NEG
    ),
    responses={**_LIST_200, **_ERR_AUTH},
)
async def list_care_plans(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    care_plan_service: CarePlanService = Depends(get_care_plan_service),
):
    rows, total = await care_plan_service.list_care_plans(limit=limit, offset=offset)
    return format_paginated_response(
        [care_plan_service._to_fhir(cp) for cp in rows],
        [care_plan_service._to_plain(cp) for cp in rows],
        total, limit, offset, request,
    )


# ── Delete ────────────────────────────────────────────────────────────────────


@router.delete(
    "/{care_plan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("care_plan", "delete"))],
    operation_id="delete_care_plan",
    summary="Delete a CarePlan resource",
    description="Permanently deletes a CarePlan and all its related child records.",
    responses={**_ERR_AUTH, **_ERR_NOT_FOUND},
)
async def delete_care_plan(
    care_plan: CarePlanModel = Depends(resolve_care_plan),
    care_plan_service: CarePlanService = Depends(get_care_plan_service),
):
    await care_plan_service.delete_care_plan(care_plan.care_plan_id)
