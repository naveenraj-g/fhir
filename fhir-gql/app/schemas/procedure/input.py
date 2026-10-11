"""
Input schemas for Procedure resource endpoints.

Three schemas cover the write/query surfaces:
  - ProcedureCreateSchema  — POST /procedures body
  - ProcedurePatchSchema   — PATCH /procedures/{id} body (scalar + reference fields only)
  - ListProceduresSchema   — GET /procedures query parameters (FHIR R4 search params)

Design notes:
  - R4 requires `status` (1..1) and `subject` (1..1); both are required here and
    mirror the fhir-server's validation, so errors surface at the boundary.
  - `status` is typed with the ProcedureStatus enum so OpenAPI lists the allowed
    codes (the hyphenated FHIR codes, e.g. "in-progress").
  - References are submitted as FHIR strings ("Patient/10001") — the fhir-server
    splits them into type + id columns.
  - performed[x] is a choice type: supply exactly one variant
    (datetime | period | string | age | range).
  - Reference: https://www.hl7.org/fhir/R4/procedure.html
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.enums import ProcedureStatus


# ── Child (0..*) input schemas ────────────────────────────────────────────────


class ProcedureIdentifierInput(BaseModel):
    """Business identifier for the Procedure (Identifier datatype)."""

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


class ProcedureBasedOnInput(BaseModel):
    """basedOn — the CarePlan or ServiceRequest that requested this procedure."""

    model_config = ConfigDict(extra="forbid")

    reference: str = Field(..., description="FHIR reference e.g. 'CarePlan/290001' or 'ServiceRequest/80001'.")
    reference_display: Optional[str] = None


class ProcedurePartOfInput(BaseModel):
    """partOf — a larger Procedure, Observation or MedicationAdministration this is part of."""

    model_config = ConfigDict(extra="forbid")

    reference: str = Field(
        ..., description="FHIR reference e.g. 'Procedure/100001', 'Observation/160001' or 'MedicationAdministration/1'."
    )
    reference_display: Optional[str] = None


class ProcedurePerformerInput(BaseModel):
    """performer — who performed the procedure and in what role."""

    model_config = ConfigDict(extra="forbid")

    function_system: Optional[str] = None
    function_code: Optional[str] = None
    function_display: Optional[str] = None
    function_text: Optional[str] = None
    actor: str = Field(
        ...,
        description="FHIR reference: Practitioner|PractitionerRole|Organization|Patient|RelatedPerson|Device e.g. 'Practitioner/30001'.",
    )
    actor_display: Optional[str] = None
    on_behalf_of: Optional[str] = Field(None, description="FHIR reference e.g. 'Organization/190001'.")
    on_behalf_of_display: Optional[str] = None


class ProcedureCodeableConceptInput(BaseModel):
    """
    CodeableConcept child entry (one coding + free text).

    Used for reasonCode, bodySite, complication, followUp and usedCode, which all
    share the same storage shape on the fhir-server.
    """

    model_config = ConfigDict(extra="forbid")

    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class ProcedureReasonReferenceInput(BaseModel):
    """reasonReference — Condition|Observation|Procedure|DiagnosticReport|DocumentReference."""

    model_config = ConfigDict(extra="forbid")

    reference: str = Field(..., description="FHIR reference e.g. 'Condition/120001'.")
    reference_display: Optional[str] = None


class ProcedureReportInput(BaseModel):
    """report — DiagnosticReport|DocumentReference|Composition produced by the procedure."""

    model_config = ConfigDict(extra="forbid")

    reference: str = Field(..., description="FHIR reference e.g. 'DiagnosticReport/110001'.")
    reference_display: Optional[str] = None


class ProcedureComplicationDetailInput(BaseModel):
    """complicationDetail — a Condition describing a complication in detail."""

    model_config = ConfigDict(extra="forbid")

    reference: str = Field(..., description="FHIR reference e.g. 'Condition/120001'.")
    reference_display: Optional[str] = None


class ProcedureNoteInput(BaseModel):
    """note — Annotation comment about the procedure."""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(..., description="Annotation text (markdown).")
    time: Optional[datetime] = None
    author_string: Optional[str] = None
    author_reference: Optional[str] = Field(
        None,
        description="FHIR reference: Practitioner|Patient|RelatedPerson|Organization e.g. 'Practitioner/30001'. "
        "Mutually exclusive with author_string.",
    )
    author_reference_display: Optional[str] = None


class ProcedureFocalDeviceInput(BaseModel):
    """focalDevice — a device that was implanted, removed or otherwise manipulated."""

    model_config = ConfigDict(extra="forbid")

    action_system: Optional[str] = None
    action_code: Optional[str] = None
    action_display: Optional[str] = None
    action_text: Optional[str] = None
    manipulated_reference: str = Field(..., description="FHIR reference e.g. 'Device/1'.")
    manipulated_reference_display: Optional[str] = None


class ProcedureUsedReferenceInput(BaseModel):
    """usedReference — Device|Medication|Substance used during the procedure."""

    model_config = ConfigDict(extra="forbid")

    reference: str = Field(..., description="FHIR reference e.g. 'Device/1' or 'Medication/250001'.")
    reference_display: Optional[str] = None


# ── Create ────────────────────────────────────────────────────────────────────


class ProcedureCreateSchema(BaseModel):
    """
    Request body for POST /procedures.

    `status` and `subject` are required (R4 cardinality 1..1). Tenant scoping
    (`user_id`, `org_id`) is supplied by the caller; `created_by` is stamped by
    FhirClient from the JWT and must not be sent.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "user_id": "user-123",
                "org_id": "org-456",
                "status": "completed",
                "code_system": "http://snomed.info/sct",
                "code_code": "80146002",
                "code_display": "Appendectomy",
                "subject": "Patient/10001",
                "encounter_id": 20001,
                "performed_datetime": "2024-03-15T10:30:00Z",
                "performer": [
                    {
                        "actor": "Practitioner/30001",
                        "actor_display": "Dr. Smith",
                        "function_system": "http://snomed.info/sct",
                        "function_code": "304292004",
                    }
                ],
                "note": [{"text": "Procedure completed without complications."}],
            }
        },
    )

    # Tenant scoping — supplied by the caller; the middleware does not inject these from the JWT.
    user_id: Optional[str] = Field(None, description="JWT sub of the record owner.")
    org_id: Optional[str] = Field(None, description="Active organization ID from the JWT.")

    # status (1..1 code)
    status: ProcedureStatus = Field(
        ..., description="preparation|in-progress|not-done|on-hold|stopped|completed|entered-in-error|unknown"
    )

    # statusReason (0..1 CodeableConcept)
    status_reason_system: Optional[str] = None
    status_reason_code: Optional[str] = None
    status_reason_display: Optional[str] = None
    status_reason_text: Optional[str] = None

    # category (0..1 CodeableConcept)
    category_system: Optional[str] = None
    category_code: Optional[str] = None
    category_display: Optional[str] = None
    category_text: Optional[str] = None

    # code (0..1 CodeableConcept) — what procedure was performed
    code_system: Optional[str] = None
    code_code: Optional[str] = None
    code_display: Optional[str] = None
    code_text: Optional[str] = None

    # subject (1..1 Reference — Patient | Group)
    subject: str = Field(..., description="FHIR reference e.g. 'Patient/10001' or 'Group/1'.")
    subject_display: Optional[str] = None

    # encounter (0..1 Reference(Encounter))
    encounter_id: Optional[int] = Field(None, description="Public encounter_id of the linked Encounter.")
    encounter_display: Optional[str] = None

    # performed[x] (0..1 choice) — supply exactly one variant
    performed_datetime: Optional[datetime] = None
    performed_period_start: Optional[datetime] = None
    performed_period_end: Optional[datetime] = None
    performed_string: Optional[str] = None
    performed_age_value: Optional[float] = None
    performed_age_comparator: Optional[str] = Field(None, description="Age comparator: '<' | '<=' | '>=' | '>'.")
    performed_age_unit: Optional[str] = None
    performed_age_system: Optional[str] = None
    performed_age_code: Optional[str] = None
    performed_range_low_value: Optional[float] = None
    performed_range_low_unit: Optional[str] = None
    performed_range_low_system: Optional[str] = None
    performed_range_low_code: Optional[str] = None
    performed_range_high_value: Optional[float] = None
    performed_range_high_unit: Optional[str] = None
    performed_range_high_system: Optional[str] = None
    performed_range_high_code: Optional[str] = None

    # recorder / asserter (0..1 Reference — Patient|RelatedPerson|Practitioner|PractitionerRole)
    recorder: Optional[str] = Field(None, description="FHIR reference e.g. 'Practitioner/30001'.")
    recorder_display: Optional[str] = None
    asserter: Optional[str] = Field(None, description="FHIR reference e.g. 'Practitioner/30001'.")
    asserter_display: Optional[str] = None

    # location (0..1 Reference(Location))
    location: Optional[str] = Field(None, description="FHIR reference e.g. 'Location/230001'.")
    location_display: Optional[str] = None

    # outcome (0..1 CodeableConcept)
    outcome_system: Optional[str] = None
    outcome_code: Optional[str] = None
    outcome_display: Optional[str] = None
    outcome_text: Optional[str] = None

    # instantiatesCanonical / instantiatesUri (0..*)
    instantiates_canonical: Optional[List[str]] = Field(None, description="Canonical URIs of FHIR protocols instantiated.")
    instantiates_uri: Optional[List[str]] = Field(None, description="External URIs of protocols instantiated.")

    # Child arrays (0..*) — all submitted in the single create request.
    identifier: Optional[List[ProcedureIdentifierInput]] = None
    based_on: Optional[List[ProcedureBasedOnInput]] = None
    part_of: Optional[List[ProcedurePartOfInput]] = None
    performer: Optional[List[ProcedurePerformerInput]] = None
    reason_code: Optional[List[ProcedureCodeableConceptInput]] = None
    reason_reference: Optional[List[ProcedureReasonReferenceInput]] = None
    body_site: Optional[List[ProcedureCodeableConceptInput]] = None
    report: Optional[List[ProcedureReportInput]] = None
    complication: Optional[List[ProcedureCodeableConceptInput]] = None
    complication_detail: Optional[List[ProcedureComplicationDetailInput]] = None
    follow_up: Optional[List[ProcedureCodeableConceptInput]] = None
    note: Optional[List[ProcedureNoteInput]] = None
    focal_device: Optional[List[ProcedureFocalDeviceInput]] = None
    used_reference: Optional[List[ProcedureUsedReferenceInput]] = None
    used_code: Optional[List[ProcedureCodeableConceptInput]] = None


