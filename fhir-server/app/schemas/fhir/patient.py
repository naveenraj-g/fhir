from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.fhir.common import (
    FHIRAddress,
    FHIRBundle,
    FHIRBundleEntry,
    FHIRContactPoint,
    FHIRIdentifier,
    FHIRHumanName,
    PlainCoding,
    PlainIdentifier,
    PlainIdentifierType,
)


# ── FHIR (camelCase) schema ───────────────────────────────────────────────────


class FHIRPatientSchema(BaseModel):
    resourceType: str = Field("Patient", description="Always 'Patient'.")
    id: str = Field(..., description="Public patient_id as a string.")
    active: Optional[bool] = None
    gender: Optional[str] = Field(None, description="male | female | other | unknown")
    birthDate: Optional[str] = Field(None, description="ISO 8601 date string (YYYY-MM-DD).")
    deceasedBoolean: Optional[bool] = None
    deceasedDateTime: Optional[str] = None
    name: Optional[List[FHIRHumanName]] = None
    identifier: Optional[List[FHIRIdentifier]] = None
    telecom: Optional[List[FHIRContactPoint]] = None
    address: Optional[List[FHIRAddress]] = None


class FHIRPatientBundleEntry(BaseModel):
    resource: FHIRPatientSchema


class FHIRPatientBundle(FHIRBundle):
    entry: Optional[List[FHIRPatientBundleEntry]] = None


# ── Plain (snake_case) sub-types ──────────────────────────────────────────────


class PlainPatientTelecom(BaseModel):
    system: Optional[str] = Field(None, description="phone | fax | email | pager | url | sms | other")
    value: Optional[str] = None
    use: Optional[str] = Field(None, description="home | work | temp | old | mobile")


class PlainPatientAddress(BaseModel):
    line: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None


# ── Plain Patient response ────────────────────────────────────────────────────


class PlainPatientResponse(BaseModel):
    id: int = Field(..., description="Public patient_id.")
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    gender: Optional[str] = Field(None, description="male | female | other | unknown")
    birth_date: Optional[str] = Field(None, description="ISO 8601 date string.")
    active: Optional[bool] = None
    deceased_boolean: Optional[bool] = None
    deceased_datetime: Optional[str] = Field(None, description="ISO 8601 datetime string.")
    identifier: Optional[List[PlainIdentifier]] = None
    telecom: Optional[List[PlainPatientTelecom]] = None
    address: Optional[List[PlainPatientAddress]] = None


# ── Paginated response ────────────────────────────────────────────────────────


class PaginatedPatientResponse(BaseModel):
    total: int = Field(..., description="Total number of matching patients.")
    limit: int = Field(..., description="Page size requested.")
    offset: int = Field(..., description="Number of records skipped.")
    data: List[PlainPatientResponse] = Field(..., description="Array of plain-JSON Patient objects.")
