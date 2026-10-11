"""
Input schemas for the CareTeam resource (FHIR R4) — fhir-gql gateway copy.

Mirrors the fhir-server contract; the fhir-server remains the source of truth for persistence.

https://www.hl7.org/fhir/R4/careteam.html

References are `Type/id` strings (format + allowed type validated, existence never).
Invariant ctm-1: participant.onBehalfOf can only be populated when participant.member is a Practitioner.
"""

from datetime import datetime, timezone
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.enums import CareTeamStatus


def _utc(d: datetime) -> datetime:
    return d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d


def _check_period(start: Optional[datetime], end: Optional[datetime], what: str = "period") -> None:
    if start and end and _utc(end) < _utc(start):
        raise ValueError(f"{what}_end must not be before {what}_start.")


class CareTeamIdentifierInput(BaseModel):
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


class CareTeamCodeableConceptInput(BaseModel):
    """CodeableConcept list entry (category, participant.role, reasonCode)."""

    model_config = ConfigDict(extra="forbid")

    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class CareTeamReferenceInput(BaseModel):
    """Reference list entry (reasonReference, managingOrganization)."""

    model_config = ConfigDict(extra="forbid")

    reference: str = Field(..., description="FHIR reference, e.g. 'Condition/120001' or 'Organization/190001'.")
    reference_display: Optional[str] = None


class CareTeamParticipantInput(BaseModel):
    """participant[] — role[], member, onBehalfOf, period."""

    model_config = ConfigDict(extra="forbid")

    role: Optional[List[CareTeamCodeableConceptInput]] = Field(None, description="Type of involvement.")
    member: Optional[str] = Field(
        None, description="Practitioner|PractitionerRole|RelatedPerson|Patient|Organization|CareTeam reference, e.g. 'Practitioner/30001'."
    )
    member_display: Optional[str] = None
    on_behalf_of: Optional[str] = Field(
        None, description="Organization reference. Only allowed when `member` is a Practitioner (ctm-1)."
    )
    on_behalf_of_display: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None

    @model_validator(mode="after")
    def _rules(self):
        _check_period(self.period_start, self.period_end, "period")
        # ctm-1: onBehalfOf can only be populated when member is a Practitioner
        if self.on_behalf_of and self.member and not self.member.startswith("Practitioner/"):
            raise ValueError("ctm-1: on_behalf_of can only be populated when member is a Practitioner.")
        return self


class CareTeamTelecomInput(BaseModel):
    """telecom[] — ContactPoint."""

    model_config = ConfigDict(extra="forbid")

    system: Optional[Literal["phone", "fax", "email", "pager", "url", "sms", "other"]] = None
    value: Optional[str] = None
    use: Optional[Literal["home", "work", "temp", "old", "mobile"]] = None
    rank: Optional[int] = Field(None, ge=1)
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None

    @model_validator(mode="after")
    def _rules(self):
        _check_period(self.period_start, self.period_end, "period")
        if self.value and not self.system:
            raise ValueError("cpt-2: a system is required if a value is provided.")
        return self


class CareTeamNoteInput(BaseModel):
    """note[] — Annotation (author[x] is a string or a Reference)."""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(..., description="Annotation text content (markdown).")
    time: Optional[datetime] = None
    author_string: Optional[str] = None
    author_reference: Optional[str] = Field(None, description="Practitioner|Patient|RelatedPerson|Organization reference.")
    author_reference_display: Optional[str] = None

    @model_validator(mode="after")
    def _author_one(self):
        if self.author_string and self.author_reference:
            raise ValueError("note.author[x]: supply authorString or authorReference, not both.")
        return self


_CHILD_LISTS = (
    "identifier", "category", "participant", "reason_code", "reason_reference", "managing_organization", "telecom", "note",
)