# ── Patch ─────────────────────────────────────────────────────────────────────


class ProcedurePatchSchema(BaseModel):
    """
    Request body for PATCH /procedures/{id}.

    All fields optional; at least one must be provided (enforced in the service).
    Child lists are patchable with REPLACE semantics (send `[]` to clear one).
    `status` and `subject` can be changed but never nulled. The optional
    references (`encounter_id`, `recorder`, `asserter`, `location`) can be
    changed but, because None is dropped from the payload, cannot be cleared
    through this gateway.
    """

    model_config = ConfigDict(extra="forbid")

    status: Optional[ProcedureStatus] = Field(
        None, description="preparation|in-progress|not-done|on-hold|stopped|completed|entered-in-error|unknown"
    )

    status_reason_system: Optional[str] = None
    status_reason_code: Optional[str] = None
    status_reason_display: Optional[str] = None
    status_reason_text: Optional[str] = None

    category_system: Optional[str] = None
    category_code: Optional[str] = None
    category_display: Optional[str] = None
    category_text: Optional[str] = None

    code_system: Optional[str] = None
    code_code: Optional[str] = None
    code_display: Optional[str] = None
    code_text: Optional[str] = None

    subject: Optional[str] = Field(None, description="FHIR reference e.g. 'Patient/10001' or 'Group/1'.")
    subject_display: Optional[str] = None
    encounter_id: Optional[int] = Field(None, description="Public encounter_id of the linked Encounter.")
    encounter_display: Optional[str] = None

    performed_datetime: Optional[datetime] = None
    performed_period_start: Optional[datetime] = None
    performed_period_end: Optional[datetime] = None
    performed_string: Optional[str] = None
    performed_age_value: Optional[float] = None
    performed_age_comparator: Optional[str] = Field(None, description="Age comparator: '<' | '<=' | '>=' | '>'.")
    performed_age_unit: Optional[str] = None
    performed_age_system: Optional[str] = None
    performed_age_code: Optional[str] = None
    performed_range_low_value: Optional[float] = None
    performed_range_low_unit: Optional[str] = None
    performed_range_low_system: Optional[str] = None
    performed_range_low_code: Optional[str] = None
    performed_range_high_value: Optional[float] = None
    performed_range_high_unit: Optional[str] = None
    performed_range_high_system: Optional[str] = None
    performed_range_high_code: Optional[str] = None

    recorder: Optional[str] = Field(None, description="FHIR reference e.g. 'Practitioner/30001'.")
    recorder_display: Optional[str] = None
    asserter: Optional[str] = Field(None, description="FHIR reference e.g. 'Practitioner/30001'.")
    asserter_display: Optional[str] = None
    location: Optional[str] = Field(None, description="FHIR reference e.g. 'Location/230001'.")
    location_display: Optional[str] = None

    outcome_system: Optional[str] = None
    outcome_code: Optional[str] = None
    outcome_display: Optional[str] = None
    outcome_text: Optional[str] = None

    instantiates_canonical: Optional[List[str]] = None
    instantiates_uri: Optional[List[str]] = None

    # Child lists — REPLACE semantics: a list that is sent replaces the stored one in full;
    # an omitted list is left untouched. Send [] to clear a list (null is dropped by the gateway).
    identifier: Optional[List[ProcedureIdentifierInput]] = None
    based_on: Optional[List[ProcedureBasedOnInput]] = None
    part_of: Optional[List[ProcedurePartOfInput]] = None
    performer: Optional[List[ProcedurePerformerInput]] = None
    reason_code: Optional[List[ProcedureCodeableConceptInput]] = None
    reason_reference: Optional[List[ProcedureReasonReferenceInput]] = None
    body_site: Optional[List[ProcedureCodeableConceptInput]] = None
    report: Optional[List[ProcedureReportInput]] = None
    complication: Optional[List[ProcedureCodeableConceptInput]] = None
    complication_detail: Optional[List[ProcedureComplicationDetailInput]] = None
    follow_up: Optional[List[ProcedureCodeableConceptInput]] = None
    note: Optional[List[ProcedureNoteInput]] = None
    focal_device: Optional[List[ProcedureFocalDeviceInput]] = None
    used_reference: Optional[List[ProcedureUsedReferenceInput]] = None
    used_code: Optional[List[ProcedureCodeableConceptInput]] = None


