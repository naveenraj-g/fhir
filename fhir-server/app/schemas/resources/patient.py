from datetime import date, datetime
from typing import List, Optional
from typing_extensions import Literal
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.enums import AdministrativeGender, ContactPointSystem, ContactPointUse, IdentifierUse
from app.schemas.datatypes.core import CodeableConcept, CodeableConceptSchema


# ── FHIR datatype fragments (response-only) ────────────────────────────────


class FHIRIdentifier(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    system: Optional[str] = None
    value: Optional[str] = None


class FHIRHumanName(BaseModel):
    use: Optional[str] = None
    family: Optional[str] = None
    given: List[str] = []


class FHIRTelecom(BaseModel):
    system: Optional[str] = None
    value: Optional[str] = None
    use: Optional[str] = None


class FHIRAddress(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    line: List[str] = []
    city: Optional[str] = None
    state: Optional[str] = None
    postalCode: Optional[str] = None
    country: Optional[str] = None


# ── Sub-resource create schemas ────────────────────────────────────────────


class IdentifierCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    use: Optional[IdentifierUse] = Field(None, description="Purpose of this identifier.")
    type: Optional[CodeableConcept] = Field(None, description="Description of identifier type (e.g. MRN, SSN).")
    system: Optional[str] = Field(None, description="URI of the identifier namespace.")
    value: str = Field(..., description="Identifier value within the given system.")
    period_start: Optional[datetime] = Field(None, description="Start of identifier validity period.")
    period_end: Optional[datetime] = Field(None, description="End of identifier validity period.")
    assigner: Optional[str] = Field(None, description="Display name of the organization that issued the identifier.")


class TelecomCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    system: ContactPointSystem = Field(..., description="Type of contact point.")
    value: str = Field(
        ..., description="Contact point value (phone number, email, etc.)."
    )
    use: Optional[ContactPointUse] = Field(
        None, description="Purpose of this contact point."
    )


class AddressCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    line: Optional[str] = Field(
        None, description="Street address line (e.g. '123 Main St')."
    )
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None


# ── Patient create / patch ─────────────────────────────────────────────────


class PatientCreateSchema(BaseModel):
    """Payload accepted when creating a new Patient (basic demographics only)."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "user_id": "user-uuid-123",
                "org_id": "org-uuid-456",
                "given_name": "John",
                "family_name": "Doe",
                "gender": "male",
                "birth_date": "1985-04-12",
                "active": True,
            }
        },
    )

    user_id: Optional[str] = None
    org_id: Optional[str] = None
    given_name: Optional[str] = Field(None, max_length=100)
    family_name: Optional[str] = Field(None, max_length=100)
    gender: Optional[AdministrativeGender] = None
    birth_date: Optional[date] = None
    active: Optional[bool] = True
    deceased_boolean: Optional[bool] = False
    deceased_datetime: Optional[datetime] = None


class PatientPatchSchema(BaseModel):
    """Partial-update payload — only supplied fields are written."""

    model_config = ConfigDict(extra="forbid")

    given_name: Optional[str] = Field(None, max_length=100)
    family_name: Optional[str] = Field(None, max_length=100)
    gender: Optional[AdministrativeGender] = None
    birth_date: Optional[date] = None
    active: Optional[bool] = None
    deceased_boolean: Optional[bool] = None
    deceased_datetime: Optional[datetime] = None


# ── Plain response sub-schemas ─────────────────────────────────────────────


class PatientIdentifierSchema(BaseModel):
    use: Optional[str] = None
    type: Optional[CodeableConceptSchema] = None
    system: Optional[str] = None
    value: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    assigner: Optional[str] = None


class PatientTelecomSchema(BaseModel):
    system: Optional[str] = None
    value: Optional[str] = None
    use: Optional[str] = None


class PatientAddressSchema(BaseModel):
    line: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None


# ── Patient response ───────────────────────────────────────────────────────


class PatientResponseSchema(BaseModel):
    """
    Plain snake_case Patient resource returned by all read/write endpoints.

    - `id` is the PUBLIC patient_id (e.g. 10001) — the internal DB pk is
      never included.
    - Sub-resources (identifier, telecom, address) are omitted when empty.
    """

    model_config = ConfigDict(populate_by_name=True)

    id: int
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    active: Optional[bool] = None
    deceased_boolean: Optional[bool] = None
    deceased_datetime: Optional[datetime] = None
    identifier: Optional[List[PatientIdentifierSchema]] = None
    telecom: Optional[List[PatientTelecomSchema]] = None
    address: Optional[List[PatientAddressSchema]] = None
