from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.auth.dependencies import require_permission
from app.auth.practitioner_deps import get_authorized_practitioner
from app.core.content_negotiation import format_response, format_paginated_response
from app.core.schema_utils import inline_schema
from app.di.dependencies.practitioner import get_practitioner_service
from app.models.practitioner import PractitionerModel
from app.schemas.fhir import (
    FHIRPractitionerSchema,
    FHIRPractitionerBundle,
    PaginatedPractitionerResponse,
    PlainPractitionerResponse,
)
from app.schemas.practitioner import (
    PractitionerCreateSchema,
    PractitionerPatchSchema,
    PractitionerNameCreate,
    PractitionerIdentifierCreate,
    PractitionerTelecomCreate,
    PractitionerAddressCreate,
    PractitionerPhotoCreate,
    PractitionerQualificationCreate,
    PractitionerCommunicationCreate,
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

_SINGLE_200 = {
    200: {
        "content": {
            "application/json": {"schema": inline_schema(PlainPractitionerResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRPractitionerSchema.model_json_schema())},
        }
    }
}
_SINGLE_201 = {201: _SINGLE_200[200]}
_LIST_200 = {
    200: {
        "description": "Paginated list of practitioners",
        "content": {
            "application/json": {"schema": inline_schema(PaginatedPractitionerResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FHIRPractitionerBundle.model_json_schema())},
        },
    }
}


# ── Create Practitioner ────────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("practitioner", "create"))],
    operation_id="create_practitioner",
    summary="Create a new Practitioner resource",
    description=(
        "Creates a Practitioner with core demographics (active status, gender, birth date). "
        "The caller's `sub` claim and `activeOrganizationId` from the JWT are automatically bound to the record. "
        "Names, identifiers, telecom, addresses, photos, qualifications, and communications must be added "
        "via the dedicated sub-resource endpoints after creation. "
        + _CONTENT_NEG
    ),
    response_description="The newly created Practitioner resource",
    responses={**_SINGLE_201, **_ERR_AUTH, **_ERR_VALIDATION},
)
async def create_practitioner(
    payload: PractitionerCreateSchema,
    request: Request,
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    created_by: str = request.state.user.get("sub")
    practitioner = await practitioner_service.create_practitioner(payload, payload.user_id, payload.org_id, created_by)
    return format_response(
        practitioner_service._to_fhir(practitioner),
        practitioner_service._to_plain(practitioner),
        request,
    )


# ── Get own Practitioner profile (/me) ────────────────────────────────────
# Declared before /{practitioner_id} so "me" is not matched by the int path param.


@router.get(
    "/me",
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
        **_SINGLE_200,
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
    dependencies=[Depends(require_permission("practitioner", "read"))],
    operation_id="get_practitioner_by_id",
    summary="Retrieve a Practitioner resource by public practitioner_id",
    description=(
        "Fetches a single Practitioner by its public integer `practitioner_id`. "
        "Access is subject to organization-scoped authorization. "
        + _CONTENT_NEG
    ),
    response_description="The requested Practitioner resource",
    responses={**_SINGLE_200, **_ERR_AUTH, **_ERR_NOT_FOUND},
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
    dependencies=[Depends(require_permission("practitioner", "update"))],
    operation_id="patch_practitioner",
    summary="Partially update a Practitioner resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. "
        "Patchable fields: active, gender, birth_date, deceased_boolean, deceased_datetime. "
        "To modify names, identifiers, telecom, addresses, photos, qualifications, or communications, "
        "use the dedicated sub-resource endpoints. "
        + _CONTENT_NEG
    ),
    response_description="The updated Practitioner resource",
    responses={**_SINGLE_200, **_ERR_AUTH, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_practitioner(
    payload: PractitionerPatchSchema,
    request: Request,
    practitioner: PractitionerModel = Depends(get_authorized_practitioner),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    updated_by: str = request.state.user.get("sub")
    updated = await practitioner_service.patch_practitioner(practitioner.practitioner_id, payload, updated_by)
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
    dependencies=[Depends(require_permission("practitioner", "read"))],
    operation_id="list_practitioners",
    summary="List all Practitioner resources",
    description=(
        "Returns a paginated list of Practitioners. "
        "Filter by `family_name` or `given_name` (searches across the practitioner_name table), "
        "`active`, `user_id`, or `org_id`. "
        "Use `limit` and `offset` for pagination. "
        + _CONTENT_NEG
    ),
    response_description="Paginated Practitioner resources",
    responses={**_LIST_200, **_ERR_AUTH},
)
async def list_practitioners(
    request: Request,
    family_name: Optional[str] = Query(None, description="Filter by family (last) name — partial match, case-insensitive."),
    given_name: Optional[str] = Query(None, description="Filter by given (first) name — partial match, case-insensitive."),
    active: Optional[bool] = Query(None, description="Filter by active status."),
    user_id: Optional[str] = Query(None, description="Filter by user_id (JWT sub claim)."),
    org_id: Optional[str] = Query(None, description="Filter by organization ID."),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    practitioners, total = await practitioner_service.list_practitioners(
        user_id=user_id, org_id=org_id, family_name=family_name,
        given_name=given_name, active=active,
        limit=limit, offset=offset,
    )
    return format_paginated_response(
        [practitioner_service._to_fhir(p) for p in practitioners],
        [practitioner_service._to_plain(p) for p in practitioners],
        total, limit, offset, request,
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
        "(names, identifiers, telecom, addresses, photos, qualifications, communications). "
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


# ── Sub-resource: Names ────────────────────────────────────────────────────


@router.post(
    "/{practitioner_id}/names",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("practitioner", "update"))],
    operation_id="add_practitioner_name",
    summary="Add a HumanName to a Practitioner",
    description=(
        "Appends a name to the Practitioner. "
        "Supports `use` (usual | official | temp | nickname | anonymous | old | maiden), "
        "`family`, `given[]`, `prefix[]`, `suffix[]`, `text`, and an optional validity `period`. "
        "Returns the full updated Practitioner resource. "
        + _CONTENT_NEG
    ),
    response_description="The updated Practitioner resource with the new name appended",
    responses={**_SINGLE_201, **_ERR_AUTH, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def add_name(
    payload: PractitionerNameCreate,
    request: Request,
    practitioner: PractitionerModel = Depends(get_authorized_practitioner),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    updated = await practitioner_service.add_name(practitioner.practitioner_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Practitioner not found")
    return format_response(
        practitioner_service._to_fhir(updated),
        practitioner_service._to_plain(updated),
        request,
    )


# ── Sub-resource: Identifiers ──────────────────────────────────────────────


@router.post(
    "/{practitioner_id}/identifiers",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("practitioner", "update"))],
    operation_id="add_practitioner_identifier",
    summary="Add a business identifier to a Practitioner (e.g. NPI, license, DEA)",
    description=(
        "Appends a business identifier to the Practitioner. "
        "`system` is a URI namespace (e.g. `http://hl7.org/fhir/sid/us-npi`); "
        "`value` is the identifier string within that namespace. "
        "Optional `type_system`, `type_code`, `type_display`, `type_text` describe the identifier category. "
        "Returns the full updated Practitioner resource. "
        + _CONTENT_NEG
    ),
    response_description="The updated Practitioner resource with the new identifier appended",
    responses={**_SINGLE_201, **_ERR_AUTH, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
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
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("practitioner", "update"))],
    operation_id="add_practitioner_telecom",
    summary="Add a contact point (telecom) to a Practitioner",
    description=(
        "Appends a contact point to the Practitioner. "
        "`system`: phone | fax | email | pager | url | sms | other. "
        "`use`: home | work | temp | old | mobile. "
        "Returns the full updated Practitioner resource. "
        + _CONTENT_NEG
    ),
    response_description="The updated Practitioner resource with the new contact point appended",
    responses={**_SINGLE_201, **_ERR_AUTH, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
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
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("practitioner", "update"))],
    operation_id="add_practitioner_address",
    summary="Add an address to a Practitioner",
    description=(
        "Appends a postal or physical address to the Practitioner. "
        "`use`: home | work | temp | old | billing. "
        "`type`: postal | physical | both. "
        "`line` is an array of street address lines. "
        "Returns the full updated Practitioner resource. "
        + _CONTENT_NEG
    ),
    response_description="The updated Practitioner resource with the new address appended",
    responses={**_SINGLE_201, **_ERR_AUTH, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
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


# ── Sub-resource: Photos ───────────────────────────────────────────────────


@router.post(
    "/{practitioner_id}/photos",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("practitioner", "update"))],
    operation_id="add_practitioner_photo",
    summary="Add a photo (Attachment) to a Practitioner",
    description=(
        "Appends a photo attachment to the Practitioner. "
        "Provide `data` (base64-encoded image) or `url` pointing to the image, "
        "plus `content_type` (MIME type, e.g. `image/png`). "
        "Returns the full updated Practitioner resource. "
        + _CONTENT_NEG
    ),
    response_description="The updated Practitioner resource with the new photo appended",
    responses={**_SINGLE_201, **_ERR_AUTH, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def add_photo(
    payload: PractitionerPhotoCreate,
    request: Request,
    practitioner: PractitionerModel = Depends(get_authorized_practitioner),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    updated = await practitioner_service.add_photo(practitioner.practitioner_id, payload)
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
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("practitioner", "update"))],
    operation_id="add_practitioner_qualification",
    summary="Add a professional qualification to a Practitioner",
    description=(
        "Records a degree, certification, accreditation, or license held by the Practitioner "
        "(e.g. MD, board certification, NPI, DEA number). "
        "Provide `code_system`, `code_code`, `code_display` for the qualification type "
        "(e.g. SNOMED CT code for MD), an optional validity `period`, and optional `issuer_id` / `issuer_display`. "
        "Returns the full updated Practitioner resource. "
        + _CONTENT_NEG
    ),
    response_description="The updated Practitioner resource with the new qualification appended",
    responses={**_SINGLE_201, **_ERR_AUTH, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
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


# ── Sub-resource: Communications ──────────────────────────────────────────


@router.post(
    "/{practitioner_id}/communications",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("practitioner", "update"))],
    operation_id="add_practitioner_communication",
    summary="Add a communication language to a Practitioner",
    description=(
        "Records a language the Practitioner can use in patient communication. "
        "`language_code` is an ISO-639-1 code (e.g. `en`, `fr`, `de`). "
        "Set `preferred: true` to mark this as the practitioner's preferred language. "
        "Returns the full updated Practitioner resource. "
        + _CONTENT_NEG
    ),
    response_description="The updated Practitioner resource with the new communication language appended",
    responses={**_SINGLE_201, **_ERR_AUTH, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def add_communication(
    payload: PractitionerCommunicationCreate,
    request: Request,
    practitioner: PractitionerModel = Depends(get_authorized_practitioner),
    practitioner_service: PractitionerService = Depends(get_practitioner_service),
):
    updated = await practitioner_service.add_communication(practitioner.practitioner_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Practitioner not found")
    return format_response(
        practitioner_service._to_fhir(updated),
        practitioner_service._to_plain(updated),
        request,
    )
