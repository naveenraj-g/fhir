"""
Input schemas for the ActivityDefinition resource (FHIR R4) — fhir-gql gateway copy.

Mirrors the fhir-server contract; the fhir-server remains the source of truth for persistence.

https://www.hl7.org/fhir/R4/activitydefinition.html

Conventions (shared with PlanDefinition, whose nested datatype inputs are re-used):
  * CodeableConcept 0..1 fields are flat `<field>_system/_code/_display/_text`; 0..* CodeableConcepts are
    lists of `{coding_system, coding_code, coding_display, text}`.
  * References are `Type/id` strings (format + allowed type validated, existence never).
  * Complex datatypes (Quantity, Range, Ratio, Period, Expression, Timing) are nested objects.
  * Choice types (`subject[x]`, `timing[x]`, `product[x]`, `asNeeded[x]`, `dose[x]`, `rate[x]`) allow at most one variant.
"""

from __future__ import annotations

from datetime import date as Date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.enums import (
    ActionParticipantType,
    ActionPriority,
    ActivityDefinitionIntent,
    ActivityDefinitionKind,
    PlanDefinitionStatus,
)
from app.schemas.plan_definition.input import (
    PdPeriodInput,
    PdQuantityInput,
    PdRangeInput,
    PdSimpleQuantityInput,
    PdTimingInput,
    PlanDefinitionCodeableConceptInput,
    PlanDefinitionContactInput,
    PlanDefinitionDynamicValueInput,
    PlanDefinitionIdentifierInput,
    PlanDefinitionRelatedArtifactInput,
    PlanDefinitionUseContextInput,
    _one,
    _utc,
)


# ── Nested datatypes ───────────────────────────────────────────────────────────


class AdRatioInput(BaseModel):
    """Ratio — numerator and denominator Quantities."""

    model_config = ConfigDict(extra="forbid")

    numerator: Optional[PdQuantityInput] = None
    denominator: Optional[PdQuantityInput] = None


class ActivityDefinitionReferenceInput(BaseModel):
    """Reference list entry (specimenRequirement / observationRequirement / observationResultRequirement)."""

    model_config = ConfigDict(extra="forbid")

    reference: str = Field(..., description="FHIR reference, e.g. 'ObservationDefinition/5'.")
    reference_display: Optional[str] = None


class ActivityDefinitionParticipantInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: ActionParticipantType = Field(..., description="patient|practitioner|related-person|device")
    role_system: Optional[str] = None
    role_code: Optional[str] = None
    role_display: Optional[str] = None
    role_text: Optional[str] = None


class ActivityDefinitionDoseAndRateInput(BaseModel):
    """dosage.doseAndRate[] — type + dose[x] (Range | SimpleQuantity) + rate[x] (Ratio | Range | SimpleQuantity)."""

    model_config = ConfigDict(extra="forbid")

    type_system: Optional[str] = None
    type_code: Optional[str] = Field(None, description="calculated|ordered (DoseAndRateType).")
    type_display: Optional[str] = None
    type_text: Optional[str] = None
    dose_range: Optional[PdRangeInput] = None
    dose_quantity: Optional[PdSimpleQuantityInput] = None
    rate_ratio: Optional[AdRatioInput] = None
    rate_range: Optional[PdRangeInput] = None
    rate_quantity: Optional[PdSimpleQuantityInput] = None

    @model_validator(mode="after")
    def _choices(self):
        _one({"Range": self.dose_range is not None, "Quantity": self.dose_quantity is not None}, "doseAndRate.dose[x]")
        _one({
            "Ratio": self.rate_ratio is not None,
            "Range": self.rate_range is not None,
            "Quantity": self.rate_quantity is not None,
        }, "doseAndRate.rate[x]")
        return self


