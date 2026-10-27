from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.core.content_negotiation import format_paginated_response, format_response
from app.core.schema_utils import inline_schema
from app.deps.plan_definition_deps import resolve_plan_definition
from app.di.dependencies.definition_apply import get_definition_apply_service
from app.di.dependencies.plan_definition import get_plan_definition_service
from app.models.plan_definition.plan_definition import PlanDefinitionModel
from app.repository.plan_definition_repository import PlanDefinitionSearch
from app.schemas.definition_apply import APPLY_200, PlanDefinitionApplyRequest
from app.schemas.plan_definition import PlanDefinitionCreateSchema, PlanDefinitionPatchSchema
from app.schemas.plan_definition.response import (
    FHIRPlanDefinitionBundle,
    FHIRPlanDefinitionSchema,
    PaginatedPlanDefinitionResponse,
    PlainPlanDefinitionResponse,
)
from app.services.definition_apply_service import DefinitionApplyService
from app.services.plan_definition_service import PlanDefinitionService

router = APIRouter()

_CONTENT_NEG = (
    "Set `Accept: application/fhir+json` to receive the full FHIR R4 representation; "
    "omit or use `Accept: application/json` for the simplified plain-JSON form."
)

_ERR_NOT_FOUND = {404: {"description": "PlanDefinition not found"}}
_ERR_VALIDATION = {422: {"description": "Validation error — request body or query params failed validation"}}

_SINGLE_200 = {
    200: {
        "content": {
            "application/json": {"schema": inline_schema(PlainPlanDefinitionResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRPlanDefinitionSchema.model_json_schema())},
        }
    }
}
_SINGLE_201 = {201: _SINGLE_200[200]}
_LIST_200 = {
    200: {
        "description": "Paginated list of plan definitions",
        "content": {
            "application/json": {"schema": inline_schema(PaginatedPlanDefinitionResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRPlanDefinitionBundle.model_json_schema())},
        },
    }
}


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_plan_definition",
    summary="Create a new PlanDefinition resource",
    description=(
        "Defines a protocol, order set or clinical decision-support rule. Only `status` is required. "
        "Supports the full R4 structure: `goal` (with `target`, `addresses`, `documentation`) and a recursive "
        "`action` tree (each action may carry `code`, `reason`, `documentation`, `goal_id`, `trigger`, `condition`, "
        "`input`/`output` data requirements, `related_action`, `participant`, `dynamic_value` and nested `action`s), "
        "plus `identifier`, `contact`, `author`, `editor`, `reviewer`, `endorser`, `use_context`, `jurisdiction`, "
        "`topic`, `related_artifact` and `library`. `subject_reference` is a Group reference (e.g. `'Group/5'`). "
        "R4 invariants (pld-1/pld-3/pld-4/pld-5, drq-1/drq-2, trd-1/trd-2, exp-1) are enforced. " + _CONTENT_NEG
    ),
    response_description="The newly created PlanDefinition resource",
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_plan_definition(
    payload: PlanDefinitionCreateSchema,
    request: Request,
    service: PlanDefinitionService = Depends(get_plan_definition_service),
):
    pd = await service.create_plan_definition(payload, payload.user_id, payload.org_id, payload.created_by)
    return format_response(service._to_fhir(pd), service._to_plain(pd), request)


