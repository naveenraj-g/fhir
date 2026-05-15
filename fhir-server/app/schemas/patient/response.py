from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.common.fhir import (
    FHIRAddress,
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRContactPoint,
    FHIRHumanName,
    FHIRIdentifier,
    FHIRPeriod,
    FHIRReference,
)


# ── FHIR contact BackboneElement sub-schemas ───────────────────────────────────


class FHIRPatientContact(BaseModel):
    relationship: Optional[List[FHIRCodeableConcept]] = None
    role: Optional[List[FHIRCodeableConcept]] = None
    name: Optional[FHIRHumanName] = None
    additionalName: Optional[List[FHIRHumanName]] = None
    telecom: Optional[List[FHIRContactPoint]] = None
    address: Optional[FHIRAddress] = None
    additionalAddress: Optional[List[FHIRAddress]] = None
    gender: Optional[str] = Field(None, description="male|female|other|unknown")
    organization: Optional[FHIRReference] = None
    period: Optional[FHIRPeriod] = None


# ── FHIR communication BackboneElement sub-schema ─────────────────────────────


class FHIRPatientCommunication(BaseModel):
    language: FHIRCodeableConcept
    preferred: Optional[bool] = None


# ── FHIR link BackboneElement sub-schema ──────────────────────────────────────


class FHIRPatientLink(BaseModel):
    other: FHIRReference
    type: str = Field(..., description="replaced-by|replaces|refer|seealso")


# ── FHIR Attachment (photo) ────────────────────────────────────────────────────


class FHIRAttachment(BaseModel):
    contentType: Optional[str] = None
    language: Optional[str] = None
    data: Optional[str] = None
    url: Optional[str] = None
    size: Optional[int] = None
    hash: Optional[str] = None
    title: Optional[str] = None
    creation: Optional[str] = None


# ── FHIR (camelCase) Patient schema ───────────────────────────────────────────


class FHIRPatientSchema(BaseModel):
    resourceType: str = Field("Patient", description="Always 'Patient'.")
    id: str = Field(..., description="Public patient_id as a string.")
    active: Optional[bool] = None
    gender: Optional[str] = Field(None, description="male|female|other|unknown")
    birthDate: Optional[str] = Field(None, description="ISO 8601 date (YYYY-MM-DD).")
    deceasedBoolean: Optional[bool] = None
    deceasedDateTime: Optional[str] = Field(None, description="ISO 8601 datetime.")
    maritalStatus: Optional[FHIRCodeableConcept] = None
    multipleBirthBoolean: Optional[bool] = None
    multipleBirthInteger: Optional[int] = None
    name: Optional[List[FHIRHumanName]] = None
    identifier: Optional[List[FHIRIdentifier]] = None
    telecom: Optional[List[FHIRContactPoint]] = None
    address: Optional[List[FHIRAddress]] = None
    photo: Optional[List[FHIRAttachment]] = None
    contact: Optional[List[FHIRPatientContact]] = None
    communication: Optional[List[FHIRPatientCommunication]] = None
    generalPractitioner: Optional[List[FHIRReference]] = None
    managingOrganization: Optional[FHIRReference] = None
    link: Optional[List[FHIRPatientLink]] = None


class FHIRPatientBundleEntry(BaseModel):
    resource: FHIRPatientSchema


class FHIRPatientBundle(FHIRBundle):
    entry: Optional[List[FHIRPatientBundleEntry]] = None


# ── Plain (snake_case) sub-types ───────────────────────────────────────────────


class PlainPatientName(BaseModel):
    use: Optional[str] = None
    text: Optional[str] = None
    family: Optional[str] = None
    given: Optional[List[str]] = None
    prefix: Optional[List[str]] = None
    suffix: Optional[List[str]] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None


class PlainPatientIdentifier(BaseModel):
    use: Optional[str] = None
    type_system: Optional[str] = None
    type_code: Optional[str] = None
    type_display: Optional[str] = None
    type_text: Optional[str] = None
    system: Optional[str] = None
    value: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    assigner: Optional[str] = None


class PlainPatientTelecom(BaseModel):
    system: Optional[str] = Field(None, description="phone|fax|email|pager|url|sms|other")
    value: Optional[str] = None
    use: Optional[str] = Field(None, description="home|work|temp|old|mobile")
    rank: Optional[int] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None


class PlainPatientAddress(BaseModel):
    use: Optional[str] = None
    type: Optional[str] = None
    text: Optional[str] = None
    line: Optional[List[str]] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None


