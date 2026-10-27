from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.core.content_negotiation import format_paginated_response, format_response
from app.core.schema_utils import inline_schema
from app.deps.activity_definition_deps import resolve_activity_definition
from app.di.dependencies.activity_definition import get_activity_definition_service
from app.di.dependencies.definition_apply import get_definition_apply_service
from app.models.activity_definition.activity_definition import ActivityDefinitionModel
from app.repository.activity_definition_repository import ActivityDefinitionSearch
from app.schemas.definition_apply import APPLY_200, ActivityDefinitionApplyRequest
from app.schemas.activity_definition import ActivityDefinitionCreateSchema, ActivityDefinitionPatchSchema
from app.schemas.activity_definition.response import (
    FHIRActivityDefinitionBundle,
    FHIRActivityDefinitionSchema,
    PaginatedActivityDefinitionResponse,
    PlainActivityDefinitionResponse,
)
from app.services.activity_definition_service import ActivityDefinitionService
from app.services.definition_apply_service import DefinitionApplyService

router = APIRouter()

_CONTENT_NEG = (
    "Set `Accept: application/fhir+json` to receive the full FHIR R4 representation; "
    "omit or use `Accept: application/json` for the simplified plain-JSON form."
)

_ERR_NOT_FOUND = {404: {"description": "ActivityDefinition not found"}}
_ERR_VALIDATION = {422: {"description": "Validation error — request body or query params failed validation"}}

_SINGLE_200 = {
    200: {
        "content": {
            "application/json": {"schema": inline_schema(PlainActivityDefinitionResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRActivityDefinitionSchema.model_json_schema())},
        }
    }
}
_SINGLE_201 = {201: _SINGLE_200[200]}
_LIST_200 = {
    200: {
        "description": "Paginated list of activity definitions",
        "content": {
            "application/json": {"schema": inline_schema(PaginatedActivityDefinitionResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRActivityDefinitionBundle.model_json_schema())},
        },
    }
}


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_activity_definition",
    summary="Create a new ActivityDefinition resource",
    description=(
        "Defines an action to be performed (a request template). Only `status` is required. Key fields: `kind` "
        "(the request resource it produces, e.g. `ServiceRequest`, `MedicationRequest`, `Task`), `intent`, `priority`, "
        "`code`, `do_not_perform`, `timing_*` (at most one of timing/datetime/age/period/range/duration), `location`, "
        "`product_reference` (Medication|Substance) or `product_cc_*`, `quantity`, `transform`, plus the child lists "
        "`participant`, `dosage` (full Dosage datatype with `dose_and_rate`), `body_site`, `specimen_requirement`, "
        "`observation_requirement`, `observation_result_requirement`, `dynamic_value`, and the metadata lists "
        "`identifier`, `contact`, `author`, `editor`, `reviewer`, `endorser`, `use_context`, `jurisdiction`, `topic`, "
        "`related_artifact`, `library`. `subject_reference` is a Group reference (e.g. `'Group/5'`). "
        + _CONTENT_NEG
    ),
    response_description="The newly created ActivityDefinition resource",
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_activity_definition(
    payload: ActivityDefinitionCreateSchema,
    request: Request,
    service: ActivityDefinitionService = Depends(get_activity_definition_service),
):
    pd = await service.create_activity_definition(payload, payload.user_id, payload.org_id, payload.created_by)
    return format_response(service._to_fhir(pd), service._to_plain(pd), request)


