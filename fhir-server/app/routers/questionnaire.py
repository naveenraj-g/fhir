from datetime import datetime  # noqa: F401
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.core.content_negotiation import format_paginated_response, format_response
from app.core.schema_utils import inline_schema
from app.deps.questionnaire_deps import resolve_questionnaire
from app.di.dependencies.questionnaire import get_questionnaire_service
from app.models.questionnaire.questionnaire import QuestionnaireModel
from app.repository.questionnaire_repository import QuestionnaireSearch
from app.schemas.questionnaire import QuestionnaireCreateSchema, QuestionnairePatchSchema
from app.schemas.questionnaire.response import (
    FHIRQuestionnaireBundle,
    FHIRQuestionnaireSchema,
    PaginatedQuestionnaireResponse,
    PlainQuestionnaireResponse,
)
from app.services.questionnaire_service import QuestionnaireService

router = APIRouter()

_CONTENT_NEG = (
    "Set `Accept: application/fhir+json` to receive the full FHIR R4 representation; "
    "omit or use `Accept: application/json` for the simplified plain-JSON form."
)

_ERR_NOT_FOUND = {404: {"description": "Questionnaire not found"}}
_ERR_VALIDATION = {422: {"description": "Validation error — request body failed schema validation"}}

_SINGLE_200 = {
    200: {
        "content": {
            "application/json": {"schema": inline_schema(PlainQuestionnaireResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRQuestionnaireSchema.model_json_schema())},
        }
    }
}
_SINGLE_201 = {201: _SINGLE_200[200]}
_LIST_200 = {
    200: {
        "description": "Paginated list of questionnaires",
        "content": {
            "application/json": {"schema": inline_schema(PaginatedQuestionnaireResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRQuestionnaireBundle.model_json_schema())},
        },
    }
}


# ── Create Questionnaire ───────────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_questionnaire",
    summary="Create a new Questionnaire resource",
    description=(
        "Defines a structured set of questions (a form). Requires `status`. "
        "The full item tree is submitted in one request: `item[]` nests recursively through `item`, and each item "
        "may carry `code`, `enable_when`, `answer_option` and `initial`. Choice types (`answer[x]`/`value[x]`) are "
        "flat fields — supply exactly one variant (e.g. `answer_coding_*`, `value_string`). "
        "R4 item invariants are enforced (group needs nested items, display cannot, answer_option xor "
        "answer_value_set, ...). `link_id` must be unique across the tree. " + _CONTENT_NEG
    ),
    response_description="The newly created Questionnaire resource",
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_questionnaire(
    payload: QuestionnaireCreateSchema,
    request: Request,
    service: QuestionnaireService = Depends(get_questionnaire_service),
):
    q = await service.create_questionnaire(payload, payload.user_id, payload.org_id, payload.created_by)
    return format_response(service._to_fhir(q), service._to_plain(q), request)


# ── Get Questionnaire ──────────────────────────────────────────────────────────


