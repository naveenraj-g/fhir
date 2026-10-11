"""
FastAPI router for QuestionnaireResponse resources.

Endpoints:
  POST   /questionnaire-responses/        — record answers with the full item tree in the body
  GET    /questionnaire-responses/{id}    — fetch a single QuestionnaireResponse (whole tree)
  GET    /questionnaire-responses/        — paginated FHIR R4 search (status, patient, author, authored, ...)
  PATCH  /questionnaire-responses/{id}    — partial update (scalar + reference fields only)
  DELETE /questionnaire-responses/{id}    — permanent delete (cascades to the whole item tree)

All routes support content negotiation:
  - `Accept: application/json`      → plain snake_case JSON (default)
  - `Accept: application/fhir+json` → FHIR R4 resource / Bundle

RBAC is enforced via require_permission() for the ("questionnaire_response", <action>) pair.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response, get_accept_header
from app.core.schema_utils import inline_schema
from app.di.dependencies.questionnaire_response import get_questionnaire_response_service
from app.schemas.questionnaire_response.input import (
    ListQuestionnaireResponsesSchema,
    QuestionnaireResponseCreateSchema,
    QuestionnaireResponsePatchSchema,
)
from app.schemas.questionnaire_response.response import (
    FhirBundleResponse,
    FhirQuestionnaireResponse,
    PaginatedQuestionnaireResponseResponse,
    QuestionnaireResponseRecord,
)
from app.services.questionnaire_response_service import QuestionnaireResponseService

# All routes are prefixed with /questionnaire-responses; tagged for Swagger grouping.
router = APIRouter(prefix="/questionnaire-responses", tags=["QuestionnaireResponses"])

# ── Shared error response descriptors ────────────────────────────────────────

_ERR_NOT_FOUND = {404: {"description": "QuestionnaireResponse not found"}}
_ERR_VALIDATION = {422: {"description": "Validation error — request body or query params failed schema validation"}}

# ── Shared success response descriptors ──────────────────────────────────────
# inline_schema() resolves Pydantic's $defs/$ref pointers (and breaks recursion) so
# both content types render in Swagger UI without resolver errors.

_SINGLE_201 = {
    201: {
        "description": "QuestionnaireResponse created successfully",
        "content": {
            "application/json": {"schema": inline_schema(QuestionnaireResponseRecord.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FhirQuestionnaireResponse.model_json_schema())},
        },
    }
}

_SINGLE_200 = {
    200: {
        "description": "QuestionnaireResponse retrieved or updated successfully",
        "content": {
            "application/json": {"schema": inline_schema(QuestionnaireResponseRecord.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FhirQuestionnaireResponse.model_json_schema())},
        },
    }
}

_LIST_200 = {
    200: {
        "description": "Paginated list of QuestionnaireResponse resources",
        "content": {
            "application/json": {"schema": inline_schema(PaginatedQuestionnaireResponseResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FhirBundleResponse.model_json_schema())},
        },
    }
}


# ── POST /questionnaire-responses/ ───────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_questionnaire_response",
    summary="Create a QuestionnaireResponse",
    description=(
        "Records a set of answers to a Questionnaire. `status` is required; `questionnaire` is the canonical URL "
        "(or `Questionnaire/<id>`) of the form being answered. The full item tree is submitted in one request: "
        "`item[]` nests recursively through `item`, and each `answer` carries at most one value "
        "(`value_boolean|decimal|integer|date|datetime|time|string|uri|coding|quantity|reference|attachment`) and "
        "may itself contain nested `item[]`. "
        "References (`subject`, `encounter`, `author`, `source`, `based_on`, `part_of`) are `Type/id` strings — "
        "only their format is validated, never whether the target exists. "
        "Send `Accept: application/fhir+json` to receive the result in FHIR R4 format."
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
    dependencies=[Depends(require_permission("questionnaire_response", "create"))],
)
async def create_questionnaire_response(
    dto: QuestionnaireResponseCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("questionnaire_response", "create")),
    service: QuestionnaireResponseService = Depends(get_questionnaire_response_service),
) -> JSONResponse:
    """Record a new QuestionnaireResponse and return the persisted record."""
    data = await service.create(dto, actor, accept=get_accept_header(request))
    return format_response(data, request)


# ── GET /questionnaire-responses/{resource_id} ───────────────────────────────


@router.get(
    "/{resource_id}",
    operation_id="get_questionnaire_response",
    summary="Get a QuestionnaireResponse by ID",
    description=(
        "Fetch a single QuestionnaireResponse (including its whole item tree) by its public integer ID. "
        "Send `Accept: application/fhir+json` for FHIR R4 format."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
    dependencies=[Depends(require_permission("questionnaire_response", "read"))],
)
async def get_questionnaire_response(
    resource_id: int,
    request: Request,
    actor: AuthUser = Depends(require_permission("questionnaire_response", "read")),
    service: QuestionnaireResponseService = Depends(get_questionnaire_response_service),
) -> JSONResponse:
    """Fetch a single QuestionnaireResponse by its public ID."""
    data = await service.get_by_id(resource_id, actor, accept=get_accept_header(request))
    return format_response(data, request)


# ── GET /questionnaire-responses/ ────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_questionnaire_responses",
    summary="Search QuestionnaireResponses",
    description=(
        "Searches QuestionnaireResponses using the FHIR R4 search parameters "
        "(https://www.hl7.org/fhir/R4/questionnaireresponse.html#search). "
        "Token params (`status`, `identifier`) accept `code`, `system|code`, `|code` or `system|`; comma = OR. "
        "Reference params (`subject`, `patient`, `encounter`, `author`, `source`, `based-on`, `part-of`) accept "
        "`Type/id` or a bare numeric id. `questionnaire` matches the stored canonical URL or `Questionnaire/<id>`. "
        "Date params (`authored`, `_lastUpdated`) take an optional prefix eq|ne|gt|lt|ge|le|sa|eb|ap; repeat for "
        "AND (e.g. `authored=ge2024-01-01&authored=lt2024-02-01`). "
        "`org_id` is mandatory on every search (tenant scope) and `user_id` is optional; paginate with `limit` / `offset`. "
        "Send `Accept: application/fhir+json` to receive a FHIR Bundle searchset."
    ),
    responses={**_LIST_200, **_ERR_VALIDATION},
    dependencies=[Depends(require_permission("questionnaire_response", "read"))],
)
async def list_questionnaire_responses(
    request: Request,
    id_: Optional[str] = Query(None, alias="_id", description="Public questionnaire_response_id(s), comma-separated."),
    identifier: Optional[str] = Query(None, description="Token `[system|]value` of QuestionnaireResponse.identifier."),
    questionnaire: Optional[str] = Query(None, description="Canonical URL, or `Questionnaire/<id>`, of the answered Questionnaire."),
    qr_status: Optional[str] = Query(
        None, alias="status",
        description="Token: in-progress|completed|amended|entered-in-error|stopped (comma = OR).",
    ),
    subject: Optional[str] = Query(None, description="Subject reference (any type), e.g. `Patient/10001`."),
    patient: Optional[str] = Query(None, description="Subject patient reference: `Patient/10001` or `10001`."),
    encounter: Optional[str] = Query(None, description="Encounter reference: `Encounter/20001` or `20001`."),
    author: Optional[str] = Query(None, description="Author reference: Device|Practitioner|PractitionerRole|Patient|RelatedPerson|Organization."),
    source: Optional[str] = Query(None, description="Source reference: Patient|Practitioner|PractitionerRole|RelatedPerson."),
    based_on: Optional[str] = Query(None, alias="based-on", description="basedOn reference: CarePlan|ServiceRequest."),
    part_of: Optional[str] = Query(None, alias="part-of", description="partOf reference: Observation|Procedure."),
    authored: Optional[List[str]] = Query(None, description="Authored date with optional prefix, e.g. `ge2024-01-01`. Repeat for AND."),
    last_updated: Optional[List[str]] = Query(None, alias="_lastUpdated", description="Last-updated instant with optional prefix. Repeat for AND."),
    user_id: Optional[str] = Query(None, description="Optional: restrict to records owned by this user (JWT subject)."),
    org_id: str = Query(..., min_length=1, description="Tenant organization ID — mandatory scope of every search."),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    actor: AuthUser = Depends(require_permission("questionnaire_response", "read")),
    service: QuestionnaireResponseService = Depends(get_questionnaire_response_service),
) -> JSONResponse:
    """
    Search QuestionnaireResponses with FHIR R4 search parameters.

    Parameters are declared explicitly (with aliases) because several FHIR names
    are hyphenated or underscore-prefixed. They are gathered into
    ListQuestionnaireResponsesSchema, whose validators (e.g. the status code
    check) run here; a failure is surfaced as a 422, not a 500.
    """
    try:
        filters = ListQuestionnaireResponsesSchema(
            id=id_, identifier=identifier, questionnaire=questionnaire, status=qr_status,
            subject=subject, patient=patient, encounter=encounter, author=author, source=source,
            based_on=based_on, part_of=part_of, authored=authored, last_updated=last_updated,
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


# ── PATCH /questionnaire-responses/{resource_id} ─────────────────────────────


@router.patch(
    "/{resource_id}",
    operation_id="update_questionnaire_response",
    summary="Partially update a QuestionnaireResponse",
    description=(
        "Update scalar and reference fields on a QuestionnaireResponse. At least one field must be provided. "
        "Patchable fields: `status`, `questionnaire`, `authored`, and the references `subject`, `encounter`, "
        "`author`, `source` (as `Type/id`) with their `*_display`. "
        "The child lists `based_on`, `part_of` and the item/answer tree `item` are also patchable with REPLACE "
        "semantics: a list that is sent replaces the stored list in full, `[]` clears it, an omitted list is left "
        "untouched. To correct answers send the corrected `item` tree (and typically `status: amended`). "
        "Send `Accept: application/fhir+json` for FHIR R4 format."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
    dependencies=[Depends(require_permission("questionnaire_response", "update"))],
)
async def update_questionnaire_response(
    resource_id: int,
    dto: QuestionnaireResponsePatchSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("questionnaire_response", "update")),
    service: QuestionnaireResponseService = Depends(get_questionnaire_response_service),
) -> JSONResponse:
    """Partially update a QuestionnaireResponse. Returns 422 if the body is empty."""
    data = await service.update(resource_id, dto, actor, accept=get_accept_header(request))
    return format_response(data, request)


# ── DELETE /questionnaire-responses/{resource_id} ────────────────────────────


@router.delete(
    "/{resource_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_questionnaire_response",
    summary="Delete a QuestionnaireResponse",
    description=(
        "Permanently deletes the QuestionnaireResponse and all its child records (basedOn, partOf, and the "
        "entire item/answer tree). This operation is irreversible. Returns 204 No Content on success."
    ),
    responses={**_ERR_NOT_FOUND},
    dependencies=[Depends(require_permission("questionnaire_response", "delete"))],
)
async def delete_questionnaire_response(
    resource_id: int,
    actor: AuthUser = Depends(require_permission("questionnaire_response", "delete")),
    service: QuestionnaireResponseService = Depends(get_questionnaire_response_service),
) -> None:
    """Permanently delete a QuestionnaireResponse and cascade to all child records."""
    await service.delete(resource_id, actor)