class PlainPatientPhoto(BaseModel):
    content_type: Optional[str] = None
    language: Optional[str] = None
    data: Optional[str] = None
    url: Optional[str] = None
    size: Optional[int] = None
    hash: Optional[str] = None
    title: Optional[str] = None
    creation: Optional[str] = None


class PlainContactRelationship(BaseModel):
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class PlainContactRole(BaseModel):
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class PlainContactAdditionalName(BaseModel):
    use: Optional[str] = None
    text: Optional[str] = None
    family: Optional[str] = None
    given: Optional[List[str]] = None
    prefix: Optional[List[str]] = None
    suffix: Optional[List[str]] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None


class PlainContactAdditionalAddress(BaseModel):
    use: Optional[str] = None
    type: Optional[str] = None
    text: Optional[str] = None
    line: Optional[List[str]] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None


class PlainContactTelecom(BaseModel):
    system: Optional[str] = None
    value: Optional[str] = None
    use: Optional[str] = None
    rank: Optional[int] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None


class PlainPatientContact(BaseModel):
    relationship: Optional[List[PlainContactRelationship]] = None
    role: Optional[List[PlainContactRole]] = None
    name_use: Optional[str] = None
    name_text: Optional[str] = None
    name_family: Optional[str] = None
    name_given: Optional[List[str]] = None
    name_prefix: Optional[List[str]] = None
    name_suffix: Optional[List[str]] = None
    telecom: Optional[List[PlainContactTelecom]] = None
    additional_name: Optional[List[PlainContactAdditionalName]] = None
    address_use: Optional[str] = None
    address_type: Optional[str] = None
    address_text: Optional[str] = None
    address_line: Optional[List[str]] = None
    address_city: Optional[str] = None
    address_district: Optional[str] = None
    address_state: Optional[str] = None
    address_postal_code: Optional[str] = None
    address_country: Optional[str] = None
    address_period_start: Optional[str] = None
    address_period_end: Optional[str] = None
    additional_address: Optional[List[PlainContactAdditionalAddress]] = None
    gender: Optional[str] = None
    organization_type: Optional[str] = None
    organization_id: Optional[int] = None
    organization_display: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None


class PlainPatientCommunication(BaseModel):
    language_system: Optional[str] = None
    language_code: Optional[str] = None
    language_display: Optional[str] = None
    language_text: Optional[str] = None
    preferred: Optional[bool] = None


class PlainPatientGeneralPractitioner(BaseModel):
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    reference_display: Optional[str] = None


class PlainPatientLink(BaseModel):
    other_type: Optional[str] = None
    other_id: Optional[int] = None
    other_display: Optional[str] = None
    type: Optional[str] = None


# ── Plain Patient response ─────────────────────────────────────────────────────


class PlainPatientResponse(BaseModel):
    id: int = Field(..., description="Public patient_id.")
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    active: Optional[bool] = None
    gender: Optional[str] = Field(None, description="male|female|other|unknown")
    birth_date: Optional[str] = Field(None, description="ISO 8601 date (YYYY-MM-DD).")
    deceased_boolean: Optional[bool] = None
    deceased_datetime: Optional[str] = Field(None, description="ISO 8601 datetime.")
    marital_status_system: Optional[str] = None
    marital_status_code: Optional[str] = None
    marital_status_display: Optional[str] = None
    marital_status_text: Optional[str] = None
    multiple_birth_boolean: Optional[bool] = None
    multiple_birth_integer: Optional[int] = None
    managing_organization_type: Optional[str] = None
    managing_organization_id: Optional[int] = None
    managing_organization_display: Optional[str] = None
    created_at: Optional[str] = Field(None, description="ISO 8601 datetime when record was created.")
    updated_at: Optional[str] = Field(None, description="ISO 8601 datetime when record was last updated.")
    name: Optional[List[PlainPatientName]] = None
    identifier: Optional[List[PlainPatientIdentifier]] = None
    telecom: Optional[List[PlainPatientTelecom]] = None
    address: Optional[List[PlainPatientAddress]] = None
    photo: Optional[List[PlainPatientPhoto]] = None
    contact: Optional[List[PlainPatientContact]] = None
    communication: Optional[List[PlainPatientCommunication]] = None
    general_practitioner: Optional[List[PlainPatientGeneralPractitioner]] = None
    link: Optional[List[PlainPatientLink]] = None


# ── Paginated response ─────────────────────────────────────────────────────────


class PaginatedPatientResponse(BaseModel):
    total: int = Field(..., description="Total number of matching patients.")
    limit: int = Field(..., description="Page size requested.")
    offset: int = Field(..., description="Number of records skipped.")
    data: List[PlainPatientResponse] = Field(..., description="Array of plain-JSON Patient objects.")
