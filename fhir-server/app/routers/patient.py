from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.auth.dependencies import require_permission
from app.auth.patient_deps import get_authorized_patient
from app.core.content_negotiation import format_response, format_paginated_response
from app.core.schema_utils import inline_schema
from app.di.dependencies.patient import get_patient_service
from app.models.patient import PatientModel
from app.schemas.fhir import FHIRPatientBundle, FHIRPatientSchema, PaginatedPatientResponse, PlainPatientResponse
from app.schemas.resources import (
    PatientCreateSchema,
    PatientPatchSchema,
    IdentifierCreate,
    TelecomCreate,
    AddressCreate,
)
from app.services.patient_service import PatientService

router = APIRouter()

_CONTENT_NEG = (
    "Set `Accept: application/fhir+json` to receive the full FHIR R4 representation; "
    "omit or use `Accept: application/json` for the simplified plain-JSON form."
)

_ERR_AUTH = {
    401: {"description": "Not authenticated — Bearer token missing or expired"},
    403: {"description": "Forbidden — caller lacks the required permission"},
}
_ERR_NOT_FOUND = {404: {"description": "Patient not found"}}
_ERR_VALIDATION = {422: {"description": "Validation error — request body failed schema validation"}}

# Pre-computed inline schemas (evaluated once at import time)
_SINGLE_200 = {
    200: {
        "content": {
            "application/json": {"schema": inline_schema(PlainPatientResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRPatientSchema.model_json_schema())},
        }
    }
}
_SINGLE_201 = {201: _SINGLE_200[200]}
_LIST_200 = {
    200: {
        "description": "Paginated list of patients",
        "content": {
            "application/json": {"schema": inline_schema(PaginatedPatientResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRPatientBundle.model_json_schema())},
        },
    }
}


# ── Create Patient ─────────────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("patient", "create"))],
    operation_id="create_patient",
    summary="Create a new Patient resource",
    description=(
        "Creates a Patient with core demographics (name, birth date, gender, active status). "
        "Supply `user_id` and `org_id` in the payload to bind the record to a specific user and organisation; "
        "omit them to create an unowned record. "
        "Identifiers, telecom, and addresses must be added after creation via the dedicated sub-resource endpoints. "
        + _CONTENT_NEG
    ),
    response_description="The newly created Patient resource",
    responses={**_SINGLE_201, **_ERR_AUTH, **_ERR_VALIDATION},
)
async def create_patient(
    payload: PatientCreateSchema,
    request: Request,
    patient_service: PatientService = Depends(get_patient_service),
):
    created_by: str = request.state.user.get("sub")
    patient = await patient_service.create_patient(payload, payload.user_id, payload.org_id, created_by)
    return format_response(
        patient_service._to_fhir(patient),
        patient_service._to_plain(patient),
        request,
    )


# ── Get own Patient profile (/me) ──────────────────────────────────────────
# Declared before /{patient_id} so "me" is not matched by the int path param.