@router.get(
    "/{questionnaire_id}",
    operation_id="get_questionnaire_by_id",
    summary="Retrieve a Questionnaire resource by public questionnaire_id",
    description="Fetches a single Questionnaire (including its full item tree) by public integer `questionnaire_id`. " + _CONTENT_NEG,
    response_description="The requested Questionnaire resource",
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_questionnaire(
    request: Request,
    q: QuestionnaireModel = Depends(resolve_questionnaire),
    service: QuestionnaireService = Depends(get_questionnaire_service),
):
    return format_response(service._to_fhir(q), service._to_plain(q), request)


# ── Patch Questionnaire ────────────────────────────────────────────────────────


@router.patch(
    "/{questionnaire_id}",
    operation_id="patch_questionnaire",
    summary="Partially update a Questionnaire resource",
    description=(
        "Patchable fields: `url`, `version`, `name`, `title`, `status`, `experimental`, `date`, `publisher`, "
        "`description`, `purpose`, `copyright`, `approval_date`, `last_review_date`, `effective_period_start`, "
        "`effective_period_end`, `derived_from`. "
        "Child lists (identifier, subject_type, contact, use_context, jurisdiction, code) and the item tree (`item`) "
        "are also patchable with REPLACE semantics: a list that is sent replaces the stored list in full, `[]` clears "
        "it, and an omitted list is left untouched. Sending `item` replaces the ENTIRE item tree (it is validated with "
        "the same R4 rules as on create). Consider publishing a new `version` instead of editing a live form. "
        + _CONTENT_NEG
    ),
    response_description="The updated Questionnaire resource",
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_questionnaire(
    payload: QuestionnairePatchSchema,
    request: Request,
    q: QuestionnaireModel = Depends(resolve_questionnaire),
    service: QuestionnaireService = Depends(get_questionnaire_service),
):
    updated = await service.patch_questionnaire(q.questionnaire_id, payload, payload.updated_by)
    if not updated:
        raise HTTPException(status_code=404, detail="Questionnaire not found")
    return format_response(service._to_fhir(updated), service._to_plain(updated), request)


# ── Search Questionnaires ──────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_questionnaires",
    summary="Search Questionnaire resources",
    description=(
        "Searches Questionnaires using the FHIR R4 Questionnaire search parameters "
        "(https://www.hl7.org/fhir/R4/questionnaire.html#search). "
        "String params (`name`, `title`, `publisher`, `description`) are case-insensitive prefix matches; use the "
        "`:contains` and `:exact` variants (e.g. `title:contains`) for substring / exact. "
        "Token params (`status`, `identifier`, `jurisdiction`, `code`, `subject-type`, `context`, `context-type`) "
        "accept `code`, `system|code`, `|code` or `system|`; comma = OR. `code` and `definition` match any item at "
        "any depth. Date params (`date`, `effective`, `_lastUpdated`) take an optional prefix "
        "eq|ne|gt|lt|ge|le|sa|eb|ap; repeat for AND. "
        "`org_id` is mandatory on every search (tenant scope) and `user_id` is optional; paginate with `limit` / `offset`. " + _CONTENT_NEG
    ),
    response_description="Paginated Questionnaire resources",
    responses={**_LIST_200, **_ERR_VALIDATION},
)
async def list_questionnaires(
    request: Request,
    id_: Optional[str] = Query(None, alias="_id", description="Public questionnaire_id(s), comma-separated."),
    identifier: Optional[str] = Query(None, description="Token `[system|]value` of Questionnaire.identifier."),
    url: Optional[str] = Query(None, description="Canonical url (exact)."),
    version: Optional[str] = Query(None, description="Business version (exact)."),
    q_status: Optional[str] = Query(None, alias="status", description="Token: draft|active|retired|unknown (comma = OR)."),
    name: Optional[str] = Query(None, description="Computer-friendly name (starts with, case-insensitive)."),
    name_contains: Optional[str] = Query(None, alias="name:contains", description="Name contains (case-insensitive)."),
    name_exact: Optional[str] = Query(None, alias="name:exact", description="Name exact match."),
    title: Optional[str] = Query(None, description="Title (starts with, case-insensitive)."),
    title_contains: Optional[str] = Query(None, alias="title:contains", description="Title contains (case-insensitive)."),
    title_exact: Optional[str] = Query(None, alias="title:exact", description="Title exact match."),
    publisher: Optional[str] = Query(None, description="Publisher (starts with, case-insensitive)."),
    publisher_contains: Optional[str] = Query(None, alias="publisher:contains", description="Publisher contains."),
    publisher_exact: Optional[str] = Query(None, alias="publisher:exact", description="Publisher exact match."),
    description: Optional[str] = Query(None, description="Description (starts with, case-insensitive)."),
    description_contains: Optional[str] = Query(None, alias="description:contains", description="Description contains."),
    description_exact: Optional[str] = Query(None, alias="description:exact", description="Description exact match."),
    date: Optional[List[str]] = Query(None, description="Date last changed, with optional prefix e.g. `ge2024-01-01`."),
    effective: Optional[List[str]] = Query(None, description="effectivePeriod with optional prefix."),
    jurisdiction: Optional[str] = Query(None, description="Token `[system|]code` of Questionnaire.jurisdiction."),
    code: Optional[str] = Query(None, description="Token `[system|]code` matching any item.code (or questionnaire code)."),
    definition: Optional[str] = Query(None, description="item.definition URI (exact)."),
    subject_type: Optional[str] = Query(None, alias="subject-type", description="Resource type that can be the subject, e.g. `Patient`."),
    context: Optional[str] = Query(None, description="Token of useContext.valueCodeableConcept."),
    context_type: Optional[str] = Query(None, alias="context-type", description="Token of useContext.code, e.g. `gender`."),
    last_updated: Optional[List[str]] = Query(None, alias="_lastUpdated", description="Last-updated instant with optional prefix."),
    user_id: Optional[str] = Query(None, description="Optional: restrict to records owned by this user."),
    org_id: str = Query(..., min_length=1, description="Tenant organization id — mandatory scope of every search."),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: QuestionnaireService = Depends(get_questionnaire_service),
):
    # Collect the string params + their :contains/:exact modifiers.
    raw = {
        "name": (name, name_contains, name_exact),
        "title": (title, title_contains, title_exact),
        "publisher": (publisher, publisher_contains, publisher_exact),
        "description": (description, description_contains, description_exact),
    }
    strings = {}
    for key, (starts, contains, exact) in raw.items():
        modes = {m: v for m, v in (("startswith", starts), ("contains", contains), ("exact", exact)) if v}
        if modes:
            strings[key] = modes

    search = QuestionnaireSearch(
        id=id_, identifier=identifier, url=url, version=version, q_status=q_status,
        date=date or [], effective=effective or [], jurisdiction=jurisdiction, code=code,
        definition=definition, subject_type=subject_type, context=context, context_type=context_type,
        last_updated=last_updated or [], strings=strings,
    )
    items, total = await service.list_questionnaires(
        user_id=user_id, org_id=org_id, search=search, limit=limit, offset=offset,
    )
    return format_paginated_response(
        [service._to_fhir(i) for i in items],
        [service._to_plain(i) for i in items],
        total, limit, offset, request,
    )


# ── Delete Questionnaire ───────────────────────────────────────────────────────


@router.delete(
    "/{questionnaire_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_questionnaire",
    summary="Delete a Questionnaire resource",
    description=(
        "Permanently deletes the Questionnaire and all its child records (identifiers, subject types, contacts, "
        "use contexts, jurisdictions, codes and the entire item tree with enableWhen / answerOption / initial). "
        "This operation is irreversible. Returns 204 No Content on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_questionnaire(
    q: QuestionnaireModel = Depends(resolve_questionnaire),
    service: QuestionnaireService = Depends(get_questionnaire_service),
):
    await service.delete_questionnaire(q.questionnaire_id)
    return None
