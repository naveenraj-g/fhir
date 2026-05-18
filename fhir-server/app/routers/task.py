from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse

from app.auth.task_deps import resolve_task
from app.auth.dependencies import require_permission
from app.core.content_negotiation import format_paginated_response, format_response
from app.core.schema_utils import inline_schema
from app.di.dependencies.task import get_task_service
from app.models.task.task import TaskModel
from app.schemas.task.input import TaskCreateSchema, TaskPatchSchema
from app.schemas.task.response import (
    FHIRTaskBundle,
    FHIRTaskSchema,
    PaginatedTaskResponse,
    PlainTaskResponse,
)
from app.services.task_service import TaskService

router = APIRouter()

_CONTENT_NEG = (
    "Set `Accept: application/fhir+json` to receive the full FHIR R4 representation; "
    "omit or use `Accept: application/json` for the simplified plain-JSON form."
)

_ERR_AUTH = {
    401: {"description": "Not authenticated — Bearer token missing or expired"},
    403: {"description": "Forbidden — caller lacks the required permission"},
}
_ERR_NOT_FOUND = {404: {"description": "Task not found"}}
_ERR_VALIDATION = {422: {"description": "Validation error"}}

_SINGLE_200 = {
    200: {
        "content": {
            "application/json": {"schema": inline_schema(PlainTaskResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRTaskSchema.model_json_schema())},
        }
    }
}
_SINGLE_201 = {201: _SINGLE_200[200]}
_LIST_200 = {
    200: {
        "description": "Paginated list of Task resources",
        "content": {
            "application/json": {"schema": inline_schema(PaginatedTaskResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRTaskBundle.model_json_schema())},
        },
    }
}


# ── Create ──────────────────────────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("task", "create"))],
    operation_id="create_task",
    summary="Create a new Task resource",
    description=(
        "Creates a FHIR R4 Task resource. "
        "Required: `status`, `intent`. "
        "Optional: all other Task fields including child arrays (identifiers, basedOn, partOf, "
        "performerType, insurance, note, relevantHistory, restriction, input, output). "
        + _CONTENT_NEG
    ),
    response_description="The newly created Task resource",
    responses={**_SINGLE_201, **_ERR_AUTH, **_ERR_VALIDATION},
)
async def create_task(
    payload: TaskCreateSchema,
    request: Request,
    task_service: TaskService = Depends(get_task_service),
):
    created_by: str = request.state.user.get("sub")
    task = await task_service.create_task(payload, payload.user_id, payload.org_id, created_by)
    return format_response(
        task_service._to_fhir(task),
        task_service._to_plain(task),
        request,
    )


# ── Get my tasks ────────────────────────────────────────────────────────────────


@router.get(
    "/me",
    dependencies=[Depends(require_permission("task", "read"))],
    operation_id="list_my_tasks",
    summary="List Task records for the authenticated user",
    description=(
        "Returns Task records scoped to the authenticated user's `sub` and `activeOrganizationId`. "
        + _CONTENT_NEG
    ),
    responses={**_LIST_200, **_ERR_AUTH},
)
async def get_my_tasks(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    task_service: TaskService = Depends(get_task_service),
):
    user_id: str = request.state.user.get("sub")
    org_id: str = request.state.user.get("activeOrganizationId")
    rows, total = await task_service.get_me(user_id, org_id, limit=limit, offset=offset)
    return format_paginated_response(
        [task_service._to_fhir(r) for r in rows],
        [task_service._to_plain(r) for r in rows],
        total, limit, offset, request,
    )


# ── Get by ID ───────────────────────────────────────────────────────────────────


@router.get(
    "/{task_id}",
    dependencies=[Depends(require_permission("task", "read"))],
    operation_id="get_task",
    summary="Retrieve a single Task by public ID",
    description="Fetches a single Task resource by its public task_id. " + _CONTENT_NEG,
    responses={**_SINGLE_200, **_ERR_AUTH, **_ERR_NOT_FOUND},
)
async def get_task(
    request: Request,
    task: TaskModel = Depends(resolve_task),
    task_service: TaskService = Depends(get_task_service),
):
    return format_response(
        task_service._to_fhir(task),
        task_service._to_plain(task),
        request,
    )


# ── Patch ────────────────────────────────────────────────────────────────────────


@router.patch(
    "/{task_id}",
    dependencies=[Depends(require_permission("task", "update"))],
    operation_id="patch_task",
    summary="Partially update a Task resource",
    description=(
        "Updates fields on a Task. Provide only the fields to change. "
        "Child arrays (identifiers, basedOn, partOf, performerType, insurance, note, "
        "relevantHistory, restriction recipients, input, output) are fully replaced when supplied. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_AUTH, **_ERR_NOT_FOUND},
)
async def patch_task(
    request: Request,
    payload: TaskPatchSchema,
    task: TaskModel = Depends(resolve_task),
    task_service: TaskService = Depends(get_task_service),
):
    updated_by: str = request.state.user.get("sub")
    updated = await task_service.patch_task(task.task_id, payload, updated_by)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return format_response(
        task_service._to_fhir(updated),
        task_service._to_plain(updated),
        request,
    )


# ── List ─────────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    dependencies=[Depends(require_permission("task", "read"))],
    operation_id="list_tasks",
    summary="List Task resources",
    description="Returns a paginated list of Task resources. " + _CONTENT_NEG,
    responses={**_LIST_200, **_ERR_AUTH},
)
async def list_tasks(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    task_service: TaskService = Depends(get_task_service),
):
    rows, total = await task_service.list_tasks(limit=limit, offset=offset)
    return format_paginated_response(
        [task_service._to_fhir(r) for r in rows],
        [task_service._to_plain(r) for r in rows],
        total, limit, offset, request,
    )


# ── Delete ───────────────────────────────────────────────────────────────────────


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("task", "delete"))],
    operation_id="delete_task",
    summary="Delete a Task resource",
    description="Permanently deletes a Task and all its child resources.",
    responses={**_ERR_AUTH, **_ERR_NOT_FOUND, 204: {"description": "Task deleted"}},
)
async def delete_task(
    task: TaskModel = Depends(resolve_task),
    task_service: TaskService = Depends(get_task_service),
):
    await task_service.delete_task(task.task_id)
    return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)
