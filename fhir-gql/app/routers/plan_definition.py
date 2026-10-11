"""
FastAPI router for PlanDefinition resources.

Endpoints:
  POST   /plan-definitions/       — create a PlanDefinition (goals + recursive action tree)
  GET    /plan-definitions/{id}   — fetch a single PlanDefinition by public ID
  GET    /plan-definitions/       — paginated FHIR R4 search (name, status, type, topic, definition, ...)
  PATCH  /plan-definitions/{id}   — partial update; every child list (incl. goal / action) is replaced when sent
  DELETE /plan-definitions/{id}   — permanent delete (cascades to all child records)

All routes support content negotiation:
  - `Accept: application/json`      → plain snake_case JSON (default)
  - `Accept: application/fhir+json` → FHIR R4 resource / Bundle

RBAC is enforced via require_permission() for the ("plan_definition", <action>) pair.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response, get_accept_header
from app.core.schema_utils import inline_schema
from app.di.dependencies.plan_definition import get_plan_definition_service
from app.schemas.plan_definition.input import PlanDefinitionCreateSchema, PlanDefinitionPatchSchema, ListPlanDefinitionsSchema
from app.schemas.plan_definition.response import FHIRPlanDefinitionBundle, FHIRPlanDefinitionSchema, PlainPlanDefinitionResponse, PaginatedPlanDefinitionResponse
from app.services.plan_definition_service import PlanDefinitionService

# All routes are prefixed with /plan-definitions; tagged for Swagger grouping.
router = APIRouter(prefix="/plan-definitions", tags=["PlanDefinitions"])

# ── Shared error response descriptors ────────────────────────────────────────

_ERR_NOT_FOUND = {404: {"description": "PlanDefinition not found"}}
_ERR_VALIDATION = {422: {"description": "Validation error — request body or query params failed validation"}}

# ── Shared success response descriptors ──────────────────────────────────────
# inline_schema() resolves Pydantic's $defs/$ref pointers so both content types
# render in Swagger UI without resolver errors.

_SINGLE_201 = {
    201: {
        "description": "PlanDefinition created successfully",
        "content": {
            "application/json": {"schema": inline_schema(PlainPlanDefinitionResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRPlanDefinitionSchema.model_json_schema())},
        },
    }
}

_SINGLE_200 = {
    200: {
        "description": "PlanDefinition retrieved or updated successfully",
        "content": {
            "application/json": {"schema": inline_schema(PlainPlanDefinitionResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRPlanDefinitionSchema.model_json_schema())},
        },
    }
}

_LIST_200 = {
    200: {
        "description": "Paginated list of PlanDefinition resources",
        "content": {
            "application/json": {"schema": inline_schema(PaginatedPlanDefinitionResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRPlanDefinitionBundle.model_json_schema())},
        },
    }
}


# ── POST /plan-definitions/ ─────────────────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_plan_definition",
    summary="Create a PlanDefinition",
    description=(
        "Defines a protocol, order set or clinical decision-support rule. Only `status` is required. "
        "Supports the full R4 structure: `goal` (with `target`, `addresses`, `documentation`) and a recursive "
        "`action` tree (each action may carry `code`, `reason`, `documentation`, `goal_id`, `trigger`, `condition`, "
        "`input`/`output` data requirements, `related_action`, `participant`, `dynamic_value` and nested `action`s), "
        "plus `identifier`, `contact`, `author`, `editor`, `reviewer`, `endorser`, `use_context`, `jurisdiction`, "
        "`topic`, `related_artifact` and `library`. `subject_reference` is a Group reference (e.g. `'Group/5'`) — "
        "only its format is validated. R4 invariants (pld-1/3/4/5, drq-1/2, trd-1/2, exp-1) are enforced. "
        "Send `Accept: application/fhir+json` to receive the result in FHIR R4 format."
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
    dependencies=[Depends(require_permission("plan_definition", "create"))],
)
async def create_plan_definition(
    dto: PlanDefinitionCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("plan_definition", "create")),
    service: PlanDefinitionService = Depends(get_plan_definition_service),
) -> JSONResponse:
    """Raise a new PlanDefinition and return the persisted record."""
    data = await service.create(dto, actor, accept=get_accept_header(request))
    return format_response(data, request)


# ── GET /plan-definitions/{resource_id} ─────────────────────────────────────────────────


@router.get(
    "/{resource_id}",
    operation_id="get_plan_definition",
    summary="Get a PlanDefinition by ID",
    description=(
        "Fetch a single PlanDefinition by its public integer ID. Send `Accept: application/fhir+json` for FHIR R4 format."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
    dependencies=[Depends(require_permission("plan_definition", "read"))],
)
async def get_plan_definition(
    resource_id: int,
    request: Request,
    actor: AuthUser = Depends(require_permission("plan_definition", "read")),
    service: PlanDefinitionService = Depends(get_plan_definition_service),
) -> JSONResponse:
    """Fetch a single PlanDefinition by its public ID."""
    data = await service.get_by_id(resource_id, actor, accept=get_accept_header(request))
    return format_response(data, request)


# ── GET /plan-definitions/ ──────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_plan_definitions",
    summary="Search PlanDefinitions",
    description=(
        "Searches PlanDefinitions using the FHIR R4 search parameters "
        "(https://www.hl7.org/fhir/R4/plandefinition.html#search): `_id`, `identifier`, `url`, `version`, "
        "`name`, `title`, `publisher`, `description` (string: prefix match by default, `:contains`, `:exact`), "
        "`status`, `type`, `topic`, `jurisdiction`, `context` (use-context value), `context-type` (use-context code), "
        "`date`, `effective`, `definition` (action.definition canonical), `depends-on`, `derived-from`, "
        "`predecessor`, `successor`, `composed-of` and `_lastUpdated`. "
        "Token params accept `code`, `system|code`, `|code` or `system|`; comma = OR. Date params take an optional "
        "prefix eq|ne|gt|lt|ge|le|sa|eb|ap (repeat for AND). "
        "`org_id` is mandatory on every search (tenant scope) and `user_id` is optional; paginate with `limit` / `offset`. "
        "Send `Accept: application/fhir+json` to receive a FHIR Bundle searchset."
    ),
    responses={**_LIST_200, **_ERR_VALIDATION},
    dependencies=[Depends(require_permission("plan_definition", "read"))],
)
async def list_plan_definitions(
    request: Request,
    id_: Optional[str] = Query(None, alias="_id", description="Public plan_definition_id(s), comma-separated."),
    identifier: Optional[str] = Query(None, description="Token `[system|]value` of PlanDefinition.identifier."),
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
    pd_status: Optional[str] = Query(None, alias="status", description="Token: draft|active|retired|unknown (comma = OR)."),
    type_: Optional[str] = Query(None, alias="type", description="Token `[system|]code` of PlanDefinition.type."),
    topic: Optional[str] = Query(None, description="Token `[system|]code` of PlanDefinition.topic."),
    jurisdiction: Optional[str] = Query(None, description="Token `[system|]code` of PlanDefinition.jurisdiction."),
    context: Optional[str] = Query(None, description="Token of useContext.valueCodeableConcept."),
    context_type: Optional[str] = Query(None, alias="context-type", description="Token of useContext.code."),
    definition: Optional[str] = Query(None, description="Action definition canonical, e.g. `ActivityDefinition/1` or a full URL."),
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
    actor: AuthUser = Depends(require_permission("plan_definition", "read")),
    service: PlanDefinitionService = Depends(get_plan_definition_service),
) -> JSONResponse:
    """
    Search PlanDefinitions with FHIR R4 search parameters.

    Parameters are declared explicitly (with aliases) because `_id` and `_lastUpdated`
    are not valid Python identifiers. They are gathered into ListPlanDefinitionsSchema, whose
    validators (e.g. the status code check) run here; a failure is surfaced as a 422.
    """
    try:
        filters = ListPlanDefinitionsSchema(
            id=id_, identifier=identifier, url=url, version=version,
            name=name, name_contains=name_contains, name_exact=name_exact,
            title=title, title_contains=title_contains, title_exact=title_exact,
            publisher=publisher, publisher_contains=publisher_contains, publisher_exact=publisher_exact,
            description=description, description_contains=description_contains, description_exact=description_exact,
            status=pd_status, type=type_, topic=topic, jurisdiction=jurisdiction, context=context,
            context_type=context_type, definition=definition, depends_on=depends_on, derived_from=derived_from,
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


# ── PATCH /plan-definitions/{resource_id} ───────────────────────────────────────────────


@router.patch(
    "/{resource_id}",
    operation_id="update_plan_definition",
    summary="Partially update a PlanDefinition",
    description=(
        "Update fields on a PlanDefinition. At least one field must be provided. Scalar fields (`status`, `url`, "
        "`version`, `name`, `title`, `date`, `type_*`, `subject_*`, `effective_period_*`, ...) are updated when present; "
        "references are `Type/id`. Every child list — `identifier`, `contact`, `author`, `editor`, `reviewer`, "
        "`endorser`, `use_context`, `jurisdiction`, `topic`, `related_artifact`, `library`, `goal`, `action` — is "
        "patchable with REPLACE semantics: a list that is sent replaces the stored list in full, `[]` clears it, and "
        "an omitted list is left untouched. Sending `action` replaces the ENTIRE action tree. Replacing `goal` or "
        "`action` alone is rejected (422) if an action would be left pointing at a missing goal id. "
        "Send `Accept: application/fhir+json` for FHIR R4 format."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
    dependencies=[Depends(require_permission("plan_definition", "update"))],
)
async def update_plan_definition(
    resource_id: int,
    dto: PlanDefinitionPatchSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("plan_definition", "update")),
    service: PlanDefinitionService = Depends(get_plan_definition_service),
) -> JSONResponse:
    """Partially update a PlanDefinition. Returns 422 if the body is empty."""
    data = await service.update(resource_id, dto, actor, accept=get_accept_header(request))
    return format_response(data, request)


# ── DELETE /plan-definitions/{resource_id} ──────────────────────────────────────────────


@router.delete(
    "/{resource_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_plan_definition",
    summary="Delete a PlanDefinition",
    description=(
        "Permanently deletes the PlanDefinition and its child records (identifier, category). "
        "This operation is irreversible. Returns 204 No Content on success."
    ),
    responses={**_ERR_NOT_FOUND},
    dependencies=[Depends(require_permission("plan_definition", "delete"))],
)
async def delete_plan_definition(
    resource_id: int,
    actor: AuthUser = Depends(require_permission("plan_definition", "delete")),
    service: PlanDefinitionService = Depends(get_plan_definition_service),
) -> None:
    """Permanently delete a PlanDefinition and cascade to its child records."""
    await service.delete(resource_id, actor)
