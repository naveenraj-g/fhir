"""
Input schemas for the CarePlan resource (FHIR R4) — fhir-gql gateway copy.

Mirrors the fhir-server contract; the fhir-server remains the source of truth for persistence.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.enums import (
    CarePlanActivityKind,
    CarePlanDetailActivityStatus,
    CarePlanIntent,
    CarePlanStatus,
)


class CarePlanIdentifierInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    use: Optional[str] = None
    type_system: Optional[str] = None
    type_code: Optional[str] = None
    type_display: Optional[str] = None
    type_text: Optional[str] = None
    system: Optional[str] = None
    value: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    assigner: Optional[str] = None


class CarePlanBasedOnInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: str = Field(..., description="Reference to another CarePlan, e.g. 'CarePlan/290001'.")
    reference_display: Optional[str] = None


class CarePlanReplacesInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: str = Field(..., description="Reference to replaced CarePlan, e.g. 'CarePlan/290001'.")
    reference_display: Optional[str] = None


class CarePlanPartOfInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: str = Field(..., description="Reference to parent CarePlan, e.g. 'CarePlan/290001'.")
    reference_display: Optional[str] = None


class CarePlanCategoryInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class CarePlanContributorInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: str = Field(
        ...,
        description=(
            "Allowed: Patient/<id>, Practitioner/<id>, PractitionerRole/<id>, "
            "Device/<id>, RelatedPerson/<id>, Organization/<id>, CareTeam/<id>."
        ),
    )
    reference_display: Optional[str] = None


class CarePlanCareTeamInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: str = Field(..., description="Reference to CareTeam, e.g. 'CareTeam/1'.")
    reference_display: Optional[str] = None


class CarePlanAddressesInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: str = Field(..., description="Reference to Condition, e.g. 'Condition/120001'.")
    reference_display: Optional[str] = None


class CarePlanSupportingInfoInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: str = Field(..., description="Open reference to any supporting info resource.")
    reference_display: Optional[str] = None


class CarePlanGoalInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: str = Field(..., description="Reference to Goal resource.")
    reference_display: Optional[str] = None


class CarePlanNoteInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(..., description="Annotation text content.")
    time: Optional[datetime] = None
    author_string: Optional[str] = None
    author_reference: Optional[str] = Field(None, description="Open reference to note author.")
    author_reference_display: Optional[str] = None


class CarePlanActivityOutcomeCCInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class CarePlanActivityOutcomeRefInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: str = Field(..., description="Open reference to outcome resource.")
    reference_display: Optional[str] = None


class CarePlanActivityProgressInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(..., description="Progress note text.")
    time: Optional[datetime] = None
    author_string: Optional[str] = None
    author_reference: Optional[str] = Field(None, description="Open reference to note author.")
    author_reference_display: Optional[str] = None


class CarePlanActivityDetailReasonCodeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class CarePlanActivityDetailReasonRefInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: str = Field(
        ...,
        description=(
            "Allowed: Condition/<id>, Observation/<id>, DiagnosticReport/<id>, DocumentReference/<id>."
        ),
    )
    reference_display: Optional[str] = None


class CarePlanActivityDetailGoalInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: str = Field(..., description="Reference to Goal resource.")
    reference_display: Optional[str] = None


class CarePlanActivityDetailPerformerInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: str = Field(
        ...,
        description=(
            "Allowed: Practitioner/<id>, PractitionerRole/<id>, Organization/<id>, "
            "RelatedPerson/<id>, Patient/<id>, CareTeam/<id>, HealthcareService/<id>, Device/<id>."
        ),
    )
    reference_display: Optional[str] = None


class CarePlanActivityInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # activity.reference (0..1 closed)
    reference: Optional[str] = Field(
        None,
        description=(
            "Allowed: Appointment/<id>, CommunicationRequest/<id>, DeviceRequest/<id>, "
            "MedicationRequest/<id>, NutritionOrder/<id>, Task/<id>, ServiceRequest/<id>, "
            "VisionPrescription/<id>, RequestGroup/<id>."
        ),
    )
    reference_display: Optional[str] = None

    # detail scalar fields
    detail_kind: Optional[CarePlanActivityKind] = Field(
        None, description="Appointment|CommunicationRequest|DeviceRequest|MedicationRequest|NutritionOrder|Task|ServiceRequest|VisionPrescription"
    )
    detail_instantiates_canonical: Optional[str] = Field(None, description="Comma-separated canonical URIs.")
    detail_instantiates_uri: Optional[str] = Field(None, description="Comma-separated URIs.")
    detail_code_system: Optional[str] = None
    detail_code_code: Optional[str] = None
    detail_code_display: Optional[str] = None
    detail_code_text: Optional[str] = None
    detail_status: Optional[CarePlanDetailActivityStatus] = Field(
        None,
        description=(
            "not-started | scheduled | in-progress | on-hold | completed | cancelled | stopped | unknown | "
            "entered-in-error. Required (1..1) whenever any activity.detail field is supplied."
        ),
    )
    detail_status_reason_system: Optional[str] = None
    detail_status_reason_code: Optional[str] = None
    detail_status_reason_display: Optional[str] = None
    detail_status_reason_text: Optional[str] = None
    detail_do_not_perform: Optional[bool] = None

    # scheduled[x] — Timing variant
    detail_scheduled_timing_event: Optional[str] = Field(None, description="Comma-separated datetime strings.")
    detail_scheduled_timing_code_system: Optional[str] = None
    detail_scheduled_timing_code_code: Optional[str] = None
    detail_scheduled_timing_code_display: Optional[str] = None
    detail_scheduled_timing_code_text: Optional[str] = None
    detail_scheduled_timing_repeat_count: Optional[int] = None
    detail_scheduled_timing_repeat_count_max: Optional[int] = None
    detail_scheduled_timing_repeat_duration: Optional[float] = None
    detail_scheduled_timing_repeat_duration_max: Optional[float] = None
    detail_scheduled_timing_repeat_duration_unit: Optional[str] = None
    detail_scheduled_timing_repeat_frequency: Optional[int] = None
    detail_scheduled_timing_repeat_frequency_max: Optional[int] = None
    detail_scheduled_timing_repeat_period: Optional[float] = None
    detail_scheduled_timing_repeat_period_max: Optional[float] = None
    detail_scheduled_timing_repeat_period_unit: Optional[str] = None
    detail_scheduled_timing_repeat_day_of_week: Optional[str] = Field(None, description="Comma-separated day codes.")
    detail_scheduled_timing_repeat_time_of_day: Optional[str] = Field(None, description="Comma-separated times.")
    detail_scheduled_timing_repeat_when: Optional[str] = Field(None, description="Comma-separated when codes.")
    detail_scheduled_timing_repeat_offset: Optional[int] = None
    detail_scheduled_timing_repeat_bounds_start: Optional[datetime] = None
    detail_scheduled_timing_repeat_bounds_end: Optional[datetime] = None
    # timing.repeat.bounds[x] — Duration variant
    detail_scheduled_timing_repeat_bounds_duration_value: Optional[float] = None
    detail_scheduled_timing_repeat_bounds_duration_comparator: Optional[str] = Field(None, description="< | <= | >= | >")
    detail_scheduled_timing_repeat_bounds_duration_unit: Optional[str] = None
    detail_scheduled_timing_repeat_bounds_duration_system: Optional[str] = None
    detail_scheduled_timing_repeat_bounds_duration_code: Optional[str] = None
    # timing.repeat.bounds[x] — Range variant
    detail_scheduled_timing_repeat_bounds_range_low_value: Optional[float] = None
    detail_scheduled_timing_repeat_bounds_range_low_unit: Optional[str] = None
    detail_scheduled_timing_repeat_bounds_range_low_system: Optional[str] = None
    detail_scheduled_timing_repeat_bounds_range_low_code: Optional[str] = None
    detail_scheduled_timing_repeat_bounds_range_high_value: Optional[float] = None
    detail_scheduled_timing_repeat_bounds_range_high_unit: Optional[str] = None
    detail_scheduled_timing_repeat_bounds_range_high_system: Optional[str] = None
    detail_scheduled_timing_repeat_bounds_range_high_code: Optional[str] = None

    # scheduled[x] — Period variant
    detail_scheduled_period_start: Optional[datetime] = None
    detail_scheduled_period_end: Optional[datetime] = None

    # scheduled[x] — string variant
    detail_scheduled_string: Optional[str] = None

    # detail.location (0..1 Reference(Location))
    detail_location: Optional[str] = Field(None, description="Reference to Location, e.g. 'Location/230001'.")
    detail_location_display: Optional[str] = None

    # detail.product[x] — CodeableConcept variant
    detail_product_codeable_concept_system: Optional[str] = None
    detail_product_codeable_concept_code: Optional[str] = None
    detail_product_codeable_concept_display: Optional[str] = None
    detail_product_codeable_concept_text: Optional[str] = None

    # detail.product[x] — Reference(Medication|Substance) variant
    detail_product_reference: Optional[str] = Field(
        None, description="Reference to Medication/<id> or Substance/<id>."
    )
    detail_product_reference_display: Optional[str] = None

    # detail.dailyAmount (0..1 SimpleQuantity)
    detail_daily_amount_value: Optional[float] = None
    detail_daily_amount_unit: Optional[str] = None
    detail_daily_amount_system: Optional[str] = None
    detail_daily_amount_code: Optional[str] = None

    # detail.quantity (0..1 SimpleQuantity)
    detail_quantity_value: Optional[float] = None
    detail_quantity_unit: Optional[str] = None
    detail_quantity_system: Optional[str] = None
    detail_quantity_code: Optional[str] = None

    # detail.description
    detail_description: Optional[str] = None

    # grandchild arrays
    outcome_codeable_concepts: Optional[List[CarePlanActivityOutcomeCCInput]] = None
    outcome_references: Optional[List[CarePlanActivityOutcomeRefInput]] = None
    progress: Optional[List[CarePlanActivityProgressInput]] = None
    detail_reason_codes: Optional[List[CarePlanActivityDetailReasonCodeInput]] = None
    detail_reason_references: Optional[List[CarePlanActivityDetailReasonRefInput]] = None
    detail_goals: Optional[List[CarePlanActivityDetailGoalInput]] = None
    detail_performers: Optional[List[CarePlanActivityDetailPerformerInput]] = None

    @model_validator(mode="after")
    def _activity_rules(self):
        fields = type(self).model_fields
        has = lambda v: v is not None and v != [] and v != ""  # noqa: E731
        detail_fields = [
            n for n in fields if n.startswith("detail_") and n != "detail_status" and has(getattr(self, n))
        ]
        has_detail = bool(detail_fields) or self.detail_status is not None
        # cpl-3: Provide a reference or detail, not both
        if self.reference and has_detail:
            raise ValueError("cpl-3: provide an activity reference or activity detail, not both.")
        if has_detail and self.detail_status is None:
            raise ValueError("activity.detail.status is required (1..1) when activity.detail is supplied.")
        # scheduled[x]: at most one of Timing | Period | string
        timing_set = any(has(getattr(self, n)) for n in fields if n.startswith("detail_scheduled_timing_"))
        period_set = self.detail_scheduled_period_start is not None or self.detail_scheduled_period_end is not None
        used = [n for n, v in (("Timing", timing_set), ("Period", period_set), ("string", self.detail_scheduled_string is not None)) if v]
        if len(used) > 1:
            raise ValueError(f"activity.detail.scheduled[x]: supply at most one variant; got {used}.")
        # product[x]: CodeableConcept | Reference
        cc_set = any([self.detail_product_codeable_concept_system, self.detail_product_codeable_concept_code,
                      self.detail_product_codeable_concept_display, self.detail_product_codeable_concept_text])
        if cc_set and self.detail_product_reference:
            raise ValueError("activity.detail.product[x]: supply a CodeableConcept or a Reference, not both.")
        # timing.repeat.bounds[x]: at most one of Duration | Range | Period
        pre = "detail_scheduled_timing_repeat_bounds_"
        bounds = [n for n, present in (
            ("Duration", any(has(getattr(self, k)) for k in fields if k.startswith(pre + "duration_"))),
            ("Range", any(has(getattr(self, k)) for k in fields if k.startswith(pre + "range_"))),
            ("Period", self.detail_scheduled_timing_repeat_bounds_start is not None or self.detail_scheduled_timing_repeat_bounds_end is not None),
        ) if present]
        if len(bounds) > 1:
            raise ValueError(f"Timing.repeat.bounds[x]: supply at most one variant; got {bounds}.")
        if (self.detail_scheduled_period_start and self.detail_scheduled_period_end
                and self.detail_scheduled_period_end < self.detail_scheduled_period_start):
            raise ValueError("detail_scheduled_period_end must not be before detail_scheduled_period_start.")
        return self


class CarePlanCreateSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "user_id": "u-test",
                    "org_id": "org-test",
                    "status": "active",
                    "intent": "plan",
                    "title": "Diabetes Management Plan",
                    "subject": "Patient/10001",
                }
            ]
        },
    )

    user_id: str
    org_id: str
    created_by: Optional[str] = None

    status: CarePlanStatus = Field(..., description="draft | active | on-hold | revoked | completed | entered-in-error | unknown")
    intent: CarePlanIntent = Field(..., description="proposal | plan | order | option")

    subject: str = Field(..., description="Required (1..1). Reference to Patient/<id> or Group/<id>.")
    subject_display: Optional[str] = None

    title: Optional[str] = None
    description: Optional[str] = None
    encounter: Optional[str] = Field(None, description="Reference to Encounter, e.g. 'Encounter/20001'.")
    encounter_display: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    created: Optional[datetime] = None
    author: Optional[str] = Field(
        None,
        description=(
            "Allowed: Patient/<id>, Practitioner/<id>, PractitionerRole/<id>, "
            "Device/<id>, RelatedPerson/<id>, Organization/<id>, CareTeam/<id>."
        ),
    )
    author_display: Optional[str] = None
    instantiates_canonical: Optional[str] = Field(None, description="Comma-separated canonical URIs.")
    instantiates_uri: Optional[str] = Field(None, description="Comma-separated URIs.")

    identifiers: Optional[List[CarePlanIdentifierInput]] = None
    based_on: Optional[List[CarePlanBasedOnInput]] = None
    replaces: Optional[List[CarePlanReplacesInput]] = None
    part_of: Optional[List[CarePlanPartOfInput]] = None
    categories: Optional[List[CarePlanCategoryInput]] = None
    contributors: Optional[List[CarePlanContributorInput]] = None
    care_teams: Optional[List[CarePlanCareTeamInput]] = None
    addresses: Optional[List[CarePlanAddressesInput]] = None
    supporting_info: Optional[List[CarePlanSupportingInfoInput]] = None
    goals: Optional[List[CarePlanGoalInput]] = None
    activities: Optional[List[CarePlanActivityInput]] = None
    notes: Optional[List[CarePlanNoteInput]] = None

    @model_validator(mode="after")
    def _period_order(self):
        if self.period_start and self.period_end and self.period_end < self.period_start:
            raise ValueError("period_end must not be before period_start.")
        return self


class CarePlanPatchSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    status: Optional[CarePlanStatus] = Field(None, description="Cannot be null.")
    intent: Optional[CarePlanIntent] = Field(None, description="Cannot be null.")
    title: Optional[str] = None
    description: Optional[str] = None
    subject: Optional[str] = Field(None, description="Cannot be null. Reference to Patient/<id> or Group/<id>.")
    subject_display: Optional[str] = None
    encounter: Optional[str] = None
    encounter_display: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    created: Optional[datetime] = None
    author: Optional[str] = None
    author_display: Optional[str] = None
    instantiates_canonical: Optional[str] = None
    instantiates_uri: Optional[str] = None

    identifiers: Optional[List[CarePlanIdentifierInput]] = None
    based_on: Optional[List[CarePlanBasedOnInput]] = None
    replaces: Optional[List[CarePlanReplacesInput]] = None
    part_of: Optional[List[CarePlanPartOfInput]] = None
    categories: Optional[List[CarePlanCategoryInput]] = None
    contributors: Optional[List[CarePlanContributorInput]] = None
    care_teams: Optional[List[CarePlanCareTeamInput]] = None
    addresses: Optional[List[CarePlanAddressesInput]] = None
    supporting_info: Optional[List[CarePlanSupportingInfoInput]] = None
    goals: Optional[List[CarePlanGoalInput]] = None
    activities: Optional[List[CarePlanActivityInput]] = None
    notes: Optional[List[CarePlanNoteInput]] = None
    updated_by: Optional[str] = None

    @field_validator("status", "intent", "subject")
    @classmethod
    def _required_not_null(cls, v):
        if v is None:
            raise ValueError("must not be null")
        return v

    @model_validator(mode="after")
    def _period_order(self):
        if self.period_start and self.period_end and self.period_end < self.period_start:
            raise ValueError("period_end must not be before period_start.")
        return self


# ── Search ─────────────────────────────────────────────────────────────────────


class ListCarePlansSchema(BaseModel):
    """
    Search parameters for GET /care-plans — the FHIR R4 CarePlan search params plus `_id` and `_lastUpdated`.

    The router builds this from explicitly declared Query parameters (`_id`, `_lastUpdated` and the
    hyphenated names are not valid Python identifiers); the service then forwards it to the fhir-server
    under the FHIR parameter names.

    Token params: `code` | `system|code` | `|code` | `system|`; comma = OR.
    Reference params: `Type/id` or bare numeric id.
    Date params (`date`, `activity_date`, `last_updated`): optional prefix eq|ne|gt|lt|ge|le|sa|eb|ap; repeat for AND.
    """

    model_config = ConfigDict(extra="forbid")

    id: Optional[str] = Field(None, description="_id — public care_plan_id(s), comma-separated.")
    identifier: Optional[str] = Field(None, description="Token `[system|]value` of CarePlan.identifier.")
    status: Optional[str] = Field(None, description="Token: draft|active|on-hold|revoked|completed|entered-in-error|unknown (comma = OR).")
    intent: Optional[str] = Field(None, description="Token: proposal|plan|order|option (comma = OR).")
    category: Optional[str] = Field(None, description="Token `[system|]code` of CarePlan.category.")
    activity_code: Optional[str] = Field(None, description="activity-code — token of activity.detail.code.")
    activity_reference: Optional[str] = Field(None, description="activity-reference — activity.reference, e.g. 'ServiceRequest/80001'.")
    based_on: Optional[str] = Field(None, description="based-on — CarePlan reference.")
    replaces: Optional[str] = Field(None, description="CarePlan reference.")
    part_of: Optional[str] = Field(None, description="part-of — CarePlan reference.")
    care_team: Optional[str] = Field(None, description="care-team — CareTeam reference.")
    condition: Optional[str] = Field(None, description="Condition reference (CarePlan.addresses).")
    goal: Optional[str] = Field(None, description="Goal reference.")
    encounter: Optional[str] = Field(None, description="Encounter reference: 'Encounter/20001' or '20001'.")
    subject: Optional[str] = Field(None, description="Subject reference (Patient|Group).")
    patient: Optional[str] = Field(None, description="Subject patient reference: 'Patient/10001' or '10001'.")
    performer: Optional[str] = Field(None, description="activity.detail.performer reference.")
    instantiates_canonical: Optional[str] = Field(None, description="instantiates-canonical — canonical URL or 'PlanDefinition/1'-style suffix.")
    instantiates_uri: Optional[str] = Field(None, description="instantiates-uri — URI instantiated by the plan.")
    date: Optional[List[str]] = Field(None, description="Plan period with optional prefix e.g. 'ge2024-01-01'.")
    activity_date: Optional[List[str]] = Field(None, description="activity-date — activity scheduled period with optional prefix.")
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
        allowed = {s.value for s in CarePlanStatus}
        bad = [t for t in v.split(",") if t.strip() and t.strip() not in allowed]
        if bad:
            raise ValueError(f"Invalid status {bad}. Allowed: {sorted(allowed)}")
        return v

    @field_validator("intent")
    @classmethod
    def _validate_intent_tokens(cls, v: Optional[str]) -> Optional[str]:
        """Reject unknown intent codes early (comma-separated OR list allowed) with a gateway 422."""
        if v is None:
            return v
        allowed = {s.value for s in CarePlanIntent}
        bad = [t for t in v.split(",") if t.strip() and t.strip() not in allowed]
        if bad:
            raise ValueError(f"Invalid intent {bad}. Allowed: {sorted(allowed)}")
        return v
