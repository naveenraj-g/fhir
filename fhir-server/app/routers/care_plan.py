from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Request, status

from app.deps.care_plan_deps import resolve_care_plan
from app.core.content_negotiation import format_paginated_response, format_response
from app.core.schema_utils import inline_schema
from app.di.dependencies.care_plan import get_care_plan_service
from app.models.care_plan.care_plan import CarePlanModel
from app.repository.care_plan_repository import CarePlanSearch
from app.schemas.care_plan.input import CarePlanCreateSchema, CarePlanPatchSchema
from app.schemas.care_plan.response import (
    FHIRCarePlanBundle,
    FHIRCarePlanSchema,
    PaginatedCarePlanResponse,
    PlainCarePlanResponse,
)
from app.services.care_plan_service import CarePlanService

router = APIRouter()

_CONTENT_NEG = (
    "Set `Accept: application/fhir+json` to receive the full FHIR R4 representation; "
    "omit or use `Accept: application/json` for the simplified plain-JSON form."
)

_ERR_NOT_FOUND = {404: {"description": "CarePlan not found"}}
_ERR_VALIDATION = {422: {"description": "Validation error"}}

_SINGLE_200 = {
    200: {
        "content": {
            "application/json": {"schema": inline_schema(PlainCarePlanResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRCarePlanSchema.model_json_schema())},
        }
    }
}
_SINGLE_201 = {201: _SINGLE_200[200]}
_LIST_200 = {
    200: {
        "description": "Paginated list of CarePlan resources",
        "content": {
            "application/json": {"schema": inline_schema(PaginatedCarePlanResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRCarePlanBundle.model_json_schema())},
        },
    }
}


# ── Create ───────────────────────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_care_plan",
    summary="Create a new CarePlan resource",
    description=(
        "Creates a FHIR R4 CarePlan resource. Required: `status`, `intent` and `subject` (Patient|Group reference, "
        "e.g. `'Patient/10001'`). Optional: `title`, `description`, `encounter`, `period_*`, `created`, `author`, "
        "`instantiates_canonical` / `instantiates_uri` (comma-separated) and the child lists `identifiers`, "
        "`based_on`, `replaces`, `part_of`, `categories`, `contributors`, `care_teams`, `addresses`, "
        "`supporting_info`, `goals`, `activities` (each with its outcome / progress / detail lists) and `notes`. "
        "An activity carries either a `reference` or `detail_*` fields, never both (cpl-3); `detail_status` is "
        "required whenever detail is supplied; `scheduled[x]` and `product[x]` allow one variant. "
        "References are `Type/id` strings — only their format is validated. "
        + _CONTENT_NEG
    ),
    response_description="The newly created CarePlan resource",
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_care_plan(
    payload: CarePlanCreateSchema,
    request: Request,
    care_plan_service: CarePlanService = Depends(get_care_plan_service),
):
    created_by = payload.created_by
    care_plan = await care_plan_service.create_care_plan(payload, payload.user_id, payload.org_id, created_by)
    return format_response(
        care_plan_service._to_fhir(care_plan),
        care_plan_service._to_plain(care_plan),
        request,
    )