@router.get(
    "/{plan_definition_id}",
    operation_id="get_plan_definition_by_id",
    summary="Retrieve a PlanDefinition resource by public plan_definition_id",
    description="Fetches a single PlanDefinition (with its full goal/action tree) by its public integer `plan_definition_id`. " + _CONTENT_NEG,
    response_description="The requested PlanDefinition resource",
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_plan_definition(
    request: Request,
    plan_definition: PlanDefinitionModel = Depends(resolve_plan_definition),
    service: PlanDefinitionService = Depends(get_plan_definition_service),
):
    return format_response(service._to_fhir(plan_definition), service._to_plain(plan_definition), request)


@router.patch(
    "/{plan_definition_id}",
    operation_id="patch_plan_definition",
    summary="Partially update a PlanDefinition resource",
    description=(
        "Scalar fields (`status` cannot be null, `url`, `version`, `name`, `title`, `date`, `type_*`, "
        "`subject_*`, `effective_period_*`, ...) are updated when present; references are `Type/id` and null "
        "clears the optional ones. Every child list — `identifier`, `contact`, `author`, `editor`, `reviewer`, "
        "`endorser`, `use_context`, `jurisdiction`, `topic`, `related_artifact`, `library`, `goal`, `action` — is "
        "patchable with REPLACE semantics: a list that is sent replaces the stored list in full, `[]`/null clears "
        "it, and an omitted list is left untouched. Replacing `goal` or `action` alone is rejected (422) if it "
        "would leave an action pointing at a missing goal id. " + _CONTENT_NEG
    ),
    response_description="The updated PlanDefinition resource",
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_plan_definition(
    payload: PlanDefinitionPatchSchema,
    request: Request,
    plan_definition: PlanDefinitionModel = Depends(resolve_plan_definition),
    service: PlanDefinitionService = Depends(get_plan_definition_service),
):
    updated = await service.patch_plan_definition(plan_definition.plan_definition_id, payload, payload.updated_by)
    if not updated:
        raise HTTPException(status_code=404, detail="PlanDefinition not found")
    return format_response(service._to_fhir(updated), service._to_plain(updated), request)


@router.get(
    "/",
    operation_id="list_plan_definitions",
    summary="Search PlanDefinition resources",
    description=(
        "Searches PlanDefinitions using the FHIR R4 search parameters "
        "(https://www.hl7.org/fhir/R4/plandefinition.html#search): `_id`, `identifier`, `url`, `version`, "
        "`name`, `title`, `publisher`, `description` (string: prefix match by default, `:contains`, `:exact`), "
        "`status`, `type`, `topic`, `jurisdiction`, `context` (use-context value), `context-type` (use-context code), "
        "`date`, `effective`, `definition` (action.definition canonical), `depends-on`, `derived-from`, "
        "`predecessor`, `successor`, `composed-of` and `_lastUpdated`. "
        "Token params accept `code`, `system|code`, `|code` or `system|`; comma = OR. Date params take an optional "
        "prefix eq|ne|gt|lt|ge|le|sa|eb|ap (repeat for AND). "
        "`org_id` is mandatory on every search (tenant scope) and `user_id` is optional; paginate with `limit` / `offset`. " + _CONTENT_NEG
    ),
    response_description="Paginated PlanDefinition resources",
    responses={**_LIST_200, **_ERR_VALIDATION},
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
    user_id: Optional[str] = Query(None, description="Optional: restrict to records owned by this user."),
    org_id: str = Query(..., min_length=1, description="Tenant organization id — mandatory scope of every search."),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: PlanDefinitionService = Depends(get_plan_definition_service),
):
    strings = {}
    for key, mode_values in {
        "name": {"startswith": name, "contains": name_contains, "exact": name_exact},
        "title": {"startswith": title, "contains": title_contains, "exact": title_exact},
        "publisher": {"startswith": publisher, "contains": publisher_contains, "exact": publisher_exact},
        "description": {"startswith": description, "contains": description_contains, "exact": description_exact},
    }.items():
        strings[key] = {m: v for m, v in mode_values.items() if v}
    search = PlanDefinitionSearch(
        id=id_, identifier=identifier, url=url, version=version, pd_status=pd_status, type=type_, topic=topic,
        jurisdiction=jurisdiction, context=context, context_type=context_type, definition=definition,
        depends_on=depends_on, derived_from=derived_from, predecessor=predecessor, successor=successor,
        composed_of=composed_of, date=date or [], effective=effective or [], last_updated=last_updated or [],
        strings=strings,
    )
    items, total = await service.list_plan_definitions(
        user_id=user_id, org_id=org_id, search=search, limit=limit, offset=offset)
    return format_paginated_response(
        [service._to_fhir(i) for i in items],
        [service._to_plain(i) for i in items],
        total, limit, offset, request,
    )


@router.delete(
    "/{plan_definition_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_plan_definition",
    summary="Delete a PlanDefinition resource",
    description=(
        "Permanently deletes the PlanDefinition with its goals, actions and every child record. "
        "This operation is irreversible. Returns 204 No Content on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_plan_definition(
    plan_definition: PlanDefinitionModel = Depends(resolve_plan_definition),
    service: PlanDefinitionService = Depends(get_plan_definition_service),
):
    await service.delete_plan_definition(plan_definition.plan_definition_id)
    return None


@router.post(
    "/{plan_definition_id}/$apply",
    operation_id="apply_plan_definition",
    summary="Apply a PlanDefinition to a subject — generate its ServiceRequests ($apply)",
    description=(
        "FHIR operation `PlanDefinition/$apply` "
        "(https://www.hl7.org/fhir/R4/plandefinition-operation-apply.html). Walks the plan's actions in order and, for "
        "every action whose `definitionCanonical` is an ActivityDefinition of this organization, generates one "
        "ServiceRequest for the `subject` (code, intent, priority, timing and quantity come from the ActivityDefinition; "
        "`practitioner` becomes the requester; the action description becomes the patient instruction; "
        "`instantiates_canonical` links back to the ActivityDefinition and this PlanDefinition). "
        "Only ActivityDefinition kind `ServiceRequest` is generated — other kinds, retired definitions, unresolved "
        "definitions and already-generated ones are returned in `skipped` with the reason. "
        "`persist=false` (default) is a preview and saves nothing; `persist=true` saves every ServiceRequest in one "
        "transaction. `selected_actions` limits the run to chosen `action[].id` values. "
        "Returns plain JSON by default, or a `collection` Bundle with `Accept: application/fhir+json`."
    ),
    response_description="The generated ServiceRequests and the skipped actions",
    responses={**APPLY_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def apply_plan_definition(
    payload: PlanDefinitionApplyRequest,
    request: Request,
    plan_definition: PlanDefinitionModel = Depends(resolve_plan_definition),
    apply_service: DefinitionApplyService = Depends(get_definition_apply_service),
):
    if plan_definition.org_id != payload.org_id:
        raise HTTPException(status_code=404, detail="PlanDefinition not found")
    result = await apply_service.apply_plan_definition(plan_definition, payload)
    return format_response(apply_service.to_fhir(result), apply_service.to_plain(result), request)
