"""
FastAPI router for Task resources.

Endpoints:
  POST   /tasks/        — create a Task (with identifiers / inputs / outputs / ... in the body)
  GET    /tasks/{id}    — fetch a single Task by public ID
  GET    /tasks/        — paginated FHIR R4 search (status, intent, patient, owner, authored-on, ...)
  PATCH  /tasks/{id}    — partial update; child lists are replaced when sent; null clears a reference
  DELETE /tasks/{id}    — permanent delete (cascades to all child records)

All routes support content negotiation:
  - `Accept: application/json`      → plain snake_case JSON (default)
  - `Accept: application/fhir+json` → FHIR R4 resource / Bundle

RBAC is enforced via require_permission() for the ("task", <action>) pair.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response, get_accept_header
from app.core.schema_utils import inline_schema
from app.di.dependencies.task import get_task_service
from app.schemas.task.input import ListTasksSchema, TaskCreateSchema, TaskPatchSchema
from app.schemas.task.response import FhirBundleResponse, FhirTaskResponse, PaginatedTaskResponse, TaskRecord
from app.services.task_service import TaskService

# All routes are prefixed with /tasks; tagged for Swagger grouping.
router = APIRouter(prefix="/tasks", tags=["Tasks"])

# ── Shared error response descriptors ────────────────────────────────────────

_ERR_NOT_FOUND = {404: {"description": "Task not found"}}
_ERR_VALIDATION = {422: {"description": "Validation error — request body or query params failed validation"}}

# ── Shared success response descriptors ──────────────────────────────────────
# inline_schema() resolves Pydantic's $defs/$ref pointers so both content types
# render in Swagger UI without resolver errors.

_SINGLE_201 = {
    201: {
        "description": "Task created successfully",
        "content": {
            "application/json": {"schema": inline_schema(TaskRecord.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FhirTaskResponse.model_json_schema())},
        },
    }
}

_SINGLE_200 = {
    200: {
        "description": "Task retrieved or updated successfully",
        "content": {
            "application/json": {"schema": inline_schema(TaskRecord.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FhirTaskResponse.model_json_schema())},
        },
    }
}

_LIST_200 = {
    200: {
        "description": "Paginated list of Task resources",
        "content": {
            "application/json": {"schema": inline_schema(PaginatedTaskResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FhirBundleResponse.model_json_schema())},
        },
    }
}


# ── POST /tasks/ ─────────────────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_task",
    summary="Create a Task",
    description=(
        "Creates a unit of work to be performed. `status` and `intent` are required. Link the Task to what it "
        "actions with `focus` (e.g. `'ServiceRequest/80001'`), who it is for with `for` (e.g. `'Patient/10001'`), "
        "and optionally an `encounter`, a `requester`, an `owner`, a `location` and a `reason_reference`. "
        "Child lists (identifiers, based_on, part_of, performer_types, insurance, notes, relevant_history, "
        "restriction_recipients, inputs, outputs) are submitted in the single request body; each input/output "
        "carries a `type` and exactly one `value_*` variant (string, integer, boolean, code, date, dateTime, "
        "decimal, uri, time, instant, markdown, canonical, url, positiveInt, unsignedInt, base64Binary, id, "
        "Reference, Coding, CodeableConcept, Quantity, Period, Range, Attachment, Identifier, Money, Ratio). "
        "`last_modified` must not be before `authored_on`. References are `Type/id` strings — only their format "
        "is validated. Send `Accept: application/fhir+json` to receive the result in FHIR R4 format."
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
    dependencies=[Depends(require_permission("task", "create"))],
)
async def create_task(
    dto: TaskCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("task", "create")),
    service: TaskService = Depends(get_task_service),
) -> JSONResponse:
    """Create a new Task and return the persisted record."""
    data = await service.create(dto, actor, accept=get_accept_header(request))
    return format_response(data, request)


# ── GET /tasks/{resource_id} ─────────────────────────────────────────────────


@router.get(
    "/{resource_id}",
    operation_id="get_task",
    summary="Get a Task by ID",
    description="Fetch a single Task by its public integer ID. Send `Accept: application/fhir+json` for FHIR R4 format.",
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
    dependencies=[Depends(require_permission("task", "read"))],
)
async def get_task(
    resource_id: int,
    request: Request,
    actor: AuthUser = Depends(require_permission("task", "read")),
    service: TaskService = Depends(get_task_service),
) -> JSONResponse:
    """Fetch a single Task by its public ID."""
    data = await service.get_by_id(resource_id, actor, accept=get_accept_header(request))
    return format_response(data, request)


# ── GET /tasks/ ──────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_tasks",
    summary="Search Tasks",
    description=(
        "Searches Tasks using the FHIR R4 Task search parameters (https://www.hl7.org/fhir/R4/task.html#search). "
        "Token params (`status`, `intent`, `priority`, `code`, `business-status`, `identifier`, `group-identifier`, "
        "`performer`) accept `code`, `system|code`, `|code` or `system|`; comma = OR. Reference params (`subject`, "
        "`patient`, `focus`, `encounter`, `owner`, `requester`, `based-on`, `part-of`) accept `Type/id` or a bare "
        "numeric id. Date params (`authored-on`, `modified`, `period`, `_lastUpdated`) take an optional prefix "
        "eq|ne|gt|lt|ge|le|sa|eb|ap; repeat for AND (e.g. `authored-on=ge2024-01-01&authored-on=lt2024-02-01`). "
        "`period` matches the executionPeriod. `org_id` is mandatory on every search (tenant scope) and `user_id` is optional; paginate with `limit` / "
        "`offset`. Send `Accept: application/fhir+json` to receive a FHIR Bundle searchset."
    ),
    responses={**_LIST_200, **_ERR_VALIDATION},
    dependencies=[Depends(require_permission("task", "read"))],
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
    intent: Optional[str] = Query(None, description="Token: unknown|proposal|plan|order|original-order|reflex-order|filler-order|instance-order|option."),
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
    user_id: Optional[str] = Query(None, description="Optional: restrict to records owned by this user (JWT subject)."),
    org_id: str = Query(..., min_length=1, description="Tenant organization ID — mandatory scope of every search."),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    actor: AuthUser = Depends(require_permission("task", "read")),
    service: TaskService = Depends(get_task_service),
) -> JSONResponse:
    """
    Search Tasks with FHIR R4 search parameters.

    Parameters are declared explicitly (with aliases) because many FHIR names are hyphenated or
    underscore-prefixed. They are gathered into ListTasksSchema, whose validators (e.g. the
    status/intent/priority code check) run here; a failure is surfaced as a 422, not a 500.
    """
    try:
        filters = ListTasksSchema(
            id=id_, identifier=identifier, group_identifier=group_identifier, status=task_status, intent=intent,
            priority=priority, code=code, business_status=business_status, subject=subject, patient=patient,
            focus=focus, encounter=encounter, owner=owner, requester=requester, performer=performer,
            based_on=based_on, part_of=part_of, authored_on=authored_on, modified=modified, period=period,
            last_updated=last_updated, user_id=user_id, org_id=org_id, limit=limit, offset=offset,
        )
    except ValidationError as exc:
        # include_context=False keeps the detail JSON-serialisable (ctx can hold exceptions).
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.errors(include_url=False, include_context=False),
        ) from exc
    data = await service.list(filters, actor, accept=get_accept_header(request))
    return format_paginated_response(data, request)


# ── PATCH /tasks/{resource_id} ───────────────────────────────────────────────


@router.patch(
    "/{resource_id}",
    operation_id="update_task",
    summary="Partially update a Task",
    description=(
        "Update fields on a Task. At least one field must be provided; `status` and `intent` cannot be null. "
        "References (`focus`, `for`, `encounter`, `requester`, `owner`, `location`, `reason_reference`) are `Type/id` "
        "strings and can be changed through this gateway (the fhir-server also clears them with null). Child lists "
        "(identifiers, based_on, part_of, performer_types, insurance, notes, relevant_history, "
        "restriction_recipients, inputs, outputs) use REPLACE semantics: a list that is sent replaces the stored "
        "list in full, `[]` clears it, an omitted list is left untouched. "
        "Send `Accept: application/fhir+json` for FHIR R4 format."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
    dependencies=[Depends(require_permission("task", "update"))],
)
async def update_task(
    resource_id: int,
    dto: TaskPatchSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("task", "update")),
    service: TaskService = Depends(get_task_service),
) -> JSONResponse:
    """Partially update a Task. Returns 422 if the body is empty."""
    data = await service.update(resource_id, dto, actor, accept=get_accept_header(request))
    return format_response(data, request)


# ── DELETE /tasks/{resource_id} ──────────────────────────────────────────────


@router.delete(
    "/{resource_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_task",
    summary="Delete a Task",
    description="Permanently deletes the Task and all its child records. This operation is irreversible. Returns 204 No Content on success.",
    responses={**_ERR_NOT_FOUND},
    dependencies=[Depends(require_permission("task", "delete"))],
)
async def delete_task(
    resource_id: int,
    actor: AuthUser = Depends(require_permission("task", "delete")),
    service: TaskService = Depends(get_task_service),
) -> None:
    """Permanently delete a Task and cascade to all child records."""
    await service.delete(resource_id, actor)
