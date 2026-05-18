from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.auth.practitioner_role_deps import resolve_practitioner_role
from app.auth.dependencies import require_permission
from app.core.content_negotiation import format_response, format_paginated_response
from app.core.schema_utils import inline_schema
from app.di.dependencies.practitioner_role import get_practitioner_role_service
from app.models.practitioner_role.practitioner_role import PractitionerRoleModel
from app.schemas.practitioner_role import PractitionerRoleCreateSchema, PractitionerRolePatchSchema
from app.schemas.practitioner_role.response import (
    FHIRPractitionerRoleSchema,
    FHIRPractitionerRoleBundle,
    PaginatedPractitionerRoleResponse,
    PlainPractitionerRoleResponse,
)
from app.services.practitioner_role_service import PractitionerRoleService

router = APIRouter()

_CONTENT_NEG = (
    "Set `Accept: application/fhir+json` to receive the full FHIR R4 representation; "
    "omit or use `Accept: application/json` for the simplified plain-JSON form."
)

_ERR_AUTH = {
    401: {"description": "Not authenticated — Bearer token missing or expired"},
    403: {"description": "Forbidden — caller lacks the required permission"},
}
_ERR_NOT_FOUND = {404: {"description": "PractitionerRole not found"}}
_ERR_VALIDATION = {422: {"description": "Validation error — request body failed schema validation"}}

_SINGLE_200 = {
    200: {
        "content": {
            "application/json": {"schema": inline_schema(PlainPractitionerRoleResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRPractitionerRoleSchema.model_json_schema())},
        }
    }
}
_SINGLE_201 = {201: _SINGLE_200[200]}
_LIST_200 = {
    200: {
        "description": "Paginated list of practitioner roles",
        "content": {
            "application/json": {"schema": inline_schema(PaginatedPractitionerRoleResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRPractitionerRoleBundle.model_json_schema())},
        },
    }
}


# ── Create PractitionerRole ────────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("practitioner_role", "create"))],
    operation_id="create_practitioner_role",
    summary="Create a new PractitionerRole resource",
    description=(
        "A specific set of roles/specialties/services a practitioner may perform at an organization. "
        "Optionally link to a `practitioner` (e.g. `'Practitioner/30001'`) and/or `organization`. "
        "Supply `code`, `specialty`, `location`, `healthcareService`, `contact`, `availability`, "
        "`endpoint`, `characteristic`, `communication`, and `identifier` arrays as needed. "
        + _CONTENT_NEG
    ),
    response_description="The newly created PractitionerRole resource",
    responses={**_SINGLE_201, **_ERR_AUTH, **_ERR_VALIDATION},
)
async def create_practitioner_role(
    payload: PractitionerRoleCreateSchema,
    request: Request,
    pr_service: PractitionerRoleService = Depends(get_practitioner_role_service),
):
    created_by: str = request.state.user.get("sub")
    pr = await pr_service.create_practitioner_role(
        payload, payload.user_id, payload.org_id, created_by
    )
    return format_response(
        pr_service._to_fhir(pr),
        pr_service._to_plain(pr),
        request,
    )


# ── Get own PractitionerRoles (/me) ───────────────────────────────────────────
# Declared before /{practitioner_role_id} to avoid routing conflicts.


@router.get(
    "/me",
    dependencies=[Depends(require_permission("practitioner_role", "read"))],
    operation_id="get_my_practitioner_roles",
    summary="List PractitionerRole resources for the currently authenticated user",
    description=(
        "Returns a paginated list of PractitionerRole records belonging to the authenticated user "
        "(identified by `sub` and `activeOrganizationId`). "
        "Filter by `active` or `practitioner_id`. "
        + _CONTENT_NEG
    ),
    response_description="Paginated PractitionerRole resources for the current user",
    responses={**_LIST_200, **_ERR_AUTH},
)
async def get_my_practitioner_roles(
    request: Request,
    active: Optional[bool] = Query(None, description="Filter by active status."),
    practitioner_id: Optional[int] = Query(None, description="Filter by public practitioner_id."),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    pr_service: PractitionerRoleService = Depends(get_practitioner_role_service),
):
    user_id: str = request.state.user.get("sub")
    org_id: str = request.state.user.get("activeOrganizationId")
    items, total = await pr_service.get_me(
        user_id, org_id,
        active=active, practitioner_id=practitioner_id,
        limit=limit, offset=offset,
    )
    return format_paginated_response(
        [pr_service._to_fhir(p) for p in items],
        [pr_service._to_plain(p) for p in items],
        total, limit, offset, request,
    )