@router.get(
    "/{activity_definition_id}",
    operation_id="get_activity_definition_by_id",
    summary="Retrieve a ActivityDefinition resource by public activity_definition_id",
    description="Fetches a single ActivityDefinition by its public integer `activity_definition_id`. " + _CONTENT_NEG,
    response_description="The requested ActivityDefinition resource",
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_activity_definition(
    request: Request,
    activity_definition: ActivityDefinitionModel = Depends(resolve_activity_definition),
    service: ActivityDefinitionService = Depends(get_activity_definition_service),
):
    return format_response(service._to_fhir(activity_definition), service._to_plain(activity_definition), request)


@router.patch(
    "/{activity_definition_id}",
    operation_id="patch_activity_definition",
    summary="Partially update a ActivityDefinition resource",
    description=(
        "Scalar fields (`status` cannot be null, `url`, `version`, `name`, `title`, `date`, `kind`, `intent`, `priority`, "
        "`code_*`, `timing_*`, `product_*`, `quantity`, `subject_*`, `effective_period_*`, ...) are updated when present; "
        "references are `Type/id` and null clears the optional ones. Setting one variant of a choice (`timing[x]`, "
        "`subject[x]`, `product[x]`) clears the other variants. Every child list — `identifier`, `contact`, `author`, "
        "`editor`, `reviewer`, `endorser`, `use_context`, `jurisdiction`, `topic`, `related_artifact`, `library`, "
        "`participant`, `dosage`, `body_site`, `specimen_requirement`, `observation_requirement`, "
        "`observation_result_requirement`, `dynamic_value` — is patchable with REPLACE semantics: a list that is sent "
        "replaces the stored list in full, `[]`/null clears it, and an omitted list is left untouched. "
        + _CONTENT_NEG
    ),
    response_description="The updated ActivityDefinition resource",
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_activity_definition(
    payload: ActivityDefinitionPatchSchema,
    request: Request,
    activity_definition: ActivityDefinitionModel = Depends(resolve_activity_definition),
    service: ActivityDefinitionService = Depends(get_activity_definition_service),
):
    updated = await service.patch_activity_definition(activity_definition.activity_definition_id, payload, payload.updated_by)
    if not updated:
        raise HTTPException(status_code=404, detail="ActivityDefinition not found")
    return format_response(service._to_fhir(updated), service._to_plain(updated), request)


@router.get(
    "/",
    operation_id="list_activity_definitions",
    summary="Search ActivityDefinition resources",
    description=(
        "Searches ActivityDefinitions using the FHIR R4 search parameters "
        "(https://www.hl7.org/fhir/R4/plandefinition.html#search): `_id`, `identifier`, `url`, `version`, "
        "`name`, `title`, `publisher`, `description` (string: prefix match by default, `:contains`, `:exact`), "
        "`status`, `topic`, `jurisdiction`, `context` (use-context value), `context-type` (use-context code), "
        "`date`, `effective`, `depends-on`, `derived-from`, "
        "`predecessor`, `successor`, `composed-of` and `_lastUpdated`. "
        "Token params accept `code`, `system|code`, `|code` or `system|`; comma = OR. Date params take an optional "
        "prefix eq|ne|gt|lt|ge|le|sa|eb|ap (repeat for AND). "
        "`org_id` is mandatory on every search (tenant scope) and `user_id` is optional; paginate with `limit` / `offset`. " + _CONTENT_NEG
    ),
    response_description="Paginated ActivityDefinition resources",
    responses={**_LIST_200, **_ERR_VALIDATION},
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
    user_id: Optional[str] = Query(None, description="Optional: restrict to records owned by this user."),
    org_id: str = Query(..., min_length=1, description="Tenant organization id — mandatory scope of every search."),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: ActivityDefinitionService = Depends(get_activity_definition_service),
):
    strings = {}
    for key, mode_values in {
        "name": {"startswith": name, "contains": name_contains, "exact": name_exact},
        "title": {"startswith": title, "contains": title_contains, "exact": title_exact},
        "publisher": {"startswith": publisher, "contains": publisher_contains, "exact": publisher_exact},
        "description": {"startswith": description, "contains": description_contains, "exact": description_exact},
    }.items():
        strings[key] = {m: v for m, v in mode_values.items() if v}
    search = ActivityDefinitionSearch(
        id=id_, identifier=identifier, url=url, version=version, ad_status=ad_status, topic=topic,
        jurisdiction=jurisdiction, context=context, context_type=context_type,
        depends_on=depends_on, derived_from=derived_from, predecessor=predecessor, successor=successor,
        composed_of=composed_of, date=date or [], effective=effective or [], last_updated=last_updated or [],
        strings=strings,
    )
    items, total = await service.list_activity_definitions(
        user_id=user_id, org_id=org_id, search=search, limit=limit, offset=offset)
    return format_paginated_response(
        [service._to_fhir(i) for i in items],
        [service._to_plain(i) for i in items],
        total, limit, offset, request,
    )


@router.delete(
    "/{activity_definition_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_activity_definition",
    summary="Delete a ActivityDefinition resource",
    description=(
        "Permanently deletes the ActivityDefinition and every child record (dosage, participants, lists, ...). "
        "This operation is irreversible. Returns 204 No Content on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_activity_definition(
    activity_definition: ActivityDefinitionModel = Depends(resolve_activity_definition),
    service: ActivityDefinitionService = Depends(get_activity_definition_service),
):
    await service.delete_activity_definition(activity_definition.activity_definition_id)
    return None


@router.post(
    "/{activity_definition_id}/$apply",
    operation_id="apply_activity_definition",
    summary="Apply an ActivityDefinition to a subject — generate one ServiceRequest ($apply)",
    description=(
        "FHIR operation `ActivityDefinition/$apply` "
        "(https://www.hl7.org/fhir/R4/activitydefinition-operation-apply.html). Turns this template into a "
        "ServiceRequest for the `subject` (code, intent, priority, timing and quantity are copied; `practitioner` "
        "becomes the requester; `instantiates_canonical` links back to this definition). Only kind `ServiceRequest` "
        "is generated — any other kind, a retired definition, or one already generated for the same subject/encounter "
        "comes back in `skipped` with the reason. `persist=false` (default) is a preview and saves nothing; "
        "`persist=true` saves the ServiceRequest. Returns plain JSON by default, or a `collection` Bundle with "
        "`Accept: application/fhir+json`."
    ),
    response_description="The generated ServiceRequest, or the reason it was skipped",
    responses={**APPLY_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def apply_activity_definition(
    payload: ActivityDefinitionApplyRequest,
    request: Request,
    activity_definition: ActivityDefinitionModel = Depends(resolve_activity_definition),
    apply_service: DefinitionApplyService = Depends(get_definition_apply_service),
):
    if activity_definition.org_id != payload.org_id:
        raise HTTPException(status_code=404, detail="ActivityDefinition not found")
    result = await apply_service.apply_activity_definition(activity_definition, payload)
    return format_response(apply_service.to_fhir(result), apply_service.to_plain(result), request)
