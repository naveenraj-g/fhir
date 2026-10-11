from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from app.deps.task_deps import resolve_task
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
from app.repository.task_repository import TaskSearch
from app.services.task_service import TaskService

router = APIRouter()

_CONTENT_NEG = (
    "Set `Accept: application/fhir+json` to receive the full FHIR R4 representation; "
    "omit or use `Accept: application/json` for the simplified plain-JSON form."
)

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
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_task(
    payload: TaskCreateSchema,
    request: Request,
    task_service: TaskService = Depends(get_task_service),
):
    created_by = payload.created_by
    task = await task_service.create_task(payload, payload.user_id, payload.org_id, created_by)
    return format_response(
        task_service._to_fhir(task),
        task_service._to_plain(task),
        request,
    )


# ── Get my tasks ────────────────────────────────────────────────────────────────



@router.get(
    "/{task_id}",
    operation_id="get_task",
    summary="Retrieve a single Task by public ID",
    description="Fetches a single Task resource by its public task_id. " + _CONTENT_NEG,
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
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
    operation_id="patch_task",
    summary="Partially update a Task resource",
    description=(
        "Updates fields on a Task. Provide only the fields to change. `status` and `intent` cannot be null. "
        "References (`focus`, `for`, `encounter`, `requester`, `owner`, `location`, `reason_reference`) are `Type/id` "
        "strings; send null to clear one. Child lists (identifiers, based_on, part_of, performer_types, insurance, "
        "notes, relevant_history, restriction_recipients, inputs, outputs) use REPLACE semantics: a list that is "
        "sent replaces the stored list in full, `[]` clears it, an omitted list is left untouched. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_task(
    request: Request,
    payload: TaskPatchSchema,
    task: TaskModel = Depends(resolve_task),
    task_service: TaskService = Depends(get_task_service),
):
    updated_by = payload.updated_by
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
    operation_id="list_tasks",
    summary="Search Task resources",
    description=(
        "Searches Tasks using the FHIR R4 Task search parameters (https://www.hl7.org/fhir/R4/task.html#search). "
        "Token params (`status`, `intent`, `priority`, `code`, `business-status`, `identifier`, `group-identifier`, "
        "`performer`) accept `code`, `system|code`, `|code` or `system|`; comma = OR. Reference params "
        "(`subject`, `patient`, `focus`, `encounter`, `owner`, `requester`, `based-on`, `part-of`) accept `Type/id` "
        "or a bare numeric id. Date params (`authored-on`, `modified`, `period`, `_lastUpdated`) take an optional "
        "prefix eq|ne|gt|lt|ge|le|sa|eb|ap; repeat for AND (e.g. `authored-on=ge2024-01-01&authored-on=lt2024-02-01`). "
        "`period` matches the executionPeriod. `org_id` is mandatory on every search (tenant scope) and `user_id` is optional; paginate with `limit` / "
        "`offset`. " + _CONTENT_NEG
    ),
    responses={**_LIST_200, **_ERR_VALIDATION},
)
async def list_tasks(
    request: Request,
    id_: Optional[str] = Query(None, alias="_id", description="Public task_id(s), comma-separated."),
    identifier: Optional[str] = Query(None, description="Token `[system|]value` of Task.identifier."),
    group_identifier: Optional[str] = Query(None, alias="group-identifier", description="Token `[system|]value` of Task.groupIdentifier."),
    task_status: Optional[str] = Query(
        None, alias="status",
        description="Token: draft|requested|received|accepted|rejected|ready|cancelled|in-progress|on-hold|failed|completed|entered-in-error (comma = OR).",
    ),
    intent: Optional[str] = Query(
        None, description="Token: unknown|proposal|plan|order|original-order|reflex-order|filler-order|instance-order|option."
    ),
    priority: Optional[str] = Query(None, description="Token: routine|urgent|asap|stat."),
    code: Optional[str] = Query(None, description="Token `[system|]code` of Task.code."),
    business_status: Optional[str] = Query(None, alias="business-status", description="Token `[system|]code` of Task.businessStatus."),
    subject: Optional[str] = Query(None, description="Task.for reference (any type), e.g. `Patient/10001`."),
    patient: Optional[str] = Query(None, description="Task.for as a Patient: `Patient/10001` or `10001`."),
    focus: Optional[str] = Query(None, description="Task.focus reference (any type), e.g. `ServiceRequest/80001`."),
    encounter: Optional[str] = Query(None, description="Encounter reference: `Encounter/20001` or `20001`."),
    owner: Optional[str] = Query(None, description="Owner reference: Practitioner|PractitionerRole|Organization|CareTeam|HealthcareService|Patient|Device|RelatedPerson."),
    requester: Optional[str] = Query(None, description="Requester reference: Device|Organization|Patient|Practitioner|PractitionerRole|RelatedPerson."),
    performer: Optional[str] = Query(None, description="Token `[system|]code` of Task.performerType."),
    based_on: Optional[str] = Query(None, alias="based-on", description="basedOn reference (any type), e.g. `ServiceRequest/80001`."),
    part_of: Optional[str] = Query(None, alias="part-of", description="partOf reference: `Task/280001`."),
    authored_on: Optional[List[str]] = Query(None, alias="authored-on", description="authoredOn with optional prefix, e.g. `ge2024-01-01`. Repeat for AND."),
    modified: Optional[List[str]] = Query(None, description="lastModified with optional prefix. Repeat for AND."),
    period: Optional[List[str]] = Query(None, description="executionPeriod with optional prefix. Repeat for AND."),
    last_updated: Optional[List[str]] = Query(None, alias="_lastUpdated", description="Last-updated instant with optional prefix."),
    user_id: Optional[str] = Query(None, description="Optional: restrict to records owned by this user."),
    org_id: str = Query(..., min_length=1, description="Tenant organization id — mandatory scope of every search."),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    task_service: TaskService = Depends(get_task_service),
):
    search = TaskSearch(
        id=id_, identifier=identifier, group_identifier=group_identifier, task_status=task_status,
        intent=intent, priority=priority, code=code, business_status=business_status, subject=subject,
        patient=patient, focus=focus, encounter=encounter, owner=owner, requester=requester,
        performer=performer, based_on=based_on, part_of=part_of, authored_on=authored_on or [],
        modified=modified or [], period=period or [], last_updated=last_updated or [],
    )
    rows, total = await task_service.list_tasks(
        user_id=user_id, org_id=org_id, search=search, limit=limit, offset=offset,
    )
    return format_paginated_response(
        [task_service._to_fhir(r) for r in rows],
        [task_service._to_plain(r) for r in rows],
        total, limit, offset, request,
    )


# ── Delete ───────────────────────────────────────────────────────────────────────


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_task",
    summary="Delete a Task resource",
    description="Permanently deletes a Task and all its child resources.",
    responses={**_ERR_NOT_FOUND, 204: {"description": "Task deleted"}},
)
async def delete_task(
    task: TaskModel = Depends(resolve_task),
    task_service: TaskService = Depends(get_task_service),
):
    await task_service.delete_task(task.task_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