class ActivityDefinitionDosageInput(BaseModel):
    """dosage[] — Dosage datatype."""

    model_config = ConfigDict(extra="forbid")

    sequence: Optional[int] = None
    text: Optional[str] = Field(None, description="Free-text dosage instructions.")
    additional_instruction: Optional[List[PlanDefinitionCodeableConceptInput]] = None
    patient_instruction: Optional[str] = None
    timing: Optional[PdTimingInput] = None
    as_needed_boolean: Optional[bool] = None
    as_needed_system: Optional[str] = None
    as_needed_code: Optional[str] = None
    as_needed_display: Optional[str] = None
    as_needed_text: Optional[str] = None
    site_system: Optional[str] = None
    site_code: Optional[str] = None
    site_display: Optional[str] = None
    site_text: Optional[str] = None
    route_system: Optional[str] = None
    route_code: Optional[str] = None
    route_display: Optional[str] = None
    route_text: Optional[str] = None
    method_system: Optional[str] = None
    method_code: Optional[str] = None
    method_display: Optional[str] = None
    method_text: Optional[str] = None
    dose_and_rate: Optional[List[ActivityDefinitionDoseAndRateInput]] = None
    max_dose_per_period: Optional[AdRatioInput] = None
    max_dose_per_administration: Optional[PdSimpleQuantityInput] = None
    max_dose_per_lifetime: Optional[PdSimpleQuantityInput] = None

    @model_validator(mode="after")
    def _as_needed(self):
        _one({
            "boolean": self.as_needed_boolean is not None,
            "CodeableConcept": any([self.as_needed_system, self.as_needed_code, self.as_needed_display, self.as_needed_text]),
        }, "dosage.asNeeded[x]")
        return self


# ── Create / Patch ─────────────────────────────────────────────────────────────

_CHILD_LISTS = (
    "identifier", "contact", "author", "editor", "reviewer", "endorser", "use_context", "jurisdiction", "topic",
    "related_artifact", "library", "participant", "dosage", "body_site", "specimen_requirement",
    "observation_requirement", "observation_result_requirement", "dynamic_value",
)


def _validate_common(m) -> None:
    if m.effective_period_start and m.effective_period_end and _utc(m.effective_period_end) < _utc(m.effective_period_start):
        raise ValueError("effective_period_end must not be before effective_period_start.")
    _one({
        "CodeableConcept": any([m.subject_cc_system, m.subject_cc_code, m.subject_cc_display, m.subject_cc_text]),
        "Reference": m.subject_reference is not None,
    }, "subject[x]")
    _one({
        "Timing": m.timing_timing is not None,
        "dateTime": m.timing_datetime is not None,
        "Age": m.timing_age is not None,
        "Period": m.timing_period is not None,
        "Range": m.timing_range is not None,
        "Duration": m.timing_duration is not None,
    }, "timing[x]")
    _one({
        "Reference": m.product_reference is not None,
        "CodeableConcept": any([m.product_cc_system, m.product_cc_code, m.product_cc_display, m.product_cc_text]),
    }, "product[x]")