@router.get(
    "/me",
    dependencies=[Depends(require_permission("patient", "read"))],
    operation_id="get_my_patient_profile",
    summary="Get the Patient profile for the currently authenticated user",
    description=(
        "Looks up the Patient record bound to the authenticated user's `sub` claim and `activeOrganizationId`. "
        "Returns 404 if no Patient profile has been created for this user in the current organization. "
        + _CONTENT_NEG
    ),
    response_description="The authenticated user's Patient resource",
    responses={
        **_SINGLE_200,
        **_ERR_AUTH,
        404: {"description": "No Patient profile found for the current authenticated user"},
    },
)
async def get_my_patient_profile(
    request: Request,
    patient_service: PatientService = Depends(get_patient_service),
):
    user_id: str = request.state.user.get("sub")
    org_id: str = request.state.user.get("activeOrganizationId")
    patient = await patient_service.get_me(user_id, org_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    return format_response(
        patient_service._to_fhir(patient),
        patient_service._to_plain(patient),
        request,
    )


# ── Get Patient by public patient_id ──────────────────────────────────────


@router.get(
    "/{patient_id}",
    dependencies=[Depends(require_permission("patient", "read"))],
    operation_id="get_patient_by_id",
    summary="Retrieve a Patient resource by public patient_id",
    description=(
        "Fetches a single Patient by its public integer `patient_id`. "
        "Access is subject to organization-scoped authorization — the patient must belong to the caller's active organization. "
        + _CONTENT_NEG
    ),
    response_description="The requested Patient resource",
    responses={
        **_SINGLE_200,
        **_ERR_AUTH,
        403: {"description": "Forbidden — caller lacks `patient:read` permission or the patient belongs to a different organization"},
        **_ERR_NOT_FOUND,
    },
)
async def get_patient(
    request: Request,
    patient: PatientModel = Depends(get_authorized_patient),
    patient_service: PatientService = Depends(get_patient_service),
):
    return format_response(
        patient_service._to_fhir(patient),
        patient_service._to_plain(patient),
        request,
    )


# ── Patch Patient ──────────────────────────────────────────────────────────


@router.patch(
    "/{patient_id}",
    dependencies=[Depends(require_permission("patient", "update"))],
    operation_id="patch_patient",
    summary="Partially update a Patient resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. "
        "Patchable fields include name, birth date, gender, and active status. "
        "To modify identifiers, telecom, or addresses use the dedicated sub-resource endpoints. "
        + _CONTENT_NEG
    ),
    response_description="The updated Patient resource",
    responses={**_SINGLE_201, **_ERR_AUTH, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_patient(
    payload: PatientPatchSchema,
    request: Request,
    patient: PatientModel = Depends(get_authorized_patient),
    patient_service: PatientService = Depends(get_patient_service),
):
    updated_by: str = request.state.user.get("sub")
    updated = await patient_service.patch_patient(patient.patient_id, payload, updated_by)
    if not updated:
        raise HTTPException(status_code=404, detail="Patient not found")
    return format_response(
        patient_service._to_fhir(updated),
        patient_service._to_plain(updated),
        request,
    )


# ── List Patients ──────────────────────────────────────────────────────────


@router.get(
    "/",
    dependencies=[Depends(require_permission("patient", "read"))],
    operation_id="list_patients",
    summary="List all Patient resources",
    description=(
        "Returns a paginated list of Patient resources. "
        "Filter by `family_name`, `given_name`, `gender`, `active`, `user_id`, or `org_id`. "
        "Use `limit` and `offset` for pagination. "
        + _CONTENT_NEG
    ),
    response_description="Paginated Patient resources",
    responses={**_LIST_200, **_ERR_AUTH},
)
async def list_patients(
    request: Request,
    family_name: Optional[str] = Query(None),
    given_name: Optional[str] = Query(None),
    gender: Optional[str] = Query(None),
    active: Optional[bool] = Query(None),
    user_id: Optional[str] = Query(None),
    org_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    patient_service: PatientService = Depends(get_patient_service),
):
    patients, total = await patient_service.list_patients(
        user_id=user_id, org_id=org_id, family_name=family_name,
        given_name=given_name, gender=gender, active=active,
        limit=limit, offset=offset,
    )
    return format_paginated_response(
        [patient_service._to_fhir(p) for p in patients],
        [patient_service._to_plain(p) for p in patients],
        total, limit, offset, request,
    )


# ── Delete Patient ─────────────────────────────────────────────────────────


@router.delete(
    "/{patient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("patient", "delete"))],
    operation_id="delete_patient",
    summary="Delete a Patient resource",
    description=(
        "Permanently deletes the Patient and all associated sub-resources (identifiers, telecom, addresses). "
        "This operation is irreversible. Returns 204 No Content on success."
    ),
    responses={**_ERR_AUTH, **_ERR_NOT_FOUND},
)
async def delete_patient(
    patient: PatientModel = Depends(get_authorized_patient),
    patient_service: PatientService = Depends(get_patient_service),
):
    await patient_service.delete_patient(patient.patient_id)
    return None


# ── Sub-resource: Identifiers ──────────────────────────────────────────────


@router.post(
    "/{patient_id}/identifiers",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("patient", "update"))],
    operation_id="add_patient_identifier",
    summary="Add an identifier to a Patient",
    description=(
        "Appends a business identifier to the Patient (e.g. MRN, SSN, passport number). "
        "`system` is a URI namespace (e.g. `http://hl7.org/fhir/sid/us-ssn`); "
        "`value` is the identifier string within that namespace. "
        "Returns the full updated Patient resource. "
        + _CONTENT_NEG
    ),
    response_description="The updated Patient resource with the new identifier appended",
    responses={**_SINGLE_201, **_ERR_AUTH, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def add_identifier(
    payload: IdentifierCreate,
    request: Request,
    patient: PatientModel = Depends(get_authorized_patient),
    patient_service: PatientService = Depends(get_patient_service),
):
    updated = await patient_service.add_identifier(patient.patient_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Patient not found")
    return format_response(
        patient_service._to_fhir(updated),
        patient_service._to_plain(updated),
        request,
    )


# ── Sub-resource: Telecom ──────────────────────────────────────────────────


@router.post(
    "/{patient_id}/telecom",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("patient", "update"))],
    operation_id="add_patient_telecom",
    summary="Add a contact point (telecom) to a Patient",
    description=(
        "Appends a contact point to the Patient. "
        "`system` values: `phone`, `fax`, `email`, `pager`, `url`, `sms`, `other`. "
        "`use` values: `home`, `work`, `temp`, `old`, `mobile`. "
        "Returns the full updated Patient resource. "
        + _CONTENT_NEG
    ),
    response_description="The updated Patient resource with the new contact point appended",
    responses={**_SINGLE_201, **_ERR_AUTH, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def add_telecom(
    payload: TelecomCreate,
    request: Request,
    patient: PatientModel = Depends(get_authorized_patient),
    patient_service: PatientService = Depends(get_patient_service),
):
    updated = await patient_service.add_telecom(patient.patient_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Patient not found")
    return format_response(
        patient_service._to_fhir(updated),
        patient_service._to_plain(updated),
        request,
    )


# ── Sub-resource: Addresses ────────────────────────────────────────────────


@router.post(
    "/{patient_id}/addresses",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("patient", "update"))],
    operation_id="add_patient_address",
    summary="Add an address to a Patient",
    description=(
        "Appends a postal or physical address to the Patient. "
        "`use` values: `home`, `work`, `temp`, `old`, `billing`. "
        "`type` values: `postal`, `physical`, `both`. "
        "Returns the full updated Patient resource. "
        + _CONTENT_NEG
    ),
    response_description="The updated Patient resource with the new address appended",
    responses={**_SINGLE_201, **_ERR_AUTH, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def add_address(
    payload: AddressCreate,
    request: Request,
    patient: PatientModel = Depends(get_authorized_patient),
    patient_service: PatientService = Depends(get_patient_service),
):
    updated = await patient_service.add_address(patient.patient_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Patient not found")
    return format_response(
        patient_service._to_fhir(updated),
        patient_service._to_plain(updated),
        request,
    )