class CareTeamCreateSchema(BaseModel):
    """Request body for POST /care-teams. Every element is optional in R4 (status is 0..1)."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "user_id": "user-123",
                "org_id": "org-456",
                "status": "active",
                "name": "Diabetes care team",
                "subject": "Patient/10001",
                "period_start": "2024-01-01T00:00:00Z",
                "category": [{"coding_system": "http://loinc.org", "coding_code": "LA27976-2", "text": "Encounter-focused care team"}],
                "participant": [
                    {
                        "role": [{"coding_system": "http://snomed.info/sct", "coding_code": "17561000", "text": "Cardiologist"}],
                        "member": "Practitioner/30001",
                        "on_behalf_of": "Organization/190001",
                    }
                ],
                "managing_organization": [{"reference": "Organization/190001"}],
                "telecom": [{"system": "phone", "value": "555-0100"}],
            }
        },
    )

    user_id: Optional[str] = Field(None, description="JWT sub of the record owner.")
    org_id: Optional[str] = Field(None, description="Active organization ID from JWT.")
    created_by: Optional[str] = None

    status: Optional[CareTeamStatus] = Field(None, description="proposed|active|suspended|inactive|entered-in-error")
    name: Optional[str] = Field(None, description="Name of the team.")
    subject: Optional[str] = Field(None, description="Who the care team is for: Patient|Group reference, e.g. 'Patient/10001'.")
    subject_display: Optional[str] = None
    encounter: Optional[str] = Field(None, description="Encounter reference, e.g. 'Encounter/20001'.")
    encounter_display: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None

    identifier: Optional[List[CareTeamIdentifierInput]] = None
    category: Optional[List[CareTeamCodeableConceptInput]] = None
    participant: Optional[List[CareTeamParticipantInput]] = None
    reason_code: Optional[List[CareTeamCodeableConceptInput]] = None
    reason_reference: Optional[List[CareTeamReferenceInput]] = Field(None, description="Condition references.")
    managing_organization: Optional[List[CareTeamReferenceInput]] = Field(None, description="Organization references.")
    telecom: Optional[List[CareTeamTelecomInput]] = None
    note: Optional[List[CareTeamNoteInput]] = None

    @model_validator(mode="after")
    def _period(self):
        _check_period(self.period_start, self.period_end)
        return self


class CareTeamPatchSchema(BaseModel):
    """
    Request body for PATCH /care-teams/{id}. All optional.

    Child lists (identifier, category, participant, reason_code, reason_reference, managing_organization,
    telecom, note) use REPLACE semantics: a list that is sent replaces the stored one in full, `[]` (or null)
    clears it, an omitted list is left untouched. References are `Type/id` strings; null clears one.
    """

    model_config = ConfigDict(extra="forbid")

    status: Optional[CareTeamStatus] = None
    name: Optional[str] = None
    subject: Optional[str] = None
    subject_display: Optional[str] = None
    encounter: Optional[str] = None
    encounter_display: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    updated_by: Optional[str] = None

    identifier: Optional[List[CareTeamIdentifierInput]] = None
    category: Optional[List[CareTeamCodeableConceptInput]] = None
    participant: Optional[List[CareTeamParticipantInput]] = None
    reason_code: Optional[List[CareTeamCodeableConceptInput]] = None
    reason_reference: Optional[List[CareTeamReferenceInput]] = None
    managing_organization: Optional[List[CareTeamReferenceInput]] = None
    telecom: Optional[List[CareTeamTelecomInput]] = None
    note: Optional[List[CareTeamNoteInput]] = None

    @model_validator(mode="after")
    def _period(self):
        _check_period(self.period_start, self.period_end)
        return self


# ── Search ─────────────────────────────────────────────────────────────────────


class ListCareTeamsSchema(BaseModel):
    """
    Search parameters for GET /care-teams — the FHIR R4 CareTeam search params plus `_id` and `_lastUpdated`.

    The router builds this from explicitly declared Query parameters (`_id` and `_lastUpdated` are not valid
    Python identifiers); the service then forwards it to the fhir-server under the FHIR parameter names.

    Token params (`identifier`, `status`, `category`): `code` | `system|code` | `|code` | `system|`; comma = OR.
    Reference params (`subject`, `patient`, `encounter`, `participant`): `Type/id` or bare numeric id.
    Date params (`date`, `last_updated`): optional prefix eq|ne|gt|lt|ge|le|sa|eb|ap; repeat for AND.
    """

    model_config = ConfigDict(extra="forbid")

    id: Optional[str] = Field(None, description="_id — public care_team_id(s), comma-separated.")
    identifier: Optional[str] = Field(None, description="Token `[system|]value` of CareTeam.identifier.")
    status: Optional[str] = Field(None, description="Token: proposed|active|suspended|inactive|entered-in-error (comma = OR).")
    category: Optional[str] = Field(None, description="Token `[system|]code` of CareTeam.category.")
    subject: Optional[str] = Field(None, description="Subject reference (Patient|Group).")
    patient: Optional[str] = Field(None, description="Subject patient reference: 'Patient/10001' or '10001'.")
    encounter: Optional[str] = Field(None, description="Encounter reference: 'Encounter/20001' or '20001'.")
    participant: Optional[str] = Field(None, description="participant.member reference (Practitioner, PractitionerRole, RelatedPerson, Patient, Organization, CareTeam).")
    date: Optional[List[str]] = Field(None, description="Team period with optional prefix e.g. 'ge2024-01-01'.")
    last_updated: Optional[List[str]] = Field(None, description="_lastUpdated instant with optional prefix.")
    # Tenant-scoping filters — org_id is mandatory, user_id optional.
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
        allowed = {s.value for s in CareTeamStatus}
        bad = [t for t in v.split(",") if t.strip() and t.strip() not in allowed]
        if bad:
            raise ValueError(f"Invalid status {bad}. Allowed: {sorted(allowed)}")
        return v
