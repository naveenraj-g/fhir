"""
FastAPI router for CarePlan resources.

Endpoints:
  POST   /care-plans/       — create a CarePlan (activities, goals, care team, notes, ...)
  GET    /care-plans/{id}   — fetch a single CarePlan by public ID
  GET    /care-plans/       — paginated FHIR R4 search (patient, status, category, activity-code, ...)
  PATCH  /care-plans/{id}   — partial update; every child list is replaced when sent
  DELETE /care-plans/{id}   — permanent delete (cascades to all child records)

All routes support content negotiation:
  - `Accept: application/json`      → plain snake_case JSON (default)
  - `Accept: application/fhir+json` → FHIR R4 resource / Bundle

RBAC is enforced via require_permission() for the ("care_plan", <action>) pair.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response, get_accept_header
from app.core.schema_utils import inline_schema
from app.di.dependencies.care_plan import get_care_plan_service
from app.schemas.care_plan.input import CarePlanCreateSchema, CarePlanPatchSchema, ListCarePlansSchema
from app.schemas.care_plan.response import FHIRCarePlanBundle, FHIRCarePlanSchema, PlainCarePlanResponse, PaginatedCarePlanResponse
from app.services.care_plan_service import CarePlanService

# All routes are prefixed with /care-plans; tagged for Swagger grouping.
router = APIRouter(prefix="/care-plans", tags=["CarePlans"])

# ── Shared error response descriptors ────────────────────────────────────────

_ERR_NOT_FOUND = {404: {"description": "CarePlan not found"}}
_ERR_VALIDATION = {422: {"description": "Validation error — request body or query params failed validation"}}

# ── Shared success response descriptors ──────────────────────────────────────
# inline_schema() resolves Pydantic's $defs/$ref pointers so both content types
# render in Swagger UI without resolver errors.

_SINGLE_201 = {
    201: {
        "description": "CarePlan created successfully",
        "content": {
            "application/json": {"schema": inline_schema(PlainCarePlanResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRCarePlanSchema.model_json_schema())},
        },
    }
}

_SINGLE_200 = {
    200: {
        "description": "CarePlan retrieved or updated successfully",
        "content": {
            "application/json": {"schema": inline_schema(PlainCarePlanResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRCarePlanSchema.model_json_schema())},
        },
    }
}

_LIST_200 = {
    200: {
        "description": "Paginated list of CarePlan resources",
        "content": {
            "application/json": {"schema": inline_schema(PaginatedCarePlanResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRCarePlanBundle.model_json_schema())},
        },
    }
}


# ── POST /care-plans/ ─────────────────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_care_plan",
    summary="Create a CarePlan",
    description=(
        "Creates a CarePlan. Required: `status`, `intent` and `subject` (Patient|Group reference, e.g. "
        "`'Patient/10001'`). Optional: `title`, `description`, `encounter`, `period_*`, `created`, `author`, "
        "`instantiates_canonical` / `instantiates_uri` (comma-separated) and the child lists `identifiers`, "
        "`based_on`, `replaces`, `part_of`, `categories`, `contributors`, `care_teams`, `addresses`, "
        "`supporting_info`, `goals`, `activities` (each with its outcome / progress / detail lists) and `notes`. "
        "An activity carries either a `reference` or `detail_*` fields, never both (cpl-3); `detail_status` is "
        "required whenever detail is supplied; `scheduled[x]` and `product[x]` allow one variant. References are "
        "`Type/id` strings — only their format is validated. Send `Accept: application/fhir+json` to receive the "
        "result in FHIR R4 format."
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
    dependencies=[Depends(require_permission("care_plan", "create"))],
)
async def create_care_plan(
    dto: CarePlanCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("care_plan", "create")),
    service: CarePlanService = Depends(get_care_plan_service),
) -> JSONResponse:
    """Raise a new CarePlan and return the persisted record."""
    data = await service.create(dto, actor, accept=get_accept_header(request))
    return format_response(data, request)


# ── GET /care-plans/{resource_id} ─────────────────────────────────────────────────


@router.get(
    "/{resource_id}",
    operation_id="get_care_plan",
    summary="Get a CarePlan by ID",
    description=(
        "Fetch a single CarePlan by its public integer ID. Send `Accept: application/fhir+json` for FHIR R4 format."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
    dependencies=[Depends(require_permission("care_plan", "read"))],
)
async def get_care_plan(
    resource_id: int,
    request: Request,
    actor: AuthUser = Depends(require_permission("care_plan", "read")),
    service: CarePlanService = Depends(get_care_plan_service),
) -> JSONResponse:
    """Fetch a single CarePlan by its public ID."""
    data = await service.get_by_id(resource_id, actor, accept=get_accept_header(request))
    return format_response(data, request)


# ── GET /care-plans/ ──────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_care_plans",
    summary="Search CarePlans",
    description=(
        "Searches CarePlans using the FHIR R4 CarePlan search parameters "
        "(https://www.hl7.org/fhir/R4/careplan.html#search): `activity-code`, `activity-date`, `activity-reference`, "
        "`based-on`, `care-team`, `category`, `condition`, `date`, `encounter`, `goal`, `identifier`, "
        "`instantiates-canonical`, `instantiates-uri`, `intent`, `part-of`, `patient`, `performer`, `replaces`, "
        "`status`, `subject` — plus `_id` and `_lastUpdated`. Token params accept `code`, `system|code`, `|code` or "
        "`system|`; comma = OR. Reference params accept `Type/id` or a bare numeric id. Date params take an optional "
        "prefix eq|ne|gt|lt|ge|le|sa|eb|ap (repeat for AND). "
        "`org_id` is mandatory on every search (tenant scope) and `user_id` is optional; paginate with `limit` / `offset`. "
        "Send `Accept: application/fhir+json` to receive a FHIR Bundle searchset."
    ),
    responses={**_LIST_200, **_ERR_VALIDATION},
    dependencies=[Depends(require_permission("care_plan", "read"))],
)
async def list_care_plans(
    request: Request,
    id_: Optional[str] = Query(None, alias="_id", description="Public care_plan_id(s), comma-separated."),
    identifier: Optional[str] = Query(None, description="Token `[system|]value` of CarePlan.identifier."),
    cp_status: Optional[str] = Query(None, alias="status", description="Token: draft|active|on-hold|revoked|completed|entered-in-error|unknown (comma = OR)."),
    intent: Optional[str] = Query(None, description="Token: proposal|plan|order|option (comma = OR)."),
    category: Optional[str] = Query(None, description="Token `[system|]code` of CarePlan.category."),
    activity_code: Optional[str] = Query(None, alias="activity-code", description="Token `[system|]code` of activity.detail.code."),
    activity_reference: Optional[str] = Query(None, alias="activity-reference", description="activity.reference, e.g. `ServiceRequest/80001`."),
    based_on: Optional[str] = Query(None, alias="based-on", description="CarePlan reference, e.g. `CarePlan/290001`."),
    replaces: Optional[str] = Query(None, description="CarePlan reference."),
    part_of: Optional[str] = Query(None, alias="part-of", description="CarePlan reference."),
    care_team: Optional[str] = Query(None, alias="care-team", description="CareTeam reference."),
    condition: Optional[str] = Query(None, description="Condition reference (CarePlan.addresses), e.g. `Condition/120001`."),
    goal: Optional[str] = Query(None, description="Goal reference."),
    encounter: Optional[str] = Query(None, description="Encounter reference: `Encounter/20001` or `20001`."),
    subject: Optional[str] = Query(None, description="Subject reference (Patient|Group), e.g. `Patient/10001`."),
    patient: Optional[str] = Query(None, description="Subject patient reference: `Patient/10001` or `10001`."),
    performer: Optional[str] = Query(None, description="activity.detail.performer reference."),
    instantiates_canonical: Optional[str] = Query(None, alias="instantiates-canonical", description="Canonical URL or `PlanDefinition/1`-style suffix."),
    instantiates_uri: Optional[str] = Query(None, alias="instantiates-uri", description="URI instantiated by the plan."),
    date: Optional[List[str]] = Query(None, description="Plan period with optional prefix, e.g. `ge2024-01-01`. Repeat for AND."),
    activity_date: Optional[List[str]] = Query(None, alias="activity-date", description="Activity scheduled period with optional prefix. Repeat for AND."),
    last_updated: Optional[List[str]] = Query(None, alias="_lastUpdated", description="Last-updated instant with optional prefix."),
    user_id: Optional[str] = Query(None, description="Optional: restrict to records owned by this user (JWT subject)."),
    org_id: str = Query(..., min_length=1, description="Tenant organization ID — mandatory scope of every search."),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    actor: AuthUser = Depends(require_permission("care_plan", "read")),
    service: CarePlanService = Depends(get_care_plan_service),
) -> JSONResponse:
    """
    Search CarePlans with FHIR R4 search parameters.

    Parameters are declared explicitly (with aliases) because `_id` and `_lastUpdated`
    are not valid Python identifiers. They are gathered into ListCarePlansSchema, whose
    validators (e.g. the status code check) run here; a failure is surfaced as a 422.
    """
    try:
        filters = ListCarePlansSchema(
            id=id_, identifier=identifier, status=cp_status, intent=intent, category=category,
            activity_code=activity_code, activity_reference=activity_reference, based_on=based_on,
            replaces=replaces, part_of=part_of, care_team=care_team, condition=condition, goal=goal,
            encounter=encounter, subject=subject, patient=patient, performer=performer,
            instantiates_canonical=instantiates_canonical, instantiates_uri=instantiates_uri, date=date,
            activity_date=activity_date, last_updated=last_updated, user_id=user_id, org_id=org_id,
            limit=limit, offset=offset,
        )
    except ValidationError as exc:
        # include_context=False keeps the detail JSON-serialisable (ctx can hold exceptions).
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.errors(include_url=False, include_context=False),
        ) from exc
    data = await service.list(filters, actor, accept=get_accept_header(request))
    return format_paginated_response(data, request)


# ── PATCH /care-plans/{resource_id} ───────────────────────────────────────────────


@router.patch(
    "/{resource_id}",
    operation_id="update_care_plan",
    summary="Partially update a CarePlan",
    description=(
        "Update fields on a CarePlan. At least one field must be provided (`status`, `intent` and `subject` cannot "
        "be null). The child lists `identifiers`, `based_on`, `replaces`, `part_of`, `categories`, `contributors`, "
        "`care_teams`, `addresses`, `supporting_info`, `goals`, `activities` and `notes` use REPLACE semantics: a list "
        "that is sent replaces the stored list in full, `[]` clears it, and an omitted list is left untouched. "
        "Send `Accept: application/fhir+json` for FHIR R4 format."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
    dependencies=[Depends(require_permission("care_plan", "update"))],
)
async def update_care_plan(
    resource_id: int,
    dto: CarePlanPatchSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("care_plan", "update")),
    service: CarePlanService = Depends(get_care_plan_service),
) -> JSONResponse:
    """Partially update a CarePlan. Returns 422 if the body is empty."""
    data = await service.update(resource_id, dto, actor, accept=get_accept_header(request))
    return format_response(data, request)


# ── DELETE /care-plans/{resource_id} ──────────────────────────────────────────────


@router.delete(
    "/{resource_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_care_plan",
    summary="Delete a CarePlan",
    description=(
        "Permanently deletes the CarePlan and its child records (identifier, category). "
        "This operation is irreversible. Returns 204 No Content on success."
    ),
    responses={**_ERR_NOT_FOUND},
    dependencies=[Depends(require_permission("care_plan", "delete"))],
)
async def delete_care_plan(
    resource_id: int,
    actor: AuthUser = Depends(require_permission("care_plan", "delete")),
    service: CarePlanService = Depends(get_care_plan_service),
) -> None:
    """Permanently delete a CarePlan and cascade to its child records."""
    await service.delete(resource_id, actor)