# ── Get PractitionerRole by public practitioner_role_id ───────────────────────


@router.get(
    "/{practitioner_role_id}",
    dependencies=[Depends(require_permission("practitioner_role", "read"))],
    operation_id="get_practitioner_role_by_id",
    summary="Retrieve a PractitionerRole resource by public practitioner_role_id",
    description=(
        "Fetches a single PractitionerRole by its public integer `practitioner_role_id`. "
        + _CONTENT_NEG
    ),
    response_description="The requested PractitionerRole resource",
    responses={**_SINGLE_200, **_ERR_AUTH, **_ERR_NOT_FOUND},
)
async def get_practitioner_role(
    request: Request,
    pr: PractitionerRoleModel = Depends(resolve_practitioner_role),
    pr_service: PractitionerRoleService = Depends(get_practitioner_role_service),
):
    return format_response(
        pr_service._to_fhir(pr),
        pr_service._to_plain(pr),
        request,
    )


# ── Patch PractitionerRole ─────────────────────────────────────────────────────


@router.patch(
    "/{practitioner_role_id}",
    dependencies=[Depends(require_permission("practitioner_role", "update"))],
    operation_id="patch_practitioner_role",
    summary="Partially update a PractitionerRole resource",
    description=(
        "Patchable fields: `active`, `period_start`, `period_end`, `availability_exceptions`. "
        "Child arrays (identifier, code, specialty, location, healthcareService, characteristic, "
        "communication, contact, availability, endpoint) and the `practitioner`/`organization` "
        "references cannot be changed via PATCH — delete and re-create to correct those. "
        + _CONTENT_NEG
    ),
    response_description="The updated PractitionerRole resource",
    responses={**_SINGLE_200, **_ERR_AUTH, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_practitioner_role(
    payload: PractitionerRolePatchSchema,
    request: Request,
    pr: PractitionerRoleModel = Depends(resolve_practitioner_role),
    pr_service: PractitionerRoleService = Depends(get_practitioner_role_service),
):
    updated_by: str = request.state.user.get("sub")
    updated = await pr_service.patch_practitioner_role(
        pr.practitioner_role_id, payload, updated_by
    )
    if not updated:
        raise HTTPException(status_code=404, detail="PractitionerRole not found")
    return format_response(
        pr_service._to_fhir(updated),
        pr_service._to_plain(updated),
        request,
    )


# ── List PractitionerRoles ─────────────────────────────────────────────────────


@router.get(
    "/",
    dependencies=[Depends(require_permission("practitioner_role", "read"))],
    operation_id="list_practitioner_roles",
    summary="List all PractitionerRole resources",
    description=(
        "Returns a paginated list of PractitionerRole resources. "
        "Filter by `active`, `practitioner_id`, `user_id`, or `org_id`. "
        "Use `limit` and `offset` for pagination. "
        + _CONTENT_NEG
    ),
    response_description="Paginated PractitionerRole resources",
    responses={**_LIST_200, **_ERR_AUTH},
)
async def list_practitioner_roles(
    request: Request,
    active: Optional[bool] = Query(None, description="Filter by active status."),
    practitioner_id: Optional[int] = Query(None, description="Filter by public practitioner_id."),
    user_id: Optional[str] = Query(None),
    org_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    pr_service: PractitionerRoleService = Depends(get_practitioner_role_service),
):
    items, total = await pr_service.list_practitioner_roles(
        user_id=user_id, org_id=org_id,
        active=active, practitioner_id=practitioner_id,
        limit=limit, offset=offset,
    )
    return format_paginated_response(
        [pr_service._to_fhir(p) for p in items],
        [pr_service._to_plain(p) for p in items],
        total, limit, offset, request,
    )


# ── Delete PractitionerRole ────────────────────────────────────────────────────


@router.delete(
    "/{practitioner_role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("practitioner_role", "delete"))],
    operation_id="delete_practitioner_role",
    summary="Delete a PractitionerRole resource",
    description=(
        "Permanently deletes the PractitionerRole and all its associated child records. "
        "This operation is irreversible. Returns 204 No Content on success."
    ),
    responses={**_ERR_AUTH, **_ERR_NOT_FOUND},
)
async def delete_practitioner_role(
    pr: PractitionerRoleModel = Depends(resolve_practitioner_role),
    pr_service: PractitionerRoleService = Depends(get_practitioner_role_service),
):
    await pr_service.delete_practitioner_role(pr.practitioner_role_id)
    return None
