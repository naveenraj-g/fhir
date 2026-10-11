"""
FastAPI router for Questionnaire resources.

Endpoints:
  POST   /questionnaires/        — create with the full item tree in the body
  GET    /questionnaires/{id}    — fetch a single Questionnaire (whole tree) by public ID
  GET    /questionnaires/        — paginated FHIR R4 search (status, name, code, date, ...)
  PATCH  /questionnaires/{id}    — partial update (scalar metadata fields only)
  DELETE /questionnaires/{id}    — permanent delete (cascades to the whole item tree)

All routes support content negotiation:
  - `Accept: application/json`      → plain snake_case JSON (default)
  - `Accept: application/fhir+json` → FHIR R4 resource / Bundle

RBAC is enforced via require_permission() for the ("questionnaire", <action>) pair.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response, get_accept_header
from app.core.schema_utils import inline_schema
from app.di.dependencies.questionnaire import get_questionnaire_service
from app.schemas.questionnaire.input import (
    ListQuestionnairesSchema,
    QuestionnaireCreateSchema,
    QuestionnairePatchSchema,
)
from app.schemas.questionnaire.response import (
    FhirBundleResponse,
    FhirQuestionnaireResponse,
    PaginatedQuestionnaireResponse,
    QuestionnaireDefinitionResponse,
)
from app.services.questionnaire_service import QuestionnaireService

# All questionnaire routes are prefixed with /questionnaires; tagged for Swagger grouping.
router = APIRouter(prefix="/questionnaires", tags=["Questionnaires"])

# ── Shared error response descriptors ────────────────────────────────────────

_ERR_NOT_FOUND = {404: {"description": "Questionnaire not found"}}
_ERR_VALIDATION = {422: {"description": "Validation error — request body or query params failed schema validation"}}

# ── Shared success response descriptors ──────────────────────────────────────
# inline_schema() resolves Pydantic's $defs/$ref pointers so both content types
# render in Swagger UI without resolver errors.

_SINGLE_201 = {
    201: {
        "description": "Questionnaire created successfully",
        "content": {
            "application/json": {"schema": inline_schema(QuestionnaireDefinitionResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FhirQuestionnaireResponse.model_json_schema())},
        },
    }
}

_SINGLE_200 = {
    200: {
        "description": "Questionnaire retrieved or updated successfully",
        "content": {
            "application/json": {"schema": inline_schema(QuestionnaireDefinitionResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FhirQuestionnaireResponse.model_json_schema())},
        },
    }
}

_LIST_200 = {
    200: {
        "description": "Paginated list of Questionnaire resources",
        "content": {
            "application/json": {"schema": inline_schema(PaginatedQuestionnaireResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FhirBundleResponse.model_json_schema())},
        },
    }
}


# ── POST /questionnaires/ ────────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_questionnaire",
    summary="Create a Questionnaire",
    description=(
        "Defines a structured set of questions (a form). `status` is required. "
        "The full item tree is submitted in one request: `item[]` nests recursively through `item`, and each "
        "item may carry `code`, `enable_when`, `answer_option` and `initial`. Choice types (`answer[x]` / "
        "`value[x]`) are flat fields — supply exactly one variant (e.g. `answer_coding_*`, `value_string`). "
        "R4 item invariants are enforced: a group needs nested items, display items cannot have items/code, "
        "`answer_option` and `answer_value_set` are mutually exclusive, and so on. `link_id` must be unique "
        "across the whole tree. "
        "Send `Accept: application/fhir+json` to receive the result in FHIR R4 format."
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
    dependencies=[Depends(require_permission("questionnaire", "create"))],
)
async def create_questionnaire(
    dto: QuestionnaireCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("questionnaire", "create")),
    service: QuestionnaireService = Depends(get_questionnaire_service),
) -> JSONResponse:
    """Create a new Questionnaire and return the persisted record."""
    data = await service.create(dto, actor, accept=get_accept_header(request))
    return format_response(data, request)


# ── GET /questionnaires/{resource_id} ────────────────────────────────────────


@router.get(
    "/{resource_id}",
    operation_id="get_questionnaire",
    summary="Get a Questionnaire by ID",
    description=(
        "Fetch a single Questionnaire (including its whole item tree) by its public integer ID. "
        "Send `Accept: application/fhir+json` for FHIR R4 format."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
    dependencies=[Depends(require_permission("questionnaire", "read"))],
)
async def get_questionnaire(
    resource_id: int,
    request: Request,
    actor: AuthUser = Depends(require_permission("questionnaire", "read")),
    service: QuestionnaireService = Depends(get_questionnaire_service),
) -> JSONResponse:
    """Fetch a single Questionnaire by its public ID."""
    data = await service.get_by_id(resource_id, actor, accept=get_accept_header(request))
    return format_response(data, request)


# ── GET /questionnaires/ ─────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_questionnaires",
    summary="Search Questionnaires",
    description=(
        "Searches Questionnaires using the FHIR R4 Questionnaire search parameters "
        "(https://www.hl7.org/fhir/R4/questionnaire.html#search). "
        "String params (`name`, `title`, `publisher`, `description`) are case-insensitive prefix matches; use the "
        "`:contains` and `:exact` variants (e.g. `title:contains`) for substring / exact. "
        "Token params (`status`, `identifier`, `jurisdiction`, `code`, `subject-type`, `context`, "
        "`context-type`) accept `code`, `system|code`, `|code` or `system|`; comma = OR. `code` and `definition` "
        "match any item at any depth. Date params (`date`, `effective`, `_lastUpdated`) take an optional prefix "
        "eq|ne|gt|lt|ge|le|sa|eb|ap; repeat for AND. "
        "`org_id` is mandatory on every search (tenant scope) and `user_id` is optional; paginate with `limit` / `offset`. "
        "Send `Accept: application/fhir+json` to receive a FHIR Bundle searchset."
    ),
    responses={**_LIST_200, **_ERR_VALIDATION},
    dependencies=[Depends(require_permission("questionnaire", "read"))],
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
    user_id: Optional[str] = Query(None, description="Optional: restrict to records owned by this user (JWT subject)."),
    org_id: str = Query(..., min_length=1, description="Tenant organization ID — mandatory scope of every search."),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    actor: AuthUser = Depends(require_permission("questionnaire", "read")),
    service: QuestionnaireService = Depends(get_questionnaire_service),
) -> JSONResponse:
    """
    Search Questionnaires with FHIR R4 search parameters.

    Parameters are declared explicitly (with aliases) because several FHIR names
    are hyphenated, underscore-prefixed or carry `:contains`/`:exact` modifiers.
    They are gathered into ListQuestionnairesSchema, whose validators (e.g. the
    status code check) run here; a failure is surfaced as a 422, not a 500.
    """
    try:
        filters = ListQuestionnairesSchema(
            id=id_, identifier=identifier, url=url, version=version, status=q_status,
            name=name, name_contains=name_contains, name_exact=name_exact,
            title=title, title_contains=title_contains, title_exact=title_exact,
            publisher=publisher, publisher_contains=publisher_contains, publisher_exact=publisher_exact,
            description=description, description_contains=description_contains, description_exact=description_exact,
            date=date, effective=effective, jurisdiction=jurisdiction, code=code, definition=definition,
            subject_type=subject_type, context=context, context_type=context_type, last_updated=last_updated,
            user_id=user_id, org_id=org_id, limit=limit, offset=offset,
        )
    except ValidationError as exc:
        # include_context=False keeps the detail JSON-serialisable (ctx can hold exceptions).
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.errors(include_url=False, include_context=False),
        ) from exc
    data = await service.list(filters, actor, accept=get_accept_header(request))
    return format_paginated_response(data, request)


# ── PATCH /questionnaires/{resource_id} ──────────────────────────────────────


@router.patch(
    "/{resource_id}",
    operation_id="update_questionnaire",
    summary="Partially update a Questionnaire",
    description=(
        "Update specific scalar metadata fields on a Questionnaire. At least one field must be provided. "
        "Patchable fields: `url`, `version`, `name`, `title`, `status`, `experimental`, `date`, `publisher`, "
        "`description`, `purpose`, `copyright`, `approval_date`, `last_review_date`, `effective_period_start`, "
        "`effective_period_end`, `derived_from`. "
        "Child lists (identifier, subject_type, contact, use_context, jurisdiction, code) and the item tree "
        "(`item`) are also patchable with REPLACE semantics: a list that is sent replaces the stored list in full, "
        "`[]` clears it, and an omitted list is left untouched. Sending `item` replaces the ENTIRE item tree "
        "(validated with the same R4 rules as on create); consider publishing a new `version` instead of editing a "
        "live form. "
        "Send `Accept: application/fhir+json` for FHIR R4 format."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
    dependencies=[Depends(require_permission("questionnaire", "update"))],
)
async def update_questionnaire(
    resource_id: int,
    dto: QuestionnairePatchSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("questionnaire", "update")),
    service: QuestionnaireService = Depends(get_questionnaire_service),
) -> JSONResponse:
    """Partially update a Questionnaire. Returns 422 if the body is empty."""
    data = await service.update(resource_id, dto, actor, accept=get_accept_header(request))
    return format_response(data, request)


# ── DELETE /questionnaires/{resource_id} ─────────────────────────────────────


@router.delete(
    "/{resource_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_questionnaire",
    summary="Delete a Questionnaire",
    description=(
        "Permanently deletes the Questionnaire and all its child records (identifiers, subject types, contacts, "
        "use contexts, jurisdictions, codes and the entire item tree with enableWhen / answerOption / initial). "
        "This operation is irreversible. Returns 204 No Content on success."
    ),
    responses={**_ERR_NOT_FOUND},
    dependencies=[Depends(require_permission("questionnaire", "delete"))],
)
async def delete_questionnaire(
    resource_id: int,
    actor: AuthUser = Depends(require_permission("questionnaire", "delete")),
    service: QuestionnaireService = Depends(get_questionnaire_service),
) -> None:
    """Permanently delete a Questionnaire and cascade to all child records."""
    await service.delete(resource_id, actor)
