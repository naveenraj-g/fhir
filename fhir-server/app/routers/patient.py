from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.auth.dependencies import require_permission
from app.auth.patient_deps import get_authorized_patient
from app.core.content_negotiation import format_response, format_paginated_response
from app.core.schema_utils import inline_schema
from app.di.dependencies.patient import get_patient_service
from app.models.patient.patient import PatientModel
from app.schemas.fhir import FHIRPatientBundle, FHIRPatientSchema, PaginatedPatientResponse, PlainPatientResponse
from app.schemas.resources import (
    PatientCreateSchema,
    PatientPatchSchema,
    NameCreate,
    IdentifierCreate,
    TelecomCreate,
    AddressCreate,
    PhotoCreate,
    ContactCreate,
    CommunicationCreate,
    GeneralPractitionerCreate,
    LinkCreate,
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


# ── Create ─────────────────────────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("patient", "create"))],
    operation_id="create_patient",
    summary="Create a new Patient resource",
    description=(
        "Creates a Patient with core demographic scalar fields (gender, birth date, active status, "
        "marital status, deceased, managing organization). "
        "Names, identifiers, telecom, addresses, photos, contacts, communications, "
        "general practitioners, and links must be added via the dedicated sub-resource endpoints. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_AUTH, **_ERR_VALIDATION},
)
async def create_patient(
    payload: PatientCreateSchema,
    request: Request,
    patient_service: PatientService = Depends(get_patient_service),
):
    created_by: str = request.state.user.get("sub")
    patient = await patient_service.create_patient(payload, payload.user_id, payload.org_id, created_by)
    return format_response(patient_service._to_fhir(patient), patient_service._to_plain(patient), request)


# ── Get own profile (/me) ──────────────────────────────────────────────────────


@router.get(
    "/me",
    dependencies=[Depends(require_permission("patient", "read"))],
    operation_id="get_my_patient_profile",
    summary="Get the Patient profile for the currently authenticated user",
    description=(
        "Looks up the Patient record bound to the authenticated user's `sub` claim and "
        "`activeOrganizationId`. Returns 404 if no Patient exists for this user in the current org. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_AUTH, 404: {"description": "No Patient profile found for current user"}},
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
    return format_response(patient_service._to_fhir(patient), patient_service._to_plain(patient), request)


# ── Get by ID ──────────────────────────────────────────────────────────────────


@router.get(
    "/{patient_id}",
    dependencies=[Depends(require_permission("patient", "read"))],
    operation_id="get_patient_by_id",
    summary="Retrieve a Patient resource by public patient_id",
    responses={**_SINGLE_200, **_ERR_AUTH, **_ERR_NOT_FOUND},
)
async def get_patient(
    request: Request,
    patient: PatientModel = Depends(get_authorized_patient),
    patient_service: PatientService = Depends(get_patient_service),
):
    return format_response(patient_service._to_fhir(patient), patient_service._to_plain(patient), request)


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{patient_id}",
    dependencies=[Depends(require_permission("patient", "update"))],
    operation_id="patch_patient",
    summary="Partially update a Patient resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. "
        "Patchable scalar fields: gender, birth_date, active, deceased, marital status, "
        "multiple birth, managing organization. "
        "To modify sub-resources (names, identifiers, etc.) use the dedicated endpoints. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_AUTH, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
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
    return format_response(patient_service._to_fhir(updated), patient_service._to_plain(updated), request)


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    dependencies=[Depends(require_permission("patient", "read"))],
    operation_id="list_patients",
    summary="List all Patient resources",
    description=(
        "Returns a paginated list of Patient resources. "
        "Filter by `family_name` or `given_name` (searches across the patient_name table), "
        "`gender`, `active`, `user_id`, or `org_id`. "
        + _CONTENT_NEG
    ),
    responses={**_LIST_200, **_ERR_AUTH},
)
async def list_patients(
    request: Request,
    family_name: Optional[str] = Query(None, description="Filter by family (last) name — partial match."),
    given_name: Optional[str] = Query(None, description="Filter by given name — partial match."),
    gender: Optional[str] = Query(None, description="male|female|other|unknown"),
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


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{patient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("patient", "delete"))],
    operation_id="delete_patient",
    summary="Delete a Patient resource",
    description="Permanently deletes the Patient and all associated sub-resources. Returns 204 on success.",
    responses={**_ERR_AUTH, **_ERR_NOT_FOUND},
)
async def delete_patient(
    patient: PatientModel = Depends(get_authorized_patient),
    patient_service: PatientService = Depends(get_patient_service),
):
    await patient_service.delete_patient(patient.patient_id)
    return None


# ── Sub-resource: Names ────────────────────────────────────────────────────────


@router.post(
    "/{patient_id}/names",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("patient", "update"))],
    operation_id="add_patient_name",
    summary="Add a name to a Patient",
    description=(
        "Appends a HumanName record to the Patient. "
        "`use` values: usual|official|temp|nickname|anonymous|old|maiden. "
        "`given`, `prefix`, `suffix` accept lists of strings. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_AUTH, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def add_name(
    payload: NameCreate,
    request: Request,
    patient: PatientModel = Depends(get_authorized_patient),
    patient_service: PatientService = Depends(get_patient_service),
):
    updated = await patient_service.add_name(patient.patient_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Patient not found")
    return format_response(patient_service._to_fhir(updated), patient_service._to_plain(updated), request)


# ── Sub-resource: Identifiers ──────────────────────────────────────────────────


@router.post(
    "/{patient_id}/identifiers",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("patient", "update"))],
    operation_id="add_patient_identifier",
    summary="Add an identifier to a Patient",
    description=(
        "Appends a business identifier (e.g. MRN, SSN, passport). "
        "`system` is a URI namespace; `value` is the identifier string within that namespace. "
        + _CONTENT_NEG
    ),
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
    return format_response(patient_service._to_fhir(updated), patient_service._to_plain(updated), request)