@router.get(
    "/{care_plan_id}",
    operation_id="get_care_plan",
    summary="Retrieve a CarePlan by public identifier",
    description="Fetches a single CarePlan resource by its public `care_plan_id`. " + _CONTENT_NEG,
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_care_plan(
    request: Request,
    care_plan: CarePlanModel = Depends(resolve_care_plan),
    care_plan_service: CarePlanService = Depends(get_care_plan_service),
):
    return format_response(
        care_plan_service._to_fhir(care_plan),
        care_plan_service._to_plain(care_plan),
        request,
    )


# ── Patch ─────────────────────────────────────────────────────────────────────


@router.patch(
    "/{care_plan_id}",
    operation_id="patch_care_plan",
    summary="Partially update a CarePlan",
    description=(
        "Updates a CarePlan resource. Only supplied fields are changed (`status`, `intent` and `subject` cannot be "
        "null; `encounter` and `author` can be cleared with null). The child lists `identifiers`, `based_on`, "
        "`replaces`, `part_of`, `categories`, `contributors`, `care_teams`, `addresses`, `supporting_info`, "
        "`goals`, `activities` and `notes` use REPLACE semantics: a list that is sent replaces the stored list in "
        "full, `[]` clears it, and an omitted list is left untouched. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_care_plan(
    payload: CarePlanPatchSchema,
    request: Request,
    care_plan: CarePlanModel = Depends(resolve_care_plan),
    care_plan_service: CarePlanService = Depends(get_care_plan_service),
):
    updated_by = payload.updated_by
    updated = await care_plan_service.patch_care_plan(care_plan.care_plan_id, payload, updated_by)
    return format_response(
        care_plan_service._to_fhir(updated),
        care_plan_service._to_plain(updated),
        request,
    )


# ── List ──────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_care_plans",
    summary="Search CarePlan resources",
    description=(
        "Searches CarePlans using the FHIR R4 CarePlan search parameters "
        "(https://www.hl7.org/fhir/R4/careplan.html#search): `activity-code`, `activity-date`, `activity-reference`, "
        "`based-on`, `care-team`, `category`, `condition`, `date`, `encounter`, `goal`, `identifier`, "
        "`instantiates-canonical`, `instantiates-uri`, `intent`, `part-of`, `patient`, `performer`, `replaces`, "
        "`status`, `subject` — plus `_id` and `_lastUpdated`. "
        "Token params (`identifier`, `status`, `intent`, `category`, `activity-code`) accept `code`, `system|code`, "
        "`|code` or `system|`; comma = OR. Reference params accept `Type/id` or a bare numeric id. Date params "
        "(`date` = plan period, `activity-date` = activity scheduled period/bounds, `_lastUpdated`) take an optional "
        "prefix eq|ne|gt|lt|ge|le|sa|eb|ap (repeat for AND). "
        "`org_id` is mandatory on every search (tenant scope) and `user_id` is optional; paginate with `limit` / `offset`. "
        + _CONTENT_NEG
    ),
    responses={**_LIST_200, **_ERR_VALIDATION},
)
async def list_care_plans(
    request: Request,
    id_: Optional[str] = Query(None, alias="_id", description="Public care_plan_id(s), comma-separated."),
    identifier: Optional[str] = Query(None, description="Token `[system|]value` of CarePlan.identifier."),
    cp_status: Optional[str] = Query(None, alias="status", description="Token: draft|active|on-hold|revoked|completed|entered-in-error|unknown (comma = OR)."),
    intent: Optional[str] = Query(None, description="Token: proposal|plan|order|option (comma = OR)."),
    category: Optional[str] = Query(None, description="Token `[system|]code` of CarePlan.category."),
    activity_code: Optional[str] = Query(None, alias="activity-code", description="Token `[system|]code` of activity.detail.code."),
    activity_reference: Optional[str] = Query(None, alias="activity-reference", description="activity.reference: e.g. `ServiceRequest/80001`."),
    based_on: Optional[str] = Query(None, alias="based-on", description="CarePlan reference, e.g. `CarePlan/290001`."),
    replaces: Optional[str] = Query(None, description="CarePlan reference."),
    part_of: Optional[str] = Query(None, alias="part-of", description="CarePlan reference."),
    care_team: Optional[str] = Query(None, alias="care-team", description="CareTeam reference."),
    condition: Optional[str] = Query(None, description="Condition reference (CarePlan.addresses), e.g. `Condition/120001`."),
    goal: Optional[str] = Query(None, description="Goal reference."),
    encounter: Optional[str] = Query(None, description="Encounter reference: `Encounter/20001` or `20001`."),
    subject: Optional[str] = Query(None, description="Subject reference (Patient|Group), e.g. `Patient/10001`."),
    patient: Optional[str] = Query(None, description="Subject patient reference: `Patient/10001` or `10001`."),
    performer: Optional[str] = Query(None, description="activity.detail.performer reference (Practitioner, CareTeam, Patient, ...)."),
    instantiates_canonical: Optional[str] = Query(None, alias="instantiates-canonical", description="Canonical URL or `PlanDefinition/1`-style suffix."),
    instantiates_uri: Optional[str] = Query(None, alias="instantiates-uri", description="URI instantiated by the plan."),
    date: Optional[List[str]] = Query(None, description="Plan period with optional prefix, e.g. `ge2024-01-01`. Repeat for AND."),
    activity_date: Optional[List[str]] = Query(None, alias="activity-date", description="Activity scheduled period with optional prefix. Repeat for AND."),
    last_updated: Optional[List[str]] = Query(None, alias="_lastUpdated", description="Last-updated instant with optional prefix."),
    user_id: Optional[str] = Query(None, description="Optional: restrict to records owned by this user."),
    org_id: str = Query(..., min_length=1, description="Tenant organization id — mandatory scope of every search."),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    care_plan_service: CarePlanService = Depends(get_care_plan_service),
):
    search = CarePlanSearch(
        id=id_, identifier=identifier, cp_status=cp_status, intent=intent, category=category,
        activity_code=activity_code, activity_reference=activity_reference, based_on=based_on, replaces=replaces,
        part_of=part_of, care_team=care_team, condition=condition, goal=goal, encounter=encounter, subject=subject,
        patient=patient, performer=performer, instantiates_canonical=instantiates_canonical,
        instantiates_uri=instantiates_uri, date=date or [], activity_date=activity_date or [],
        last_updated=last_updated or [],
    )
    rows, total = await care_plan_service.list_care_plans(
        user_id=user_id, org_id=org_id, search=search, limit=limit, offset=offset)
    return format_paginated_response(
        [care_plan_service._to_fhir(cp) for cp in rows],
        [care_plan_service._to_plain(cp) for cp in rows],
        total, limit, offset, request,
    )


# ── Delete ────────────────────────────────────────────────────────────────────


@router.delete(
    "/{care_plan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_care_plan",
    summary="Delete a CarePlan resource",
    description="Permanently deletes a CarePlan and all its related child records.",
    responses={**_ERR_NOT_FOUND},
)
async def delete_care_plan(
    care_plan: CarePlanModel = Depends(resolve_care_plan),
    care_plan_service: CarePlanService = Depends(get_care_plan_service),
):
    await care_plan_service.delete_care_plan(care_plan.care_plan_id)
    return None
