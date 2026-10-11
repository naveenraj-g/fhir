"""
Input schemas for Flag endpoints (fhir-gql gateway).

Mirrors the fhir-server input contract so invalid bodies are rejected at the gateway
with a 422 before any network call. References are `Type/id` strings; only their
format is validated. The child lists `identifier` and `category` are patchable with
REPLACE semantics (send `[]` to clear one; null is dropped by the gateway).
"""

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.enums import FlagStatus


class FlagIdentifierInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    use: Optional[str] = None
    type_system: Optional[str] = None
    type_code: Optional[str] = None
    type_display: Optional[str] = None
    type_text: Optional[str] = None
    system: Optional[str] = None
    value: str = Field(..., description="Identifier value.")
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    assigner: Optional[str] = None


class FlagCategoryInput(BaseModel):
    """category — CodeableConcept (one coding + free text)."""

    model_config = ConfigDict(extra="forbid")

    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class FlagCreateSchema(BaseModel):
    """Request body for POST /flags."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "user_id": "user-123",
                "org_id": "org-456",
                "status": "active",
                "category": [
                    {
                        "coding_system": "http://terminology.hl7.org/CodeSystem/flag-category",
                        "coding_code": "safety",
                        "coding_display": "Safety",
                    }
                ],
                "code_system": "http://snomed.info/sct",
                "code_code": "91936005",
                "code_display": "Allergy to penicillin",
                "code_text": "Penicillin allergy — check before prescribing",
                "subject": "Patient/10001",
                "period_start": "2024-03-15T00:00:00Z",
                "encounter_id": 20001,
                "author": "Practitioner/30001",
            }
        },
    )

    user_id: Optional[str] = Field(None, description="JWT sub of the record owner.")
    org_id: Optional[str] = Field(None, description="Active organization ID from JWT.")
    created_by: Optional[str] = None

    status: FlagStatus = Field(..., description="active|inactive|entered-in-error")

    code_system: Optional[str] = None
    code_code: Optional[str] = None
    code_display: Optional[str] = None
    code_text: Optional[str] = Field(None, description="The message shown to the user.")

    subject: str = Field(
        ...,
        description="FHIR reference: Patient|Location|Group|Organization|Practitioner|PlanDefinition|Medication|Procedure, "
        "e.g. 'Patient/10001'.",
    )
    subject_display: Optional[str] = None

    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = Field(None, description="Leave empty while the flag is still active.")

    encounter_id: Optional[int] = Field(None, description="Public encounter_id of the linked Encounter.")
    encounter_display: Optional[str] = None

    author: Optional[str] = Field(
        None, description="FHIR reference: Device|Organization|Patient|Practitioner|PractitionerRole."
    )
    author_display: Optional[str] = None

    identifier: Optional[List[FlagIdentifierInput]] = None
    category: Optional[List[FlagCategoryInput]] = None

    @model_validator(mode="after")
    def _code_and_period(self):
        """Flag.code is 1..1 — a coding or a text message must be present; the period must not run backwards."""
        if not any([self.code_system, self.code_code, self.code_display, self.code_text]):
            raise ValueError("code is required: provide code_code and/or code_text (code_display, code_system).")
        if self.period_start and self.period_end:
            # Treat naive timestamps as UTC so a mix of "…Z" and zone-less values compares safely.
            as_utc = lambda d: d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d  # noqa: E731
            if as_utc(self.period_end) < as_utc(self.period_start):
                raise ValueError("period_end must not be before period_start.")
        return self


class FlagPatchSchema(BaseModel):
    """
    Request body for PATCH /flags/{id}. All optional.

    Typical use: set `period_end` / `status: inactive` to retire a flag. The child lists
    (`identifier`, `category`) are patchable with REPLACE semantics: a list that is sent
    replaces the stored one in full, `[]` (or null) clears it, an omitted list is left
    untouched. References are `Type/id` strings; send null to clear an optional one.
    `status` and `subject` cannot be null.
    """

    model_config = ConfigDict(extra="forbid")

    status: Optional[FlagStatus] = Field(None, description="Cannot be null.")
    code_system: Optional[str] = None
    code_code: Optional[str] = None
    code_display: Optional[str] = None
    code_text: Optional[str] = None
    subject: Optional[str] = Field(None, description="Cannot be null.")
    subject_display: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    encounter_id: Optional[int] = Field(None, description="Public encounter_id; null unlinks.")
    encounter_display: Optional[str] = None
    author: Optional[str] = None
    author_display: Optional[str] = None
    updated_by: Optional[str] = None

    identifier: Optional[List[FlagIdentifierInput]] = None
    category: Optional[List[FlagCategoryInput]] = None

    @field_validator("status", "subject")
    @classmethod
    def _not_null(cls, v):
        if v is None:
            raise ValueError("must not be null")
        return v


# ── List / search ──────────────────────────────────────────────────────────────


class ListFlagsSchema(BaseModel):
    """
    Search parameters for GET /flags — the FHIR R4 Flag search params
    (author, date, encounter, identifier, patient, subject) plus `_id`, `_lastUpdated`
    and the convenience filters status / category / code.

    The router builds this from explicitly declared Query parameters (`_id` and
    `_lastUpdated` are not valid Python identifiers); the service then forwards it
    to the fhir-server.

    Token params (`status`, `identifier`, `category`, `code`): `code` | `system|code` | `|code` | `system|`; comma = OR.
    Reference params (`subject`, `patient`, `encounter`, `author`): `Type/id` or bare numeric id.
    Date params (`date`, `last_updated`): optional prefix eq|ne|gt|lt|ge|le|sa|eb|ap; repeat for AND.
    """

    model_config = ConfigDict(extra="forbid")

    id: Optional[str] = Field(None, description="_id — public flag_id(s), comma-separated.")
    identifier: Optional[str] = Field(None, description="Token `[system|]value` of Flag.identifier.")
    status: Optional[str] = Field(None, description="Token: active|inactive|entered-in-error (comma = OR).")
    category: Optional[str] = Field(None, description="Token `[system|]code` of Flag.category.")
    code: Optional[str] = Field(None, description="Token `[system|]code` of Flag.code.")
    subject: Optional[str] = Field(None, description="Subject reference (Patient, Location, Group, ...).")
    patient: Optional[str] = Field(None, description="Subject patient reference: 'Patient/10001' or '10001'.")
    encounter: Optional[str] = Field(None, description="Encounter reference: 'Encounter/20001' or '20001'.")
    author: Optional[str] = Field(None, description="Author reference: Device|Organization|Patient|Practitioner|PractitionerRole.")
    date: Optional[List[str]] = Field(None, description="Flag active period with optional prefix e.g. 'ge2024-01-01'.")
    last_updated: Optional[List[str]] = Field(None, description="_lastUpdated instant with optional prefix.")
    # Tenant-scoping filters — optional so admin callers can query across users/orgs.
    user_id: Optional[str] = Field(None, description="Optional: restrict to records owned by this user (JWT subject).")
    org_id: str = Field(..., min_length=1, description="Tenant organization ID — mandatory scope of every search.")
    limit: int = Field(50, ge=1, le=200, description="Max records per page.")
    offset: int = Field(0, ge=0, description="Records to skip.")

    @field_validator("status")
    @classmethod
    def _validate_status_tokens(cls, v: Optional[str]) -> Optional[str]:
        """Reject unknown status codes early (comma-separated OR list allowed) with a gateway 422."""
        if v is None:
            return v
        allowed = {s.value for s in FlagStatus}
        bad = [t for t in v.split(",") if t.strip() and t.strip() not in allowed]
        if bad:
            raise ValueError(f"Invalid status {bad}. Allowed: {sorted(allowed)}")
        return v
