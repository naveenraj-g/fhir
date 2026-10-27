"""
FastAPI router for ActivityDefinition resources.

Endpoints:
  POST   /activity-definitions/       — create an ActivityDefinition (dosage, participants, requirement lists, ...)
  GET    /activity-definitions/{id}   — fetch a single ActivityDefinition by public ID
  GET    /activity-definitions/       — paginated FHIR R4 search (name, status, topic, depends-on, ...)
  PATCH  /activity-definitions/{id}   — partial update; every child list is replaced when sent
  POST   /activity-definitions/{id}/$apply — apply to a subject: generate ServiceRequests
  DELETE /activity-definitions/{id}   — permanent delete (cascades to all child records)

All routes support content negotiation:
  - `Accept: application/json`      → plain snake_case JSON (default)
  - `Accept: application/fhir+json` → FHIR R4 resource / Bundle

RBAC is enforced via require_permission() for the ("activity_definition", <action>) pair.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response, get_accept_header
from app.core.schema_utils import inline_schema
from app.di.dependencies.activity_definition import get_activity_definition_service
from app.schemas.definition_apply import APPLY_200, ActivityDefinitionApplySchema
from app.schemas.activity_definition.input import ActivityDefinitionCreateSchema, ActivityDefinitionPatchSchema, ListActivityDefinitionsSchema
from app.schemas.activity_definition.response import FHIRActivityDefinitionBundle, FHIRActivityDefinitionSchema, PlainActivityDefinitionResponse, PaginatedActivityDefinitionResponse
from app.services.activity_definition_service import ActivityDefinitionService

# All routes are prefixed with /activity-definitions; tagged for Swagger grouping.
router = APIRouter(prefix="/activity-definitions", tags=["ActivityDefinitions"])

# ── Shared error response descriptors ────────────────────────────────────────

_ERR_NOT_FOUND = {404: {"description": "ActivityDefinition not found"}}
_ERR_VALIDATION = {422: {"description": "Validation error — request body or query params failed validation"}}

# ── Shared success response descriptors ──────────────────────────────────────
# inline_schema() resolves Pydantic's $defs/$ref pointers so both content types
# render in Swagger UI without resolver errors.

_SINGLE_201 = {
    201: {
        "description": "ActivityDefinition created successfully",
        "content": {
            "application/json": {"schema": inline_schema(PlainActivityDefinitionResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRActivityDefinitionSchema.model_json_schema())},
        },
    }
}

_SINGLE_200 = {
    200: {
        "description": "ActivityDefinition retrieved or updated successfully",
        "content": {
            "application/json": {"schema": inline_schema(PlainActivityDefinitionResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRActivityDefinitionSchema.model_json_schema())},
        },
    }
}

_LIST_200 = {
    200: {
        "description": "Paginated list of ActivityDefinition resources",
        "content": {
            "application/json": {"schema": inline_schema(PaginatedActivityDefinitionResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRActivityDefinitionBundle.model_json_schema())},
        },
    }
}


# ── POST /activity-definitions/ ─────────────────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_activity_definition",
    summary="Create an ActivityDefinition",
    description=(
        "Defines an action to be performed (a request template). Only `status` is required. Key fields: `kind` "
        "(the request resource it produces, e.g. `ServiceRequest`, `MedicationRequest`, `Task`), `intent`, `priority`, "
        "`code`, `do_not_perform`, `timing_*` (at most one of timing/datetime/age/period/range/duration), `location`, "
        "`product_reference` (Medication|Substance) or `product_cc_*`, `quantity`, `transform`, plus the child lists "
        "`participant`, `dosage` (full Dosage datatype with `dose_and_rate`), `body_site`, `specimen_requirement`, "
        "`observation_requirement`, `observation_result_requirement`, `dynamic_value`, and the metadata lists "
        "`identifier`, `contact`, `author`, `editor`, `reviewer`, `endorser`, `use_context`, `jurisdiction`, `topic`, "
        "`related_artifact`, `library`. `subject_reference` is a Group reference (e.g. `'Group/5'`) — only its format "
        "is validated. Send `Accept: application/fhir+json` to receive the result in FHIR R4 format."
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
    dependencies=[Depends(require_permission("activity_definition", "create"))],
)
async def create_activity_definition(
    dto: ActivityDefinitionCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("activity_definition", "create")),
    service: ActivityDefinitionService = Depends(get_activity_definition_service),
) -> JSONResponse:
    """Raise a new ActivityDefinition and return the persisted record."""
    data = await service.create(dto, actor, accept=get_accept_header(request))
    return format_response(data, request)


# ── GET /activity-definitions/{resource_id} ─────────────────────────────────────────────────


@router.get(
    "/{resource_id}",
    operation_id="get_activity_definition",
    summary="Get an ActivityDefinition by ID",
    description=(
        "Fetch a single ActivityDefinition by its public integer ID. Send `Accept: application/fhir+json` for FHIR R4 format."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
    dependencies=[Depends(require_permission("activity_definition", "read"))],
)
async def get_activity_definition(
    resource_id: int,
    request: Request,
    actor: AuthUser = Depends(require_permission("activity_definition", "read")),
    service: ActivityDefinitionService = Depends(get_activity_definition_service),
) -> JSONResponse:
    """Fetch a single ActivityDefinition by its public ID."""
    data = await service.get_by_id(resource_id, actor, accept=get_accept_header(request))
    return format_response(data, request)


# ── GET /activity-definitions/ ──────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_activity_definitions",
    summary="Search ActivityDefinitions",
    description=(
        "Searches ActivityDefinitions using the FHIR R4 search parameters "
        "(https://www.hl7.org/fhir/R4/activitydefinition.html#search): `_id`, `identifier`, `url`, `version`, "
        "`name`, `title`, `publisher`, `description` (string: prefix match by default, `:contains`, `:exact`), "
        "`status`, `topic`, `jurisdiction`, `context` (use-context value), `context-type` (use-context code), "
        "`date`, `effective`, `depends-on`, `derived-from`, `predecessor`, `successor`, `composed-of` and "
        "`_lastUpdated`. Token params accept `code`, `system|code`, `|code` or `system|`; comma = OR. Date params take "
        "an optional prefix eq|ne|gt|lt|ge|le|sa|eb|ap (repeat for AND). "
        "`org_id` is mandatory on every search (tenant scope) and `user_id` is optional; paginate with `limit` / `offset`. "
        "Send `Accept: application/fhir+json` to receive a FHIR Bundle searchset."
    ),
    responses={**_LIST_200, **_ERR_VALIDATION},
    dependencies=[Depends(require_permission("activity_definition", "read"))],
)
async def list_activity_definitions(
    request: Request,
    id_: Optional[str] = Query(None, alias="_id", description="Public activity_definition_id(s), comma-separated."),
    identifier: Optional[str] = Query(None, description="Token `[system|]value` of ActivityDefinition.identifier."),
    url: Optional[str] = Query(None, description="Canonical URL(s), comma = OR."),
    version: Optional[str] = Query(None, description="Business version(s), comma = OR."),
    name: Optional[str] = Query(None, description="Computer-friendly name (prefix match)."),
    name_contains: Optional[str] = Query(None, alias="name:contains", description="Name substring."),
    name_exact: Optional[str] = Query(None, alias="name:exact", description="Name exact, case-sensitive."),
    title: Optional[str] = Query(None, description="Title (prefix match)."),
    title_contains: Optional[str] = Query(None, alias="title:contains", description="Title substring."),
    title_exact: Optional[str] = Query(None, alias="title:exact", description="Title exact, case-sensitive."),
    publisher: Optional[str] = Query(None, description="Publisher (prefix match)."),
    publisher_contains: Optional[str] = Query(None, alias="publisher:contains", description="Publisher substring."),
    publisher_exact: Optional[str] = Query(None, alias="publisher:exact", description="Publisher exact."),
    description: Optional[str] = Query(None, description="Description (prefix match)."),
    description_contains: Optional[str] = Query(None, alias="description:contains", description="Description substring."),
    description_exact: Optional[str] = Query(None, alias="description:exact", description="Description exact."),
    ad_status: Optional[str] = Query(None, alias="status", description="Token: draft|active|retired|unknown (comma = OR)."),
    topic: Optional[str] = Query(None, description="Token `[system|]code` of ActivityDefinition.topic."),
    jurisdiction: Optional[str] = Query(None, description="Token `[system|]code` of ActivityDefinition.jurisdiction."),
    context: Optional[str] = Query(None, description="Token of useContext.valueCodeableConcept."),
    context_type: Optional[str] = Query(None, alias="context-type", description="Token of useContext.code."),
    depends_on: Optional[str] = Query(None, alias="depends-on", description="Resource the plan depends on (relatedArtifact depends-on / library)."),
    derived_from: Optional[str] = Query(None, alias="derived-from", description="Resource the plan is derived from."),
    predecessor: Optional[str] = Query(None, description="Predecessor resource."),
    successor: Optional[str] = Query(None, description="Successor resource."),
    composed_of: Optional[str] = Query(None, alias="composed-of", description="Resource the plan is composed of."),
    date: Optional[List[str]] = Query(None, description="Publication date with optional prefix. Repeat for AND."),
    effective: Optional[List[str]] = Query(None, description="Effective period with optional prefix. Repeat for AND."),
    last_updated: Optional[List[str]] = Query(None, alias="_lastUpdated", description="Last-updated instant with optional prefix."),
    user_id: Optional[str] = Query(None, description="Optional: restrict to records owned by this user (JWT subject)."),
    org_id: str = Query(..., min_length=1, description="Tenant organization ID — mandatory scope of every search."),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    actor: AuthUser = Depends(require_permission("activity_definition", "read")),
    service: ActivityDefinitionService = Depends(get_activity_definition_service),
) -> JSONResponse:
    """
    Search ActivityDefinitions with FHIR R4 search parameters.

    Parameters are declared explicitly (with aliases) because `_id` and `_lastUpdated`
    are not valid Python identifiers. They are gathered into ListActivityDefinitionsSchema, whose
    validators (e.g. the status code check) run here; a failure is surfaced as a 422.
    """
    try:
        filters = ListActivityDefinitionsSchema(
            id=id_, identifier=identifier, url=url, version=version,
            name=name, name_contains=name_contains, name_exact=name_exact,
            title=title, title_contains=title_contains, title_exact=title_exact,
            publisher=publisher, publisher_contains=publisher_contains, publisher_exact=publisher_exact,
            description=description, description_contains=description_contains, description_exact=description_exact,
            status=ad_status, topic=topic, jurisdiction=jurisdiction, context=context,
            context_type=context_type, depends_on=depends_on, derived_from=derived_from,
            predecessor=predecessor, successor=successor, composed_of=composed_of, date=date, effective=effective,
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


# ── PATCH /activity-definitions/{resource_id} ───────────────────────────────────────────────


@router.patch(
    "/{resource_id}",
    operation_id="update_activity_definition",
    summary="Partially update an ActivityDefinition",
    description=(
        "Update fields on an ActivityDefinition. At least one field must be provided. Scalar fields (`status`, `url`, "
        "`version`, `name`, `title`, `date`, `kind`, `intent`, `priority`, `code_*`, `timing_*`, `product_*`, `quantity`, "
        "`subject_*`, `effective_period_*`, ...) are updated when present; references are `Type/id`. Setting one "
        "variant of a choice (`timing[x]`, `subject[x]`, `product[x]`) clears the other variants. Every child list — "
        "`identifier`, `contact`, `author`, `editor`, `reviewer`, `endorser`, `use_context`, `jurisdiction`, `topic`, "
        "`related_artifact`, `library`, `participant`, `dosage`, `body_site`, `specimen_requirement`, "
        "`observation_requirement`, `observation_result_requirement`, `dynamic_value` — is patchable with REPLACE "
        "semantics: a list that is sent replaces the stored list in full, `[]` clears it, and an omitted list is left "
        "untouched. Send `Accept: application/fhir+json` for FHIR R4 format."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
    dependencies=[Depends(require_permission("activity_definition", "update"))],
)
async def update_activity_definition(
    resource_id: int,
    dto: ActivityDefinitionPatchSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("activity_definition", "update")),
    service: ActivityDefinitionService = Depends(get_activity_definition_service),
) -> JSONResponse:
    """Partially update an ActivityDefinition. Returns 422 if the body is empty."""
    data = await service.update(resource_id, dto, actor, accept=get_accept_header(request))
    return format_response(data, request)


# ── DELETE /activity-definitions/{resource_id} ──────────────────────────────────────────────


@router.delete(
    "/{resource_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_activity_definition",
    summary="Delete an ActivityDefinition",
    description=(
        "Permanently deletes the ActivityDefinition and its child records (identifier, category). "
        "This operation is irreversible. Returns 204 No Content on success."
    ),
    responses={**_ERR_NOT_FOUND},
    dependencies=[Depends(require_permission("activity_definition", "delete"))],
)
async def delete_activity_definition(
    resource_id: int,
    actor: AuthUser = Depends(require_permission("activity_definition", "delete")),
    service: ActivityDefinitionService = Depends(get_activity_definition_service),
) -> None:
    """Permanently delete an ActivityDefinition and cascade to its child records."""
    await service.delete(resource_id, actor)


# ── POST /activity-definitions/{resource_id}/$apply ───────────────────────────────────────────────


@router.post(
    "/{resource_id}/$apply",
    operation_id="apply_activity_definition",
    summary="Apply an ActivityDefinition to a subject — generate one ServiceRequest",
    description=(
        "FHIR operation `ActivityDefinition/$apply`. Turns this template into one ServiceRequest for the `subject` (code, intent, priority, timing and quantity are copied; `practitioner` becomes the requester). "
        "Only ActivityDefinition kind `ServiceRequest` is generated — other kinds, retired or unresolved definitions and "
        "ones already generated for the same subject/encounter are returned in `skipped` with the reason. "
        "`persist=false` (default) is a preview and saves nothing; `persist=true` saves every ServiceRequest in one "
        "transaction. Send `Accept: application/fhir+json` to receive a `collection` Bundle."
    ),
    responses={**APPLY_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
    dependencies=[Depends(require_permission("service_request", "create"))],
)
async def apply_activity_definition(
    resource_id: int,
    dto: ActivityDefinitionApplySchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("service_request", "create")),
    service: ActivityDefinitionService = Depends(get_activity_definition_service),
) -> JSONResponse:
    """Generate (preview or persist) the ServiceRequests of this ActivityDefinition for a subject."""
    data = await service.apply(resource_id, dto, actor, accept=get_accept_header(request))
    return format_response(data, request)
