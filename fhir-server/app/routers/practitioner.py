from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth.dependencies import require_permission
from app.auth.practitioner_deps import get_authorized_practitioner
from app.core.content_negotiation import format_response, format_list_response
from app.di.dependencies.practitioner import get_practitioner_service
from app.models.practitioner import PractitionerModel
from app.schemas.practitioner import (
    PractitionerCreateSchema,
    PractitionerPatchSchema,
    PractitionerResponseSchema,
    PractitionerIdentifierCreate,
    PractitionerTelecomCreate,
    PractitionerAddressCreate,
    PractitionerQualificationCreate,
)
from app.services.practitioner_service import PractitionerService

router = APIRouter()

_CONTENT_NEG = (
    "Set `Accept: application/fhir+json` to receive the full FHIR R4 representation; "
    "omit or use `Accept: application/json` for the simplified plain-JSON form."
)

_ERR_AUTH = {
    401: {"description": "Not authenticated — Bearer token missing or expired"},
    403: {"description": "Forbidden — caller lacks the required permission"},
}
_ERR_NOT_FOUND = {404: {"description": "Practitioner not found"}}
_ERR_VALIDATION = {422: {"description": "Validation error — request body failed schema validation"}}


# ── Create Practitioner ────────────────────────────────────────────────────


@router.post(
    "/",
    response_model=PractitionerResponseSchema,
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("practitioner", "create"))],
    operation_id="create_practitioner",
    summary="Create a new Practitioner resource",
    description=(
        "Creates a Practitioner with core demographics (name, birth date, gender, active status, communication language). "
        "The caller's `sub` claim (user ID) and `activeOrganizationId` from the JWT are automatically bound to the record. "
        "Identifiers, telecom, addresses, and qualifications must be added after creation via the dedicated sub-resource endpoints. "
        + _CONTENT_NEG
    ),
    response_description="The newly created Practitioner resource",
    responses={**_ERR_AUTH, **_ERR_VALIDATION},
)
async def create_practitioner(
    payload: PractitionerCreateSchema,
    request: Request,
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    user_id: str = request.state.user.get("sub")
    org_id: str = request.state.user.get("activeOrganizationId")
    practitioner = await practitioner_service.create_practitioner(payload, user_id, org_id)
    return format_response(
        practitioner_service._to_fhir(practitioner),
        practitioner_service._to_plain(practitioner),
        request,
    )


# ── Get own Practitioner profile (/me) ────────────────────────────────────
# Declared before /{practitioner_id} so "me" is not matched by the int path param.


@router.get(
    "/me",
    response_model=PractitionerResponseSchema,
    response_model_exclude_none=True,
    dependencies=[Depends(require_permission("practitioner", "read"))],
    operation_id="get_my_practitioner_profile",
    summary="Get the Practitioner profile for the currently authenticated user",
    description=(
        "Looks up the Practitioner record bound to the authenticated user's `sub` claim and `activeOrganizationId`. "
        "Returns 404 if no Practitioner profile has been created for this user in the current organization. "
        + _CONTENT_NEG
    ),
    response_description="The authenticated user's Practitioner resource",
    responses={
        **_ERR_AUTH,
        404: {"description": "No Practitioner profile found for the current authenticated user"},
    },
)
async def get_my_practitioner_profile(
    request: Request,
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    user_id: str = request.state.user.get("sub")
    org_id: str = request.state.user.get("activeOrganizationId")
    practitioner = await practitioner_service.get_me(user_id, org_id)
    if not practitioner:
        raise HTTPException(status_code=404, detail="Practitioner profile not found")
    return format_response(
        practitioner_service._to_fhir(practitioner),
        practitioner_service._to_plain(practitioner),
        request,
    )


# ── Get Practitioner by public practitioner_id ─────────────────────────────


@router.get(
    "/{practitioner_id}",
    response_model=PractitionerResponseSchema,
    response_model_exclude_none=True,
    dependencies=[Depends(require_permission("practitioner", "read"))],
    operation_id="get_practitioner_by_id",
    summary="Retrieve a Practitioner resource by public practitioner_id",
    description=(
        "Fetches a single Practitioner by its public integer `practitioner_id`. "
        "Access is subject to organization-scoped authorization — the practitioner must belong to the caller's active organization. "
        + _CONTENT_NEG
    ),
    response_description="The requested Practitioner resource",
    responses={
        **_ERR_AUTH,
        403: {"description": "Forbidden — caller lacks `practitioner:read` permission or the practitioner belongs to a different organization"},
        **_ERR_NOT_FOUND,
    },
)
async def get_practitioner(
    request: Request,
    practitioner: PractitionerModel = Depends(get_authorized_practitioner),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    return format_response(
        practitioner_service._to_fhir(practitioner),
        practitioner_service._to_plain(practitioner),
        request,
    )


# ── Patch Practitioner ─────────────────────────────────────────────────────


@router.patch(
    "/{practitioner_id}",
    response_model=PractitionerResponseSchema,
    response_model_exclude_none=True,
    dependencies=[Depends(require_permission("practitioner", "update"))],
    operation_id="patch_practitioner",
    summary="Partially update a Practitioner resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. "
        "Patchable fields include name, birth date, gender, active status, and communication language. "
        "To modify identifiers, telecom, addresses, or qualifications use the dedicated sub-resource endpoints. "
        + _CONTENT_NEG
    ),
    response_description="The updated Practitioner resource",
    responses={**_ERR_AUTH, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_practitioner(
    payload: PractitionerPatchSchema,
    request: Request,
    practitioner: PractitionerModel = Depends(get_authorized_practitioner),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    updated = await practitioner_service.patch_practitioner(practitioner.practitioner_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Practitioner not found")
    return format_response(
        practitioner_service._to_fhir(updated),
        practitioner_service._to_plain(updated),
        request,
    )


# ── List Practitioners ─────────────────────────────────────────────────────


@router.get(
    "/",
    response_model=list[PractitionerResponseSchema],
    response_model_exclude_none=True,
    dependencies=[Depends(require_permission("practitioner", "read"))],
    operation_id="list_practitioners",
    summary="List all Practitioner resources",
    description=(
        "Returns all Practitioner resources accessible to the caller. "
        "Results are scoped to the caller's active organization. "
        + _CONTENT_NEG
    ),
    response_description="Array of Practitioner resources",
    responses={**_ERR_AUTH},
)
async def list_practitioners(
    request: Request,
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    practitioners = await practitioner_service.list_practitioners()
    return format_list_response(
        [practitioner_service._to_fhir(p) for p in practitioners],
        [practitioner_service._to_plain(p) for p in practitioners],
        request,
    )


# ── Delete Practitioner ────────────────────────────────────────────────────


@router.delete(
    "/{practitioner_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("practitioner", "delete"))],
    operation_id="delete_practitioner",
    summary="Delete a Practitioner resource",
    description=(
        "Permanently deletes the Practitioner and all associated sub-resources "
        "(identifiers, telecom, addresses, qualifications). "
        "This operation is irreversible. Returns 204 No Content on success."
    ),
    responses={**_ERR_AUTH, **_ERR_NOT_FOUND},
)
async def delete_practitioner(
    practitioner: PractitionerModel = Depends(get_authorized_practitioner),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    await practitioner_service.delete_practitioner(practitioner.practitioner_id)
    return None


# ── Sub-resource: Identifiers ──────────────────────────────────────────────


@router.post(
    "/{practitioner_id}/identifiers",
    response_model=PractitionerResponseSchema,
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("practitioner", "update"))],
    operation_id="add_practitioner_identifier",
    summary="Add a business identifier to a Practitioner (e.g. NPI, license number)",
    description=(
        "Appends a business identifier to the Practitioner, such as a National Provider Identifier (NPI), "
        "state medical license, or DEA number. "
        "`system` is a URI namespace (e.g. `http://hl7.org/fhir/sid/us-npi`); "
        "`value` is the identifier string within that namespace. "
        "Returns the full updated Practitioner resource. "
        + _CONTENT_NEG
    ),
    response_description="The updated Practitioner resource with the new identifier appended",
    responses={**_ERR_AUTH, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def add_identifier(
    payload: PractitionerIdentifierCreate,
    request: Request,
    practitioner: PractitionerModel = Depends(get_authorized_practitioner),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    updated = await practitioner_service.add_identifier(practitioner.practitioner_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Practitioner not found")
    return format_response(
        practitioner_service._to_fhir(updated),
        practitioner_service._to_plain(updated),
        request,
    )


# ── Sub-resource: Telecom ──────────────────────────────────────────────────


@router.post(
    "/{practitioner_id}/telecom",
    response_model=PractitionerResponseSchema,
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("practitioner", "update"))],
    operation_id="add_practitioner_telecom",
    summary="Add a contact point (telecom) to a Practitioner",
    description=(
        "Appends a contact point to the Practitioner. "
        "`system` values: `phone`, `fax`, `email`, `pager`, `url`, `sms`, `other`. "
        "`use` values: `home`, `work`, `temp`, `old`, `mobile`. "
        "Returns the full updated Practitioner resource. "
        + _CONTENT_NEG
    ),
    response_description="The updated Practitioner resource with the new contact point appended",
    responses={**_ERR_AUTH, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def add_telecom(
    payload: PractitionerTelecomCreate,
    request: Request,
    practitioner: PractitionerModel = Depends(get_authorized_practitioner),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    updated = await practitioner_service.add_telecom(practitioner.practitioner_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Practitioner not found")
    return format_response(
        practitioner_service._to_fhir(updated),
        practitioner_service._to_plain(updated),
        request,
    )


# ── Sub-resource: Addresses ────────────────────────────────────────────────


@router.post(
    "/{practitioner_id}/addresses",
    response_model=PractitionerResponseSchema,
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("practitioner", "update"))],
    operation_id="add_practitioner_address",
    summary="Add an address to a Practitioner",
    description=(
        "Appends a postal or physical address to the Practitioner. "
        "`use` values: `home`, `work`, `temp`, `old`, `billing`. "
        "`type` values: `postal`, `physical`, `both`. "
        "Returns the full updated Practitioner resource. "
        + _CONTENT_NEG
    ),
    response_description="The updated Practitioner resource with the new address appended",
    responses={**_ERR_AUTH, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def add_address(
    payload: PractitionerAddressCreate,
    request: Request,
    practitioner: PractitionerModel = Depends(get_authorized_practitioner),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    updated = await practitioner_service.add_address(practitioner.practitioner_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Practitioner not found")
    return format_response(
        practitioner_service._to_fhir(updated),
        practitioner_service._to_plain(updated),
        request,
    )


# ── Sub-resource: Qualifications ───────────────────────────────────────────


@router.post(
    "/{practitioner_id}/qualifications",
    response_model=PractitionerResponseSchema,
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("practitioner", "update"))],
    operation_id="add_practitioner_qualification",
    summary="Add a professional qualification to a Practitioner",
    description=(
        "Records a degree, certification, accreditation, or license held by the Practitioner "
        "(e.g. MD, board certification, DEA number). "
        "Provide a FHIR CodeableConcept `code` (system + code + display) identifying the qualification type, "
        "an optional validity `period`, and an optional `issuer` organization name. "
        "Returns the full updated Practitioner resource. "
        + _CONTENT_NEG
    ),
    response_description="The updated Practitioner resource with the new qualification appended",
    responses={**_ERR_AUTH, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def add_qualification(
    payload: PractitionerQualificationCreate,
    request: Request,
    practitioner: PractitionerModel = Depends(get_authorized_practitioner),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    updated = await practitioner_service.add_qualification(practitioner.practitioner_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Practitioner not found")
    return format_response(
        practitioner_service._to_fhir(updated),
        practitioner_service._to_plain(updated),
        request,
    )
