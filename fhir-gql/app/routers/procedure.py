"""
FastAPI router for Procedure resources.

Endpoints:
  POST   /procedures/        — create with all child arrays in the body
  GET    /procedures/{id}    — fetch a single Procedure by public ID
  GET    /procedures/        — paginated FHIR R4 search (status, code, patient, date, ...)
  PATCH  /procedures/{id}    — partial update (scalar + reference fields only)
  DELETE /procedures/{id}    — permanent delete (cascades to all child records)

All routes support content negotiation:
  - `Accept: application/json`      → plain snake_case JSON (default)
  - `Accept: application/fhir+json` → FHIR R4 resource / Bundle

RBAC is enforced via require_permission() for the ("procedure", <action>) pair.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response, get_accept_header
from app.core.schema_utils import inline_schema
from app.di.dependencies.procedure import get_procedure_service
from app.schemas.procedure.fhir_schemas import FhirBundleResponse, FhirProcedureResponse
from app.schemas.procedure.input import (
    ListProceduresSchema,
    ProcedureCreateSchema,
    ProcedurePatchSchema,
)
from app.schemas.procedure.response import PaginatedProcedureResponse, ProcedureResponse
from app.services.procedure_service import ProcedureService

# All procedure routes are prefixed with /procedures; tagged for Swagger grouping.
router = APIRouter(prefix="/procedures", tags=["Procedures"])

# ── Shared error response descriptors ────────────────────────────────────────

_ERR_NOT_FOUND = {404: {"description": "Procedure not found"}}
_ERR_VALIDATION = {422: {"description": "Validation error — request body or query params failed schema validation"}}

# ── Shared success response descriptors ──────────────────────────────────────
# inline_schema() resolves Pydantic's $defs/$ref pointers so both content types
# render in Swagger UI without resolver errors.

_SINGLE_201 = {
    201: {
        "description": "Procedure created successfully",
        "content": {
            "application/json": {
                "schema": inline_schema(ProcedureResponse.model_json_schema())
            },
            "application/fhir+json": {
                "schema": inline_schema(FhirProcedureResponse.model_json_schema())
            },
        },
    }
}

_SINGLE_200 = {
    200: {
        "description": "Procedure retrieved or updated successfully",
        "content": {
            "application/json": {
                "schema": inline_schema(ProcedureResponse.model_json_schema())
            },
            "application/fhir+json": {
                "schema": inline_schema(FhirProcedureResponse.model_json_schema())
            },
        },
    }
}

_LIST_200 = {
    200: {
        "description": "Paginated list of Procedure resources",
        "content": {
            "application/json": {
                "schema": inline_schema(PaginatedProcedureResponse.model_json_schema())
            },
            "application/fhir+json": {
                "schema": inline_schema(FhirBundleResponse.model_json_schema())
            },
        },
    }
}


# ── POST /procedures/ ────────────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_procedure",
    summary="Create a Procedure",
    description=(
        "Records an action that is or was performed on or for a patient (surgery, biopsy, therapy, ...). "
        "`status` and `subject` are required. Provide `subject` as a FHIR reference string e.g. `'Patient/10001'`. "
        "Optionally link to an Encounter via `encounter_id` (public encounter_id). "
        "Supply `performed[x]` via exactly one of: `performed_datetime`, `performed_period_*`, "
        "`performed_string`, `performed_age_*`, or `performed_range_*`. "
        "All child arrays (identifier, based_on, part_of, performer, reason_code, reason_reference, body_site, "
        "report, complication, complication_detail, follow_up, note, focal_device, used_reference, used_code) "
        "are submitted in the single request body. "
        "Send `Accept: application/fhir+json` to receive the result in FHIR R4 format."
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
    dependencies=[Depends(require_permission("procedure", "create"))],
)
async def create_procedure(
    dto: ProcedureCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("procedure", "create")),
    service: ProcedureService = Depends(get_procedure_service),
) -> JSONResponse:
    """Create a new Procedure resource and return the persisted record."""
    data = await service.create(dto, actor, accept=get_accept_header(request))
    return format_response(data, request)


# ── GET /procedures/{resource_id} ────────────────────────────────────────────


@router.get(
    "/{resource_id}",
    operation_id="get_procedure",
    summary="Get a Procedure by ID",
    description=(
        "Fetch a single Procedure by its public integer ID. "
        "The response includes all child arrays (performer, reason_code, note, ...). "
        "Send `Accept: application/fhir+json` for FHIR R4 format."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
    dependencies=[Depends(require_permission("procedure", "read"))],
)
async def get_procedure(
    resource_id: int,
    request: Request,
    actor: AuthUser = Depends(require_permission("procedure", "read")),
    service: ProcedureService = Depends(get_procedure_service),
) -> JSONResponse:
    """Fetch a single Procedure resource by its public ID."""
    data = await service.get_by_id(resource_id, actor, accept=get_accept_header(request))
    return format_response(data, request)


# ── GET /procedures/ ─────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_procedures",
    summary="Search Procedures",
    description=(
        "Searches Procedure resources using the FHIR R4 Procedure search parameters "
        "(https://www.hl7.org/fhir/R4/procedure.html#search). "
        "Token params (`status`, `code`, `category`, `identifier`, `reason-code`) accept `code`, `system|code`, "
        "`|code` or `system|`. Reference params (`patient`, `subject`, `encounter`, `performer`, `location`, "
        "`part-of`, `based-on`, `reason-reference`) accept `Type/id` or a bare numeric id. "
        "Comma-separated values are OR; repeat `date` / `_lastUpdated` for AND (e.g. a range). "
        "Date params take an optional prefix eq|ne|gt|lt|ge|le|sa|eb|ap, e.g. "
        "`date=ge2024-01-01&date=lt2024-02-01`; `date` matches performedDateTime or performedPeriod. "
        "`org_id` is mandatory on every search (tenant scope) and `user_id` is optional; paginate with `limit` and `offset`. "
        "Send `Accept: application/fhir+json` to receive a FHIR Bundle searchset."
    ),
    responses={**_LIST_200, **_ERR_VALIDATION},
    dependencies=[Depends(require_permission("procedure", "read"))],
)
async def list_procedures(
    request: Request,
    id_: Optional[str] = Query(None, alias="_id", description="Public procedure_id(s), comma-separated."),
    identifier: Optional[str] = Query(None, description="Token `[system|]value` of Procedure.identifier."),
    proc_status: Optional[str] = Query(
        None,
        alias="status",
        description="Token: preparation|in-progress|not-done|on-hold|stopped|completed|entered-in-error|unknown (comma = OR).",
    ),
    category: Optional[str] = Query(None, description="Token `[system|]code` of Procedure.category."),
    code: Optional[str] = Query(None, description="Token `[system|]code` of Procedure.code, e.g. `http://snomed.info/sct|80146002`."),
    patient: Optional[str] = Query(None, description="Subject patient reference: `Patient/10001` or `10001`."),
    subject: Optional[str] = Query(None, description="Subject reference (Patient or Group): `Patient/10001`, `Group/1`."),
    encounter: Optional[str] = Query(None, description="Encounter reference: `Encounter/20001` or `20001`."),
    date: Optional[List[str]] = Query(None, description="performed[x] date with optional prefix, e.g. `ge2024-01-01`. Repeat for AND."),
    performer: Optional[str] = Query(None, description="Performer.actor reference, e.g. `Practitioner/30001`."),
    location: Optional[str] = Query(None, description="Location reference, e.g. `Location/230001`."),
    part_of: Optional[str] = Query(None, alias="part-of", description="partOf reference: Procedure|Observation|MedicationAdministration."),
    based_on: Optional[str] = Query(None, alias="based-on", description="basedOn reference: CarePlan|ServiceRequest."),
    reason_code: Optional[str] = Query(None, alias="reason-code", description="Token `[system|]code` of Procedure.reasonCode."),
    reason_reference: Optional[str] = Query(None, alias="reason-reference", description="reasonReference: Condition|Observation|Procedure|DiagnosticReport|DocumentReference."),
    instantiates_canonical: Optional[str] = Query(None, alias="instantiates-canonical", description="Canonical URI of an instantiated protocol."),
    instantiates_uri: Optional[str] = Query(None, alias="instantiates-uri", description="URI of an instantiated external protocol."),
    last_updated: Optional[List[str]] = Query(None, alias="_lastUpdated", description="Last-updated instant with optional prefix. Repeat for AND."),
    user_id: Optional[str] = Query(None, description="Optional: restrict to records owned by this user (JWT subject)."),
    org_id: str = Query(..., min_length=1, description="Tenant organization ID — mandatory scope of every search."),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    actor: AuthUser = Depends(require_permission("procedure", "read")),
    service: ProcedureService = Depends(get_procedure_service),
) -> JSONResponse:
    """
    Search Procedures with FHIR R4 search parameters.

    Parameters are declared explicitly (with aliases) because several FHIR names
    are hyphenated or underscore-prefixed. They are gathered into
    ListProceduresSchema, whose validators (e.g. the status code check) run here;
    a failure is surfaced as a 422 rather than an unhandled 500.
    """
    try:
        filters = ListProceduresSchema(
            id=id_,
            identifier=identifier,
            status=proc_status,
            category=category,
            code=code,
            patient=patient,
            subject=subject,
            encounter=encounter,
            date=date,
            performer=performer,
            location=location,
            part_of=part_of,
            based_on=based_on,
            reason_code=reason_code,
            reason_reference=reason_reference,
            instantiates_canonical=instantiates_canonical,
            instantiates_uri=instantiates_uri,
            last_updated=last_updated,
            user_id=user_id,
            org_id=org_id,
            limit=limit,
            offset=offset,
        )
    except ValidationError as exc:
        # include_context=False keeps the detail JSON-serialisable (ctx can hold exceptions).
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.errors(include_url=False, include_context=False),
        ) from exc
    data = await service.list(filters, actor, accept=get_accept_header(request))
    return format_paginated_response(data, request)


# ── PATCH /procedures/{resource_id} ──────────────────────────────────────────


@router.patch(
    "/{resource_id}",
    operation_id="update_procedure",
    summary="Partially update a Procedure",
    description=(
        "Update specific scalar and reference fields on a Procedure. At least one field must be provided. "
        "Patchable fields: `status`, `status_reason_*`, `category_*`, `code_*`, `subject` (Patient/Group "
        "reference), `subject_display`, `encounter_id`, `encounter_display`, all `performed_*` variants, "
        "`recorder`, `asserter`, `location` (FHIR references) and their `*_display`, `outcome_*`, "
        "`instantiates_canonical`, `instantiates_uri`. "
        "Child lists (identifier, based_on, part_of, performer, reason_code, reason_reference, body_site, "
        "report, complication, complication_detail, follow_up, note, focal_device, used_reference, used_code) "
        "are also patchable with REPLACE semantics: a list that is sent replaces the stored list in full, `[]` "
        "clears it, and an omitted list is left untouched. "
        "Send `Accept: application/fhir+json` for FHIR R4 format."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
    dependencies=[Depends(require_permission("procedure", "update"))],
)
async def update_procedure(
    resource_id: int,
    dto: ProcedurePatchSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("procedure", "update")),
    service: ProcedureService = Depends(get_procedure_service),
) -> JSONResponse:
    """Partially update a Procedure resource. Returns 422 if the body is empty."""
    data = await service.update(resource_id, dto, actor, accept=get_accept_header(request))
    return format_response(data, request)


# ── DELETE /procedures/{resource_id} ─────────────────────────────────────────


@router.delete(
    "/{resource_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_procedure",
    summary="Delete a Procedure",
    description=(
        "Permanently deletes the Procedure and all its child records "
        "(identifier, basedOn, partOf, performer, reasonCode, reasonReference, bodySite, report, "
        "complication, complicationDetail, followUp, note, focalDevice, usedReference, usedCode). "
        "This operation is irreversible. Returns 204 No Content on success."
    ),
    responses={**_ERR_NOT_FOUND},
    dependencies=[Depends(require_permission("procedure", "delete"))],
)
async def delete_procedure(
    resource_id: int,
    actor: AuthUser = Depends(require_permission("procedure", "delete")),
    service: ProcedureService = Depends(get_procedure_service),
) -> None:
    """Permanently delete a Procedure and cascade to all child records."""
    await service.delete(resource_id, actor)
