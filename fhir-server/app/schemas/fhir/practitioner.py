from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.fhir.common import (
    FHIRAddress,
    FHIRBundle,
    FHIRBundleEntry,
    FHIRContactPoint,
    FHIRIdentifier,
    FHIRHumanName,
    PlainIdentifier,
)


# ── FHIR (camelCase) schema ───────────────────────────────────────────────────


class FHIRQualificationCode(BaseModel):
    text: Optional[str] = None


class FHIRQualificationIssuer(BaseModel):
    display: Optional[str] = None


class FHIRQualificationIdentifier(BaseModel):
    system: Optional[str] = None
    value: Optional[str] = None


class FHIRQualification(BaseModel):
    identifier: Optional[List[FHIRQualificationIdentifier]] = None
    code: Optional[FHIRQualificationCode] = None
    issuer: Optional[FHIRQualificationIssuer] = None


class FHIRPractitionerSchema(BaseModel):
    resourceType: str = Field("Practitioner", description="Always 'Practitioner'.")
    id: str = Field(..., description="Public practitioner_id as a string.")
    active: Optional[bool] = None
    gender: Optional[str] = Field(None, description="male | female | other | unknown")
    birthDate: Optional[str] = None
    role: Optional[str] = None
    specialty: Optional[str] = None
    deceasedBoolean: Optional[bool] = None
    deceasedDateTime: Optional[str] = None
    identifier: Optional[List[FHIRIdentifier]] = None
    name: Optional[List[FHIRHumanName]] = None
    telecom: Optional[List[FHIRContactPoint]] = None
    address: Optional[List[FHIRAddress]] = None
    qualification: Optional[List[FHIRQualification]] = None


class FHIRPractitionerBundleEntry(BaseModel):
    resource: FHIRPractitionerSchema


class FHIRPractitionerBundle(FHIRBundle):
    entry: Optional[List[FHIRPractitionerBundleEntry]] = None


# ── Plain (snake_case) sub-types ──────────────────────────────────────────────


class PlainPractitionerTelecom(BaseModel):
    system: Optional[str] = Field(None, description="phone | fax | email | pager | url | sms | other")
    value: Optional[str] = None
    use: Optional[str] = Field(None, description="home | work | temp | old | mobile")
    rank: Optional[int] = None


class PlainPractitionerAddress(BaseModel):
    use: Optional[str] = Field(None, description="home | work | temp | old | billing")
    type: Optional[str] = Field(None, description="postal | physical | both")
    text: Optional[str] = None
    line: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None


class PlainQualification(BaseModel):
    identifier_system: Optional[str] = None
    identifier_value: Optional[str] = None
    code_text: Optional[str] = None
    issuer: Optional[str] = None


# ── Plain Practitioner response ───────────────────────────────────────────────


class PlainPractitionerResponse(BaseModel):
    id: int = Field(..., description="Public practitioner_id.")
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    active: Optional[bool] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    gender: Optional[str] = Field(None, description="male | female | other | unknown")
    birth_date: Optional[str] = Field(None, description="ISO 8601 date string.")
    role: Optional[str] = None
    specialty: Optional[str] = None
    deceased_boolean: Optional[bool] = None
    deceased_datetime: Optional[str] = Field(None, description="ISO 8601 datetime string.")
    identifier: Optional[List[PlainIdentifier]] = None
    telecom: Optional[List[PlainPractitionerTelecom]] = None
    address: Optional[List[PlainPractitionerAddress]] = None
    qualification: Optional[List[PlainQualification]] = None


# ── Paginated response ────────────────────────────────────────────────────────


class PaginatedPractitionerResponse(BaseModel):
    total: int = Field(..., description="Total number of matching practitioners.")
    limit: int = Field(..., description="Page size requested.")
    offset: int = Field(..., description="Number of records skipped.")
    data: List[PlainPractitionerResponse] = Field(..., description="Array of plain-JSON Practitioner objects.")
