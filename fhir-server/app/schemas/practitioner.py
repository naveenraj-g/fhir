from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.enums import (
    AdministrativeGender,
    ContactPointSystem,
    ContactPointUse,
    AddressUse,
    AddressType,
    IdentifierUse,
    PractitionerRole,
)
from app.schemas.datatypes.core import CodeableConcept, CodeableConceptSchema


# ── FHIR datatype fragments (response-only) ────────────────────────────────


class FHIRPractitionerIdentifier(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    system: Optional[str] = None
    value: Optional[str] = None
    use: Optional[str] = None


class FHIRHumanName(BaseModel):
    use: Optional[str] = None
    family: Optional[str] = None
    given: List[str] = []


class FHIRPractitionerTelecom(BaseModel):
    system: Optional[str] = None
    value: Optional[str] = None
    use: Optional[str] = None
    rank: Optional[int] = None


class FHIRPractitionerAddress(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    use: Optional[str] = None
    type: Optional[str] = None
    text: Optional[str] = None
    line: List[str] = []
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    postalCode: Optional[str] = None
    country: Optional[str] = None


class FHIRQualificationIdentifier(BaseModel):
    system: Optional[str] = None
    value: Optional[str] = None


class FHIRQualificationCode(BaseModel):
    text: Optional[str] = None


class FHIRQualificationIssuer(BaseModel):
    display: Optional[str] = None


class FHIRQualification(BaseModel):
    identifier: Optional[List[FHIRQualificationIdentifier]] = None
    code: Optional[FHIRQualificationCode] = None
    issuer: Optional[FHIRQualificationIssuer] = None


# ── Sub-resource create schemas ────────────────────────────────────────────


class PractitionerIdentifierCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    use: Optional[IdentifierUse] = Field(None, description="Purpose of this identifier.")
    type: Optional[CodeableConcept] = Field(None, description="Description of identifier type (e.g. NPI, DEA, license).")
    system: Optional[str] = Field(None, description="URI of the identifier namespace (e.g. NPI system).")
    value: str = Field(..., description="Identifier value (e.g. NPI number, license number).")
    period_start: Optional[datetime] = Field(None, description="Start of identifier validity period.")
    period_end: Optional[datetime] = Field(None, description="End of identifier validity period.")
    assigner: Optional[str] = Field(None, description="Display name of the organization that issued the identifier.")



class PractitionerTelecomCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    system: ContactPointSystem = Field(..., description="Type of contact point.")
    value: str = Field(..., description="Contact value (phone number, email address, etc.).")
    use: Optional[ContactPointUse] = Field(None, description="Purpose of this contact point.")
    rank: Optional[int] = Field(None, ge=1, description="Preferred contact order (1 = most preferred).")


class PractitionerAddressCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    use: Optional[AddressUse] = Field(None, description="Purpose of this address.")
    type: Optional[AddressType] = Field(None, description="postal | physical | both.")
    text: Optional[str] = Field(None, description="Full address as plain text.")
    line: Optional[str] = Field(None, description="Street address line(s), comma-separated for multiple.")
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None


class PractitionerQualificationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    identifier_system: Optional[str] = Field(None, description="Namespace URI for the qualification identifier.")
    identifier_value: Optional[str] = Field(None, description="Qualification or license number.")
    code_text: Optional[str] = Field(None, description="Human-readable qualification type, e.g. 'MD - Doctor of Medicine'.")
    issuer: Optional[str] = Field(None, description="Display name of the issuing organization.")


# ── Practitioner create / patch ────────────────────────────────────────────


class PractitionerCreateSchema(BaseModel):
    """
    Payload accepted when creating a new Practitioner (core demographics only).
    Sub-resources (names, identifiers, telecom, addresses, qualifications) are
    added via their respective POST sub-resource endpoints.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "given_name": "Jane",
                "family_name": "Smith",
                "active": True,
                "gender": "female",
                "birth_date": "1978-03-15",
            }
        },
    )

    given_name: Optional[str] = Field(None, max_length=100)
    family_name: Optional[str] = Field(None, max_length=100)
    active: Optional[bool] = True
    gender: Optional[AdministrativeGender] = None
    birth_date: Optional[date] = None
    role: Optional[PractitionerRole] = None
    specialty: Optional[str] = Field(None, max_length=200)
    deceased_boolean: Optional[bool] = False
    deceased_datetime: Optional[datetime] = None


class PractitionerPatchSchema(BaseModel):
    """Partial-update payload — only supplied fields are written."""

    model_config = ConfigDict(extra="forbid")

    given_name: Optional[str] = Field(None, max_length=100)
    family_name: Optional[str] = Field(None, max_length=100)
    active: Optional[bool] = None
    gender: Optional[AdministrativeGender] = None
    birth_date: Optional[date] = None
    role: Optional[PractitionerRole] = None
    specialty: Optional[str] = Field(None, max_length=200)
    deceased_boolean: Optional[bool] = None
    deceased_datetime: Optional[datetime] = None


# ── Plain response sub-schemas ─────────────────────────────────────────────


class PractitionerIdentifierSchema(BaseModel):
    use: Optional[str] = None
    type: Optional[CodeableConceptSchema] = None
    system: Optional[str] = None
    value: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    assigner: Optional[str] = None


class PractitionerTelecomSchema(BaseModel):
    system: Optional[str] = None
    value: Optional[str] = None
    use: Optional[str] = None
    rank: Optional[int] = None


class PractitionerAddressSchema(BaseModel):
    use: Optional[str] = None
    type: Optional[str] = None
    text: Optional[str] = None
    line: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None


class PractitionerQualificationSchema(BaseModel):
    identifier_system: Optional[str] = None
    identifier_value: Optional[str] = None
    code_text: Optional[str] = None
    issuer: Optional[str] = None


# ── Practitioner response ──────────────────────────────────────────────────


class PractitionerResponseSchema(BaseModel):
    """
    Plain snake_case Practitioner resource returned by all read/write endpoints.

    - `id` is the PUBLIC practitioner_id (e.g. 30001) — the internal DB pk is never included.
    - Sub-resources are omitted when empty.
    """

    model_config = ConfigDict(populate_by_name=True)

    id: int
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    active: Optional[bool] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    role: Optional[str] = None
    specialty: Optional[str] = None
    deceased_boolean: Optional[bool] = None
    deceased_datetime: Optional[datetime] = None
    identifier: Optional[List[PractitionerIdentifierSchema]] = None
    telecom: Optional[List[PractitionerTelecomSchema]] = None
    address: Optional[List[PractitionerAddressSchema]] = None
    qualification: Optional[List[PractitionerQualificationSchema]] = None
