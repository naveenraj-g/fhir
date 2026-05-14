from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth.dependencies import require_permission
from app.auth.patient_deps import get_authorized_patient
from app.core.content_negotiation import format_response, format_list_response
from app.di.dependencies.patient import get_patient_service
from app.models.patient import PatientModel
from app.schemas.resources import (
    PatientCreateSchema,
    PatientPatchSchema,
    PatientResponseSchema,
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


# ── Create Patient ─────────────────────────────────────────────────────────


@router.post(
    "/",
    response_model=PatientResponseSchema,
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("patient", "create"))],
    operation_id="create_patient",
    summary="Create a new Patient resource",
    description=(
        "Creates a Patient with core demographics (name, birth date, gender, preferred language, active status). "
        "The caller's `sub` claim (user ID) and `activeOrganizationId` from the JWT are automatically bound to the record. "
        "Identifiers, telecom, and addresses must be added after creation via the dedicated sub-resource endpoints. "
        + _CONTENT_NEG
    ),
    response_description="The newly created Patient resource",
    responses={**_ERR_AUTH, **_ERR_VALIDATION},
)
async def create_patient(
    payload: PatientCreateSchema,
    request: Request,
    patient_service: PatientService = Depends(get_patient_service),
):
    user_id: str = request.state.user.get("sub")
    org_id: str = request.state.user.get("activeOrganizationId")
    patient = await patient_service.create_patient(payload, user_id, org_id)
    return format_response(
        patient_service._to_fhir(patient),
        patient_service._to_plain(patient),
        request,
    )


# ── Get own Patient profile (/me) ──────────────────────────────────────────
# Declared before /{patient_id} so "me" is not matched by the int path param.


@router.get(
    "/me",
    response_model=PatientResponseSchema,
    response_model_exclude_none=True,
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
    response_model=PatientResponseSchema,
    response_model_exclude_none=True,
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
    response_model=PatientResponseSchema,
    response_model_exclude_none=True,
    dependencies=[Depends(require_permission("patient", "update"))],
    operation_id="patch_patient",
    summary="Partially update a Patient resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. "
        "Patchable fields include name, birth date, gender, active status, and preferred language. "
        "To modify identifiers, telecom, or addresses use the dedicated sub-resource endpoints. "
        + _CONTENT_NEG
    ),
    response_description="The updated Patient resource",
    responses={**_ERR_AUTH, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_patient(
    payload: PatientPatchSchema,
    request: Request,
    patient: PatientModel = Depends(get_authorized_patient),
    patient_service: PatientService = Depends(get_patient_service),
):
    updated = await patient_service.patch_patient(patient.patient_id, payload)
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
    response_model=list[PatientResponseSchema],
    response_model_exclude_none=True,
    dependencies=[Depends(require_permission("patient", "read"))],
    operation_id="list_patients",
    summary="List all Patient resources",
    description=(
        "Returns all Patient resources accessible to the caller. "
        "Results are scoped to the caller's active organization. "
        + _CONTENT_NEG
    ),
    response_description="Array of Patient resources",
    responses={**_ERR_AUTH},
)
async def list_patients(
    request: Request,
    patient_service: PatientService = Depends(get_patient_service),
):
    patients = await patient_service.list_patients()
    return format_list_response(
        [patient_service._to_fhir(p) for p in patients],
        [patient_service._to_plain(p) for p in patients],
        request,
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
    response_model=PatientResponseSchema,
    response_model_exclude_none=True,
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
    responses={**_ERR_AUTH, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
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
    response_model=PatientResponseSchema,
    response_model_exclude_none=True,
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
    responses={**_ERR_AUTH, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
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
    response_model=PatientResponseSchema,
    response_model_exclude_none=True,
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
    responses={**_ERR_AUTH, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
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
