from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.core.content_negotiation import format_paginated_response, format_response
from app.core.schema_utils import inline_schema
from app.deps.flag_deps import resolve_flag
from app.di.dependencies.flag import get_flag_service
from app.models.flag.flag import FlagModel
from app.repository.flag_repository import FlagSearch
from app.schemas.flag import FlagCreateSchema, FlagPatchSchema
from app.schemas.flag.response import (
    FHIRFlagBundle,
    FHIRFlagSchema,
    PaginatedFlagResponse,
    PlainFlagResponse,
)
from app.services.flag_service import FlagService

router = APIRouter()

_CONTENT_NEG = (
    "Set `Accept: application/fhir+json` to receive the full FHIR R4 representation; "
    "omit or use `Accept: application/json` for the simplified plain-JSON form."
)

_ERR_NOT_FOUND = {404: {"description": "Flag not found"}}
_ERR_VALIDATION = {422: {"description": "Validation error — request body or query params failed validation"}}

_SINGLE_200 = {
    200: {
        "content": {
            "application/json": {"schema": inline_schema(PlainFlagResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRFlagSchema.model_json_schema())},
        }
    }
}
_SINGLE_201 = {201: _SINGLE_200[200]}
_LIST_200 = {
    200: {
        "description": "Paginated list of flags",
        "content": {
            "application/json": {"schema": inline_schema(PaginatedFlagResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRFlagBundle.model_json_schema())},
        },
    }
}


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_flag",
    summary="Create a new Flag resource",
    description=(
        "Raises a prospective warning about a potential issue when providing care (e.g. an allergy alert or a "
        "safety flag). `status`, `code` (`code_code` and/or `code_text`) and `subject` are required. "
        "`subject` is a FHIR reference: Patient|Location|Group|Organization|Practitioner|PlanDefinition|Medication|"
        "Procedure, e.g. `'Patient/10001'`. Optionally set the active `period_start` / `period_end` (an empty end "
        "means still active), an `encounter_id`, an `author` (Device|Organization|Patient|Practitioner|"
        "PractitionerRole) and the `identifier` / `category` lists. " + _CONTENT_NEG
    ),
    response_description="The newly created Flag resource",
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_flag(
    payload: FlagCreateSchema,
    request: Request,
    service: FlagService = Depends(get_flag_service),
):
    flag = await service.create_flag(payload, payload.user_id, payload.org_id, payload.created_by)
    return format_response(service._to_fhir(flag), service._to_plain(flag), request)


@router.get(
    "/{flag_id}",
    operation_id="get_flag_by_id",
    summary="Retrieve a Flag resource by public flag_id",
    description="Fetches a single Flag by its public integer `flag_id`. " + _CONTENT_NEG,
    response_description="The requested Flag resource",
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_flag(
    request: Request,
    flag: FlagModel = Depends(resolve_flag),
    service: FlagService = Depends(get_flag_service),
):
    return format_response(service._to_fhir(flag), service._to_plain(flag), request)


@router.patch(
    "/{flag_id}",
    operation_id="patch_flag",
    summary="Partially update a Flag resource",
    description=(
        "Patchable fields: `status` (cannot be null), `code_*`, `subject` (cannot be null), `period_start` / "
        "`period_end`, `encounter_id`, `author`, and their `*_display` (references as `Type/id`; null clears the "
        "optional ones). To retire a flag set `status: inactive` and/or `period_end`. "
        "The child lists `identifier` and `category` are also patchable with REPLACE semantics: a list that is "
        "sent replaces the stored list in full, `[]` clears it, and an omitted list is left untouched. " + _CONTENT_NEG
    ),
    response_description="The updated Flag resource",
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_flag(
    payload: FlagPatchSchema,
    request: Request,
    flag: FlagModel = Depends(resolve_flag),
    service: FlagService = Depends(get_flag_service),
):
    updated = await service.patch_flag(flag.flag_id, payload, payload.updated_by)
    if not updated:
        raise HTTPException(status_code=404, detail="Flag not found")
    return format_response(service._to_fhir(updated), service._to_plain(updated), request)


@router.get(
    "/",
    operation_id="list_flags",
    summary="Search Flag resources",
    description=(
        "Searches Flags using the FHIR R4 Flag search parameters (https://www.hl7.org/fhir/R4/flag.html#search): "
        "`author`, `date`, `encounter`, `identifier`, `patient`, `subject` — plus `_id`, `_lastUpdated` and the "
        "convenience filters `status`, `category` and `code`. "
        "Token params (`identifier`, `status`, `category`, `code`) accept `code`, `system|code`, `|code` or "
        "`system|`; comma = OR. Reference params (`patient`, `subject`, `encounter`, `author`) accept `Type/id` or "
        "a bare numeric id. `date` matches the flag's active period and, like `_lastUpdated`, takes an optional "
        "prefix eq|ne|gt|lt|ge|le|sa|eb|ap (repeat for AND, e.g. flags active during a window). "
        "`org_id` is mandatory on every search (tenant scope) and `user_id` is optional; paginate with `limit` / `offset`. " + _CONTENT_NEG
    ),
    response_description="Paginated Flag resources",
    responses={**_LIST_200, **_ERR_VALIDATION},
)
async def list_flags(
    request: Request,
    id_: Optional[str] = Query(None, alias="_id", description="Public flag_id(s), comma-separated."),
    identifier: Optional[str] = Query(None, description="Token `[system|]value` of Flag.identifier."),
    flag_status: Optional[str] = Query(None, alias="status", description="Token: active|inactive|entered-in-error (comma = OR)."),
    category: Optional[str] = Query(None, description="Token `[system|]code` of Flag.category."),
    code: Optional[str] = Query(None, description="Token `[system|]code` of Flag.code."),
    subject: Optional[str] = Query(None, description="Subject reference (Patient, Location, Group, ...), e.g. `Patient/10001`."),
    patient: Optional[str] = Query(None, description="Subject patient reference: `Patient/10001` or `10001`."),
    encounter: Optional[str] = Query(None, description="Encounter reference: `Encounter/20001` or `20001`."),
    author: Optional[str] = Query(None, description="Author reference: Device|Organization|Patient|Practitioner|PractitionerRole."),
    date: Optional[List[str]] = Query(None, description="Flag active period with optional prefix, e.g. `ge2024-01-01`. Repeat for AND."),
    last_updated: Optional[List[str]] = Query(None, alias="_lastUpdated", description="Last-updated instant with optional prefix."),
    user_id: Optional[str] = Query(None, description="Optional: restrict to records owned by this user."),
    org_id: str = Query(..., min_length=1, description="Tenant organization id — mandatory scope of every search."),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: FlagService = Depends(get_flag_service),
):
    search = FlagSearch(
        id=id_, identifier=identifier, flag_status=flag_status, category=category, code=code,
        subject=subject, patient=patient, encounter=encounter, author=author,
        date=date or [], last_updated=last_updated or [],
    )
    items, total = await service.list_flags(user_id=user_id, org_id=org_id, search=search, limit=limit, offset=offset)
    return format_paginated_response(
        [service._to_fhir(i) for i in items],
        [service._to_plain(i) for i in items],
        total, limit, offset, request,
    )


@router.delete(
    "/{flag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_flag",
    summary="Delete a Flag resource",
    description=(
        "Permanently deletes the Flag and its child records (identifier, category). "
        "This operation is irreversible. Returns 204 No Content on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_flag(
    flag: FlagModel = Depends(resolve_flag),
    service: FlagService = Depends(get_flag_service),
):
    await service.delete_flag(flag.flag_id)
    return None