# ── Sub-resource: Telecom ──────────────────────────────────────────────────────


@router.post(
    "/{patient_id}/telecom",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("patient", "update"))],
    operation_id="add_patient_telecom",
    summary="Add a contact point (telecom) to a Patient",
    description=(
        "Appends a contact point. `system`: phone|fax|email|pager|url|sms|other. "
        "`use`: home|work|temp|old|mobile. `rank`: preferred order (1 = highest). "
        + _CONTENT_NEG
    ),
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
    return format_response(patient_service._to_fhir(updated), patient_service._to_plain(updated), request)


# ── Sub-resource: Addresses ────────────────────────────────────────────────────


@router.post(
    "/{patient_id}/addresses",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("patient", "update"))],
    operation_id="add_patient_address",
    summary="Add an address to a Patient",
    description=(
        "Appends an address. `use`: home|work|temp|old|billing. `type`: postal|physical|both. "
        "`line` accepts a list of address lines. "
        + _CONTENT_NEG
    ),
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
    return format_response(patient_service._to_fhir(updated), patient_service._to_plain(updated), request)


# ── Sub-resource: Photos ───────────────────────────────────────────────────────


@router.post(
    "/{patient_id}/photos",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("patient", "update"))],
    operation_id="add_patient_photo",
    summary="Add a photo (Attachment) to a Patient",
    description=(
        "Appends a photo attachment. Provide either `url` (external link) or "
        "`data` (base64-encoded binary). `content_type` is a MIME type (e.g. image/png). "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_AUTH, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def add_photo(
    payload: PhotoCreate,
    request: Request,
    patient: PatientModel = Depends(get_authorized_patient),
    patient_service: PatientService = Depends(get_patient_service),
):
    updated = await patient_service.add_photo(patient.patient_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Patient not found")
    return format_response(patient_service._to_fhir(updated), patient_service._to_plain(updated), request)


# ── Sub-resource: Contacts ─────────────────────────────────────────────────────


@router.post(
    "/{patient_id}/contacts",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("patient", "update"))],
    operation_id="add_patient_contact",
    summary="Add a contact (next-of-kin / guardian) to a Patient",
    description=(
        "Appends a contact BackboneElement. Accepts flattened name and address fields, "
        "plus nested `relationship[]` and `telecom[]` arrays. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_AUTH, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def add_contact(
    payload: ContactCreate,
    request: Request,
    patient: PatientModel = Depends(get_authorized_patient),
    patient_service: PatientService = Depends(get_patient_service),
):
    updated = await patient_service.add_contact(patient.patient_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Patient not found")
    return format_response(patient_service._to_fhir(updated), patient_service._to_plain(updated), request)


# ── Sub-resource: Communications ──────────────────────────────────────────────


@router.post(
    "/{patient_id}/communications",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("patient", "update"))],
    operation_id="add_patient_communication",
    summary="Add a communication language to a Patient",
    description=(
        "Appends a preferred communication language. `language_code` is an ISO-639-1 code (e.g. en, fr). "
        "Set `preferred: true` to mark this as the patient's primary language. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_AUTH, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def add_communication(
    payload: CommunicationCreate,
    request: Request,
    patient: PatientModel = Depends(get_authorized_patient),
    patient_service: PatientService = Depends(get_patient_service),
):
    updated = await patient_service.add_communication(patient.patient_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Patient not found")
    return format_response(patient_service._to_fhir(updated), patient_service._to_plain(updated), request)


# ── Sub-resource: General Practitioners ───────────────────────────────────────


@router.post(
    "/{patient_id}/general-practitioners",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("patient", "update"))],
    operation_id="add_patient_general_practitioner",
    summary="Add a general practitioner reference to a Patient",
    description=(
        "Appends a reference to the patient's nominated primary care provider. "
        "`reference_type`: Organization|Practitioner|PractitionerRole. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_AUTH, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def add_general_practitioner(
    payload: GeneralPractitionerCreate,
    request: Request,
    patient: PatientModel = Depends(get_authorized_patient),
    patient_service: PatientService = Depends(get_patient_service),
):
    updated = await patient_service.add_general_practitioner(patient.patient_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Patient not found")
    return format_response(patient_service._to_fhir(updated), patient_service._to_plain(updated), request)


# ── Sub-resource: Links ────────────────────────────────────────────────────────


@router.post(
    "/{patient_id}/links",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("patient", "update"))],
    operation_id="add_patient_link",
    summary="Add a link to a related Patient or RelatedPerson",
    description=(
        "`other_type`: Patient|RelatedPerson. "
        "`type`: replaced-by|replaces|refer|seealso. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_AUTH, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def add_link(
    payload: LinkCreate,
    request: Request,
    patient: PatientModel = Depends(get_authorized_patient),
    patient_service: PatientService = Depends(get_patient_service),
):
    updated = await patient_service.add_link(patient.patient_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Patient not found")
    return format_response(patient_service._to_fhir(updated), patient_service._to_plain(updated), request)
