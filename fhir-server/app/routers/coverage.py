from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse

from app.auth.coverage_deps import get_authorized_coverage
from app.auth.dependencies import require_permission
from app.core.content_negotiation import format_paginated_response, format_response
from app.core.schema_utils import inline_schema
from app.di.dependencies.coverage import get_coverage_service
from app.models.coverage.coverage import CoverageModel
from app.schemas.coverage.input import CoverageCreateSchema, CoveragePatchSchema
from app.schemas.coverage.response import (
    FHIRCoverageBundle,
    FHIRCoverageSchema,
    PaginatedCoverageResponse,
    PlainCoverageResponse,
)
from app.services.coverage_service import CoverageService

router = APIRouter()

_CONTENT_NEG = (
    "Set `Accept: application/fhir+json` to receive the full FHIR R4 representation; "
    "omit or use `Accept: application/json` for the simplified plain-JSON form."
)

_ERR_AUTH = {
    401: {"description": "Not authenticated — Bearer token missing or expired"},
    403: {"description": "Forbidden — caller lacks the required permission"},
}
_ERR_NOT_FOUND = {404: {"description": "Coverage not found"}}
_ERR_VALIDATION = {422: {"description": "Validation error"}}

_SINGLE_200 = {
    200: {
        "content": {
            "application/json": {"schema": inline_schema(PlainCoverageResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRCoverageSchema.model_json_schema())},
        }
    }
}
_SINGLE_201 = {201: _SINGLE_200[200]}
_LIST_200 = {
    200: {
        "description": "Paginated list of coverage resources",
        "content": {
            "application/json": {"schema": inline_schema(PaginatedCoverageResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRCoverageBundle.model_json_schema())},
        },
    }
}


# ── Create ─────────────────────────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("coverage", "create"))],
    operation_id="create_coverage",
    summary="Create a new Coverage resource",
    description=(
        "Creates a FHIR R4 Coverage resource. "
        "Required fields: `status`, `beneficiary` (Patient reference), `payor` (at least one). "
        + _CONTENT_NEG
    ),
    response_description="The newly created Coverage resource",
    responses={**_SINGLE_201, **_ERR_AUTH, **_ERR_VALIDATION},
)
async def create_coverage(
    payload: CoverageCreateSchema,
    request: Request,
    coverage_service: CoverageService = Depends(get_coverage_service),
):
    created_by: str = request.state.user.get("sub")
    coverage = await coverage_service.create_coverage(
        payload, payload.user_id, payload.org_id, created_by
    )
    return format_response(
        coverage_service._to_fhir(coverage),
        coverage_service._to_plain(coverage),
        request,
    )


# ── Get my coverages ───────────────────────────────────────────────────────────


@router.get(
    "/me",
    dependencies=[Depends(require_permission("coverage", "read"))],
    operation_id="list_my_coverages",
    summary="List coverages for the authenticated user",
    description=(
        "Returns coverages scoped to the authenticated user's `sub` and `activeOrganizationId`. "
        + _CONTENT_NEG
    ),
    responses={**_LIST_200, **_ERR_AUTH},
)
async def get_my_coverages(
    request: Request,
    coverage_status: Optional[str] = Query(None, alias="status", description="Filter by status."),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    coverage_service: CoverageService = Depends(get_coverage_service),
):
    user_id: str = request.state.user.get("sub")
    org_id: str = request.state.user.get("activeOrganizationId")
    rows, total = await coverage_service.get_me(
        user_id, org_id, coverage_status=coverage_status, limit=limit, offset=offset
    )
    return format_paginated_response(
        [coverage_service._to_fhir(r) for r in rows],
        [coverage_service._to_plain(r) for r in rows],
        total, limit, offset, request,
    )


# ── Get by ID ──────────────────────────────────────────────────────────────────


@router.get(
    "/{coverage_id}",
    dependencies=[Depends(require_permission("coverage", "read"))],
    operation_id="get_coverage",
    summary="Retrieve a single Coverage by public ID",
    description="Fetches a single Coverage resource by its public coverage_id. " + _CONTENT_NEG,
    responses={**_SINGLE_200, **_ERR_AUTH, **_ERR_NOT_FOUND},
)
async def get_coverage(
    request: Request,
    coverage: CoverageModel = Depends(get_authorized_coverage),
    coverage_service: CoverageService = Depends(get_coverage_service),
):
    return format_response(
        coverage_service._to_fhir(coverage),
        coverage_service._to_plain(coverage),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{coverage_id}",
    dependencies=[Depends(require_permission("coverage", "update"))],
    operation_id="patch_coverage",
    summary="Partially update a Coverage resource",
    description="Updates scalar fields on a Coverage. Child arrays are not modified via PATCH.",
    responses={**_SINGLE_200, **_ERR_AUTH, **_ERR_NOT_FOUND},
)
async def patch_coverage(
    request: Request,
    payload: CoveragePatchSchema,
    coverage: CoverageModel = Depends(get_authorized_coverage),
    coverage_service: CoverageService = Depends(get_coverage_service),
):
    updated_by: str = request.state.user.get("sub")
    updated = await coverage_service.patch_coverage(coverage.coverage_id, payload, updated_by)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coverage not found")
    return format_response(
        coverage_service._to_fhir(updated),
        coverage_service._to_plain(updated),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    dependencies=[Depends(require_permission("coverage", "read"))],
    operation_id="list_coverages",
    summary="List Coverage resources",
    description="Returns a paginated list of Coverage resources. " + _CONTENT_NEG,
    responses={**_LIST_200, **_ERR_AUTH},
)
async def list_coverages(
    request: Request,
    coverage_status: Optional[str] = Query(None, alias="status", description="Filter by status."),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    coverage_service: CoverageService = Depends(get_coverage_service),
):
    rows, total = await coverage_service.list_coverages(
        coverage_status=coverage_status, limit=limit, offset=offset
    )
    return format_paginated_response(
        [coverage_service._to_fhir(r) for r in rows],
        [coverage_service._to_plain(r) for r in rows],
        total, limit, offset, request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{coverage_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("coverage", "delete"))],
    operation_id="delete_coverage",
    summary="Delete a Coverage resource",
    description="Permanently deletes a Coverage and all its child resources.",
    responses={**_ERR_AUTH, **_ERR_NOT_FOUND, 204: {"description": "Coverage deleted"}},
)
async def delete_coverage(
    coverage: CoverageModel = Depends(get_authorized_coverage),
    coverage_service: CoverageService = Depends(get_coverage_service),
):
    await coverage_service.delete_coverage(coverage.coverage_id)
    return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)