class ActivityDefinitionCreateSchema(BaseModel):
    """Request body for POST /activity-definitions. Only `status` is required (R4 1..1)."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "user_id": "user-123",
                "org_id": "org-456",
                "url": "http://example.org/fhir/ActivityDefinition/administer-zika-virus-exposure-assessment",
                "version": "1.0.0",
                "name": "AdministerZikaVirusExposureAssessment",
                "title": "Administer Zika Virus Exposure Assessment",
                "status": "active",
                "kind": "ServiceRequest",
                "intent": "proposal",
                "priority": "routine",
                "code_system": "http://example.org/questionnaires",
                "code_code": "zika-virus-exposure-assessment",
                "timing_timing": {"repeat": {"frequency": 1, "period": 1, "period_unit": "d"}},
                "participant": [{"type": "practitioner"}],
                "dosage": [{"text": "1 tablet twice daily", "route_code": "26643006", "route_system": "http://snomed.info/sct"}],
            }
        },
    )

    user_id: Optional[str] = Field(None, description="JWT sub of the record owner.")
    org_id: Optional[str] = Field(None, description="Active organization ID from JWT.")
    created_by: Optional[str] = None

    url: Optional[str] = None
    version: Optional[str] = None
    name: Optional[str] = None
    title: Optional[str] = None
    subtitle: Optional[str] = None
    status: PlanDefinitionStatus = Field(..., description="draft|active|retired|unknown")
    experimental: Optional[bool] = None
    date: Optional[datetime] = Field(None, description="Date last changed.")
    publisher: Optional[str] = None
    description: Optional[str] = Field(None, description="markdown")
    purpose: Optional[str] = Field(None, description="markdown")
    usage: Optional[str] = None
    copyright: Optional[str] = Field(None, description="markdown")
    approval_date: Optional[Date] = None
    last_review_date: Optional[Date] = None
    effective_period_start: Optional[datetime] = None
    effective_period_end: Optional[datetime] = None

    subject_cc_system: Optional[str] = None
    subject_cc_code: Optional[str] = None
    subject_cc_display: Optional[str] = None
    subject_cc_text: Optional[str] = None
    subject_reference: Optional[str] = Field(None, description="Group reference e.g. 'Group/1'.")
    subject_reference_display: Optional[str] = None

    kind: Optional[ActivityDefinitionKind] = Field(None, description="Kind of resource this definition creates (RequestResourceType), e.g. ServiceRequest.")
    profile: Optional[str] = Field(None, description="canonical(StructureDefinition) the resulting resource conforms to.")
    code_system: Optional[str] = None
    code_code: Optional[str] = None
    code_display: Optional[str] = None
    code_text: Optional[str] = None
    intent: Optional[ActivityDefinitionIntent] = Field(
        None, description="proposal|plan|directive|order|original-order|reflex-order|filler-order|instance-order|option"
    )
    priority: Optional[ActionPriority] = Field(None, description="routine|urgent|asap|stat")
    do_not_perform: Optional[bool] = Field(None, description="True if the activity should NOT be performed.")

    timing_datetime: Optional[datetime] = None
    timing_age: Optional[PdQuantityInput] = None
    timing_period: Optional[PdPeriodInput] = None
    timing_range: Optional[PdRangeInput] = None
    timing_duration: Optional[PdQuantityInput] = None
    timing_timing: Optional[PdTimingInput] = None

    location: Optional[str] = Field(None, description="Location reference e.g. 'Location/230001'.")
    location_display: Optional[str] = None

    product_reference: Optional[str] = Field(None, description="Medication|Substance reference e.g. 'Medication/250001'.")
    product_reference_display: Optional[str] = None
    product_cc_system: Optional[str] = None
    product_cc_code: Optional[str] = None
    product_cc_display: Optional[str] = None
    product_cc_text: Optional[str] = None

    quantity: Optional[PdSimpleQuantityInput] = Field(None, description="How much is administered/consumed.")
    transform: Optional[str] = Field(None, description="canonical(StructureMap) used to transform the definition into the resource.")

    identifier: Optional[List[PlanDefinitionIdentifierInput]] = None
    contact: Optional[List[PlanDefinitionContactInput]] = None
    author: Optional[List[PlanDefinitionContactInput]] = None
    editor: Optional[List[PlanDefinitionContactInput]] = None
    reviewer: Optional[List[PlanDefinitionContactInput]] = None
    endorser: Optional[List[PlanDefinitionContactInput]] = None
    use_context: Optional[List[PlanDefinitionUseContextInput]] = None
    jurisdiction: Optional[List[PlanDefinitionCodeableConceptInput]] = None
    topic: Optional[List[PlanDefinitionCodeableConceptInput]] = None
    related_artifact: Optional[List[PlanDefinitionRelatedArtifactInput]] = None
    library: Optional[List[str]] = Field(None, description="canonical(Library) URLs.")
    participant: Optional[List[ActivityDefinitionParticipantInput]] = None
    dosage: Optional[List[ActivityDefinitionDosageInput]] = None
    body_site: Optional[List[PlanDefinitionCodeableConceptInput]] = None
    specimen_requirement: Optional[List[ActivityDefinitionReferenceInput]] = Field(None, description="SpecimenDefinition references.")
    observation_requirement: Optional[List[ActivityDefinitionReferenceInput]] = Field(None, description="ObservationDefinition references.")
    observation_result_requirement: Optional[List[ActivityDefinitionReferenceInput]] = Field(None, description="ObservationDefinition references.")
    dynamic_value: Optional[List[PlanDefinitionDynamicValueInput]] = None

    @model_validator(mode="after")
    def _validate(self):
        _validate_common(self)
        return self


class ActivityDefinitionPatchSchema(BaseModel):
    """
    Request body for PATCH /activity-definitions/{id}. All optional. `status` cannot be null.

    Child lists (identifier, contact, author, editor, reviewer, endorser, use_context, jurisdiction, topic,
    related_artifact, library, participant, dosage, body_site, specimen_requirement, observation_requirement,
    observation_result_requirement, dynamic_value) use REPLACE semantics: a list that is sent replaces the stored
    one in full, `[]` (or null) clears it, an omitted list is left untouched. References are `Type/id` strings;
    null clears one.
    """

    model_config = ConfigDict(extra="forbid")

    url: Optional[str] = None
    version: Optional[str] = None
    name: Optional[str] = None
    title: Optional[str] = None
    subtitle: Optional[str] = None
    status: Optional[PlanDefinitionStatus] = Field(None, description="Cannot be null.")
    experimental: Optional[bool] = None
    date: Optional[datetime] = None
    publisher: Optional[str] = None
    description: Optional[str] = None
    purpose: Optional[str] = None
    usage: Optional[str] = None
    copyright: Optional[str] = None
    approval_date: Optional[Date] = None
    last_review_date: Optional[Date] = None
    effective_period_start: Optional[datetime] = None
    effective_period_end: Optional[datetime] = None
    subject_cc_system: Optional[str] = None
    subject_cc_code: Optional[str] = None
    subject_cc_display: Optional[str] = None
    subject_cc_text: Optional[str] = None
    subject_reference: Optional[str] = None
    subject_reference_display: Optional[str] = None
    kind: Optional[ActivityDefinitionKind] = None
    profile: Optional[str] = None
    code_system: Optional[str] = None
    code_code: Optional[str] = None
    code_display: Optional[str] = None
    code_text: Optional[str] = None
    intent: Optional[ActivityDefinitionIntent] = None
    priority: Optional[ActionPriority] = None
    do_not_perform: Optional[bool] = None
    timing_datetime: Optional[datetime] = None
    timing_age: Optional[PdQuantityInput] = None
    timing_period: Optional[PdPeriodInput] = None
    timing_range: Optional[PdRangeInput] = None
    timing_duration: Optional[PdQuantityInput] = None
    timing_timing: Optional[PdTimingInput] = None
    location: Optional[str] = None
    location_display: Optional[str] = None
    product_reference: Optional[str] = None
    product_reference_display: Optional[str] = None
    product_cc_system: Optional[str] = None
    product_cc_code: Optional[str] = None
    product_cc_display: Optional[str] = None
    product_cc_text: Optional[str] = None
    quantity: Optional[PdSimpleQuantityInput] = None
    transform: Optional[str] = None
    updated_by: Optional[str] = None

    identifier: Optional[List[PlanDefinitionIdentifierInput]] = None
    contact: Optional[List[PlanDefinitionContactInput]] = None
    author: Optional[List[PlanDefinitionContactInput]] = None
    editor: Optional[List[PlanDefinitionContactInput]] = None
    reviewer: Optional[List[PlanDefinitionContactInput]] = None
    endorser: Optional[List[PlanDefinitionContactInput]] = None
    use_context: Optional[List[PlanDefinitionUseContextInput]] = None
    jurisdiction: Optional[List[PlanDefinitionCodeableConceptInput]] = None
    topic: Optional[List[PlanDefinitionCodeableConceptInput]] = None
    related_artifact: Optional[List[PlanDefinitionRelatedArtifactInput]] = None
    library: Optional[List[str]] = None
    participant: Optional[List[ActivityDefinitionParticipantInput]] = None
    dosage: Optional[List[ActivityDefinitionDosageInput]] = None
    body_site: Optional[List[PlanDefinitionCodeableConceptInput]] = None
    specimen_requirement: Optional[List[ActivityDefinitionReferenceInput]] = None
    observation_requirement: Optional[List[ActivityDefinitionReferenceInput]] = None
    observation_result_requirement: Optional[List[ActivityDefinitionReferenceInput]] = None
    dynamic_value: Optional[List[PlanDefinitionDynamicValueInput]] = None

    @field_validator("status")
    @classmethod
    def _status_not_null(cls, v):
        if v is None:
            raise ValueError("must not be null")
        return v

    @model_validator(mode="after")
    def _validate(self):
        _validate_common(self)
        return self


# ── Search ─────────────────────────────────────────────────────────────────────


class ListActivityDefinitionsSchema(BaseModel):
    """
    Search parameters for GET /activity-definitions — the FHIR R4 ActivityDefinition search params plus `_id`
    and `_lastUpdated`.

    The router builds this from explicitly declared Query parameters (`_id`, `_lastUpdated` and the
    hyphenated / `:modifier` names are not valid Python identifiers); the service then forwards it to the
    fhir-server under the FHIR parameter names.

    Token params: `code` | `system|code` | `|code` | `system|`; comma = OR.
    String params (name/title/publisher/description): prefix match by default, `*_contains` / `*_exact` variants.
    Date params (`date`, `effective`, `last_updated`): optional prefix eq|ne|gt|lt|ge|le|sa|eb|ap; repeat for AND.
    """

    model_config = ConfigDict(extra="forbid")

    id: Optional[str] = Field(None, description="_id — public activity_definition_id(s), comma-separated.")
    identifier: Optional[str] = Field(None, description="Token `[system|]value` of ActivityDefinition.identifier.")
    url: Optional[str] = Field(None, description="Canonical URL(s), comma = OR.")
    version: Optional[str] = Field(None, description="Business version(s), comma = OR.")
    name: Optional[str] = Field(None, description="Name — prefix match.")
    name_contains: Optional[str] = Field(None, description="name:contains — substring.")
    name_exact: Optional[str] = Field(None, description="name:exact — case-sensitive full match.")
    title: Optional[str] = Field(None, description="Title — prefix match.")
    title_contains: Optional[str] = Field(None, description="title:contains — substring.")
    title_exact: Optional[str] = Field(None, description="title:exact — case-sensitive full match.")
    publisher: Optional[str] = Field(None, description="Publisher — prefix match.")
    publisher_contains: Optional[str] = Field(None, description="publisher:contains — substring.")
    publisher_exact: Optional[str] = Field(None, description="publisher:exact — case-sensitive full match.")
    description: Optional[str] = Field(None, description="Description — prefix match.")
    description_contains: Optional[str] = Field(None, description="description:contains — substring.")
    description_exact: Optional[str] = Field(None, description="description:exact — case-sensitive full match.")
    status: Optional[str] = Field(None, description="Token: draft|active|retired|unknown (comma = OR).")
    topic: Optional[str] = Field(None, description="Token `[system|]code` of ActivityDefinition.topic.")
    jurisdiction: Optional[str] = Field(None, description="Token `[system|]code` of ActivityDefinition.jurisdiction.")
    context: Optional[str] = Field(None, description="Token of useContext.valueCodeableConcept.")
    context_type: Optional[str] = Field(None, description="context-type — token of useContext.code.")
    depends_on: Optional[str] = Field(None, description="depends-on — resource the definition depends on (relatedArtifact / library).")
    derived_from: Optional[str] = Field(None, description="derived-from — resource the definition is derived from.")
    predecessor: Optional[str] = Field(None, description="Predecessor resource.")
    successor: Optional[str] = Field(None, description="Successor resource.")
    composed_of: Optional[str] = Field(None, description="composed-of — resource the definition is composed of.")
    date: Optional[List[str]] = Field(None, description="Publication date with optional prefix e.g. 'ge2024-01-01'.")
    effective: Optional[List[str]] = Field(None, description="Effective period with optional prefix.")
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
        allowed = {s.value for s in PlanDefinitionStatus}
        bad = [t for t in v.split(",") if t.strip() and t.strip() not in allowed]
        if bad:
            raise ValueError(f"Invalid status {bad}. Allowed: {sorted(allowed)}")
        return v