# ── List / search ─────────────────────────────────────────────────────────────


class ListProceduresSchema(BaseModel):
    """
    Search parameters for GET /procedures — the FHIR R4 Procedure search params.

    The router builds this from explicitly declared Query parameters (several FHIR
    names are hyphenated or underscore-prefixed and cannot be plain Python
    identifiers); the service then forwards it to the fhir-server.

    Token params (`status`, `code`, `category`, `identifier`, `reason_code`):
    `code` | `system|code` | `|code` | `system|`; comma = OR.
    Reference params (`patient`, `subject`, `encounter`, `performer`, `location`,
    `part_of`, `based_on`, `reason_reference`): `Type/id` or bare numeric id; comma = OR.
    Date params (`date`, `last_updated`): optional prefix eq|ne|gt|lt|ge|le|sa|eb|ap;
    repeat for AND (e.g. a range).
    """

    model_config = ConfigDict(extra="forbid")

    id: Optional[str] = Field(None, description="_id — public procedure_id(s), comma-separated.")
    identifier: Optional[str] = Field(None, description="Token `[system|]value` of Procedure.identifier.")
    status: Optional[str] = Field(
        None, description="Token: preparation|in-progress|not-done|on-hold|stopped|completed|entered-in-error|unknown."
    )
    category: Optional[str] = Field(None, description="Token `[system|]code` of Procedure.category.")
    code: Optional[str] = Field(None, description="Token `[system|]code` of Procedure.code.")
    patient: Optional[str] = Field(None, description="Subject patient reference: 'Patient/10001' or '10001'.")
    subject: Optional[str] = Field(None, description="Subject reference (Patient or Group).")
    encounter: Optional[str] = Field(None, description="Encounter reference: 'Encounter/20001' or '20001'.")
    date: Optional[List[str]] = Field(None, description="performed[x] date with optional prefix e.g. 'ge2024-01-01'.")
    performer: Optional[str] = Field(None, description="Performer.actor reference e.g. 'Practitioner/30001'.")
    location: Optional[str] = Field(None, description="Location reference e.g. 'Location/230001'.")
    part_of: Optional[str] = Field(None, description="part-of reference: Procedure|Observation|MedicationAdministration.")
    based_on: Optional[str] = Field(None, description="based-on reference: CarePlan|ServiceRequest.")
    reason_code: Optional[str] = Field(None, description="reason-code token `[system|]code`.")
    reason_reference: Optional[str] = Field(None, description="reason-reference: Condition|Observation|Procedure|DiagnosticReport|DocumentReference.")
    instantiates_canonical: Optional[str] = Field(None, description="instantiates-canonical URI.")
    instantiates_uri: Optional[str] = Field(None, description="instantiates-uri URI.")
    last_updated: Optional[List[str]] = Field(None, description="_lastUpdated instant with optional prefix.")
    # Tenant-scoping filters — optional so admin callers can query across users/orgs.
    user_id: Optional[str] = Field(None, description="Optional: restrict to records owned by this user (JWT subject).")
    org_id: str = Field(..., min_length=1, description="Tenant organization ID — mandatory scope of every search.")
    limit: int = Field(50, ge=1, le=200, description="Max records per page.")
    offset: int = Field(0, ge=0, description="Records to skip.")

    @field_validator("status")
    @classmethod
    def _validate_status_tokens(cls, v: Optional[str]) -> Optional[str]:
        """
        Reject unknown status codes early (comma-separated OR list allowed).

        Fails fast at the gateway with a 422 instead of forwarding an invalid
        token to the fhir-server.
        """
        if v is None:
            return v
        allowed = {s.value for s in ProcedureStatus}
        bad = [t for t in v.split(",") if t.strip() and t.strip() not in allowed]
        if bad:
            raise ValueError(f"Invalid status {bad}. Allowed: {sorted(allowed)}")
        return v
