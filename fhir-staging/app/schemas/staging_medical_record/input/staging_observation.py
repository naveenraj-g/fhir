"""Input schemas for an extracted Observation, nested inside a staging record.

Ported from fhir-server's app/schemas/observation/input.py so the two services
accept the same shape and a staged staging_observation can be promoted without
translation. Two differences:

  - No `user_id` / `org_id` / `created_by`. A nested staging_observation inherits all
    three from its parent staging record — the document and everything
    extracted from it belong to one tenant by construction, so accepting them
    per staging_observation would only let them disagree.
  - `status` has a default instead of being required. See its Field docstring.

There is no StagingObservationPatchSchema: observations are not individually
addressable here. A PATCH on the staging record replaces the whole
`observations` list (see StagingMedicalRecordPatchSchema).
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.staging_observation.enums import StagingObservationStatus


# ── Shared value[x] mixin fields (reused by Observation and Component) ─────────

class _ValueXFields(BaseModel):
    """value[x] fields shared by both StagingObservationInput and StagingObservationComponentInput."""
    # Quantity
    value_quantity_value: Optional[float] = None
    value_quantity_comparator: Optional[str] = Field(None, description="<|<=|>=|>")
    value_quantity_unit: Optional[str] = None
    value_quantity_system: Optional[str] = None
    value_quantity_code: Optional[str] = None
    # CodeableConcept
    value_codeable_concept_system: Optional[str] = None
    value_codeable_concept_code: Optional[str] = None
    value_codeable_concept_display: Optional[str] = None
    value_codeable_concept_text: Optional[str] = None
    # Primitives
    value_string: Optional[str] = None
    value_boolean: Optional[bool] = None
    value_integer: Optional[int] = None
    value_time: Optional[str] = Field(None, description="HH:mm:ss")
    value_date_time: Optional[datetime] = None
    # Period
    value_period_start: Optional[datetime] = None
    value_period_end: Optional[datetime] = None
    # Range
    value_range_low_value: Optional[float] = None
    value_range_low_unit: Optional[str] = None
    value_range_low_system: Optional[str] = None
    value_range_low_code: Optional[str] = None
    value_range_high_value: Optional[float] = None
    value_range_high_unit: Optional[str] = None
    value_range_high_system: Optional[str] = None
    value_range_high_code: Optional[str] = None
    # Ratio
    value_ratio_numerator_value: Optional[float] = None
    value_ratio_numerator_comparator: Optional[str] = None
    value_ratio_numerator_unit: Optional[str] = None
    value_ratio_numerator_system: Optional[str] = None
    value_ratio_numerator_code: Optional[str] = None
    value_ratio_denominator_value: Optional[float] = None
    value_ratio_denominator_comparator: Optional[str] = None
    value_ratio_denominator_unit: Optional[str] = None
    value_ratio_denominator_system: Optional[str] = None
    value_ratio_denominator_code: Optional[str] = None
    # SampledData
    value_sampled_data_origin_value: Optional[float] = None
    value_sampled_data_origin_unit: Optional[str] = None
    value_sampled_data_origin_system: Optional[str] = None
    value_sampled_data_origin_code: Optional[str] = None
    value_sampled_data_period: Optional[float] = None
    value_sampled_data_factor: Optional[float] = None
    value_sampled_data_lower_limit: Optional[float] = None
    value_sampled_data_upper_limit: Optional[float] = None
    value_sampled_data_dimensions: Optional[int] = None
    value_sampled_data_data: Optional[str] = None


# ── Sub-input schemas ───────────────────────────────────────────────────────────


class StagingObservationIdentifierInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    use: Optional[str] = None
    type_system: Optional[str] = None
    type_code: Optional[str] = None
    type_display: Optional[str] = None
    type_text: Optional[str] = None
    system: Optional[str] = None
    value: str
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    assigner: Optional[str] = None


class StagingObservationBasedOnInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: str = Field(
        ...,
        description="Reference to CarePlan|DeviceRequest|ImmunizationRecommendation|MedicationRequest|NutritionOrder|ServiceRequest.",
    )
    reference_display: Optional[str] = None


class StagingObservationPartOfInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: str = Field(
        ...,
        description="Reference to MedicationAdministration|MedicationDispense|MedicationStatement|Procedure|Immunization|ImagingStudy.",
    )
    reference_display: Optional[str] = None


class StagingObservationCategoryInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class StagingObservationFocusInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: str = Field(..., description="Open FHIR reference e.g. 'Condition/120001'.")
    reference_display: Optional[str] = None


class StagingObservationPerformerInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: str = Field(
        ...,
        description="Reference to Practitioner|PractitionerRole|Organization|CareTeam|Patient|RelatedPerson.",
    )
    reference_display: Optional[str] = None


class StagingObservationInterpretationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class StagingObservationNoteInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str
    time: Optional[datetime] = None
    author_string: Optional[str] = None
    author_reference: Optional[str] = Field(
        None, description="Open reference e.g. 'Practitioner/30001'."
    )


class StagingObservationAppliesToInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class StagingObservationReferenceRangeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    low_value: Optional[float] = None
    low_unit: Optional[str] = None
    low_system: Optional[str] = None
    low_code: Optional[str] = None
    high_value: Optional[float] = None
    high_unit: Optional[str] = None
    high_system: Optional[str] = None
    high_code: Optional[str] = None
    type_system: Optional[str] = None
    type_code: Optional[str] = None
    type_display: Optional[str] = None
    type_text: Optional[str] = None
    age_low_value: Optional[float] = None
    age_low_unit: Optional[str] = None
    age_low_system: Optional[str] = None
    age_low_code: Optional[str] = None
    age_high_value: Optional[float] = None
    age_high_unit: Optional[str] = None
    age_high_system: Optional[str] = None
    age_high_code: Optional[str] = None
    text: Optional[str] = None
    applies_to: Optional[List[StagingObservationAppliesToInput]] = None


class StagingObservationHasMemberInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: str = Field(
        ..., description="Reference to Observation|QuestionnaireResponse|MolecularSequence."
    )
    reference_display: Optional[str] = None


class StagingObservationDerivedFromInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: str = Field(
        ...,
        description="Reference to DocumentReference|ImagingStudy|Media|QuestionnaireResponse|Observation|MolecularSequence.",
    )
    reference_display: Optional[str] = None


class StagingObservationComponentInput(_ValueXFields):
    model_config = ConfigDict(extra="forbid")
    # code (1..1)
    code_system: Optional[str] = None
    code_code: Optional[str] = None
    code_display: Optional[str] = None
    code_text: Optional[str] = None
    # dataAbsentReason
    data_absent_reason_system: Optional[str] = None
    data_absent_reason_code: Optional[str] = None
    data_absent_reason_display: Optional[str] = None
    data_absent_reason_text: Optional[str] = None
    interpretation: Optional[List[StagingObservationInterpretationInput]] = None
    reference_range: Optional[List[StagingObservationReferenceRangeInput]] = None


# ── Observation input ──────────────────────────────────────────────────────────────


class StagingObservationInput(_ValueXFields):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                # No user_id/org_id here on purpose — they come from the
                # parent staging record, and extra="forbid" would reject them.
                "status": "final",
                "code_system": "http://loinc.org",
                "code_code": "8867-4",
                "code_display": "Heart rate",
                "subject": "Patient/10001",
                "encounter_id": 20001,
                "effective_date_time": "2026-05-17T09:00:00Z",
                "value_quantity_value": 72,
                "value_quantity_unit": "beats/minute",
                "value_quantity_system": "http://unitsofmeasure.org",
                "value_quantity_code": "/min",
                "category": [
                    {
                        "coding_system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "coding_code": "vital-signs",
                        "coding_display": "Vital Signs",
                    }
                ],
            }
        },
    )

    # Required
    status: StagingObservationStatus = Field(
        StagingObservationStatus.preliminary,
        description=(
            "Defaults to 'preliminary' — FHIR's own "
            "term for interim or unverified data, which is precisely what a "
            "freshly extracted staging_observation is. The column is NOT NULL (status "
            "is 1..1 in R4), so a default is required somewhere; putting it "
            "here keeps the agent from having to assert a status it cannot know."
        ),
    )

    # code (1..1)
    code_system: Optional[str] = None
    code_code: Optional[str] = None
    code_display: Optional[str] = None
    code_text: Optional[str] = None

    # subject
    subject: Optional[str] = Field(None, description="Reference e.g. 'Patient/10001'.")
    subject_display: Optional[str] = None

    # encounter
    encounter_id: Optional[int] = Field(None, description="Public encounter_id.")
    encounter_display: Optional[str] = None

    # effective[x]
    effective_date_time: Optional[datetime] = None
    effective_period_start: Optional[datetime] = None
    effective_period_end: Optional[datetime] = None
    effective_instant: Optional[datetime] = None
    # Timing variant
    effective_timing_event: Optional[str] = Field(None, description="Comma-separated ISO datetimes.")
    effective_timing_code_system: Optional[str] = None
    effective_timing_code_code: Optional[str] = None
    effective_timing_code_display: Optional[str] = None
    effective_timing_code_text: Optional[str] = None
    effective_timing_repeat_bounds_duration_value: Optional[float] = None
    effective_timing_repeat_bounds_duration_comparator: Optional[str] = None
    effective_timing_repeat_bounds_duration_unit: Optional[str] = None
    effective_timing_repeat_bounds_duration_system: Optional[str] = None
    effective_timing_repeat_bounds_duration_code: Optional[str] = None
    effective_timing_repeat_bounds_range_low_value: Optional[float] = None
    effective_timing_repeat_bounds_range_low_unit: Optional[str] = None
    effective_timing_repeat_bounds_range_low_system: Optional[str] = None
    effective_timing_repeat_bounds_range_low_code: Optional[str] = None
    effective_timing_repeat_bounds_range_high_value: Optional[float] = None
    effective_timing_repeat_bounds_range_high_unit: Optional[str] = None
    effective_timing_repeat_bounds_range_high_system: Optional[str] = None
    effective_timing_repeat_bounds_range_high_code: Optional[str] = None
    effective_timing_repeat_bounds_period_start: Optional[datetime] = None
    effective_timing_repeat_bounds_period_end: Optional[datetime] = None
    effective_timing_repeat_count: Optional[int] = None
    effective_timing_repeat_count_max: Optional[int] = None
    effective_timing_repeat_duration: Optional[float] = None
    effective_timing_repeat_duration_max: Optional[float] = None
    effective_timing_repeat_duration_unit: Optional[str] = None
    effective_timing_repeat_frequency: Optional[int] = None
    effective_timing_repeat_frequency_max: Optional[int] = None
    effective_timing_repeat_period: Optional[float] = None
    effective_timing_repeat_period_max: Optional[float] = None
    effective_timing_repeat_period_unit: Optional[str] = None
    effective_timing_repeat_day_of_week: Optional[str] = Field(None, description="Comma-separated e.g. 'mon,wed,fri'.")
    effective_timing_repeat_time_of_day: Optional[str] = Field(None, description="Comma-separated HH:MM.")
    effective_timing_repeat_when: Optional[str] = Field(None, description="Comma-separated event codes.")
    effective_timing_repeat_offset: Optional[int] = None

    issued: Optional[datetime] = None

    # dataAbsentReason
    data_absent_reason_system: Optional[str] = None
    data_absent_reason_code: Optional[str] = None
    data_absent_reason_display: Optional[str] = None
    data_absent_reason_text: Optional[str] = None

    # bodySite
    body_site_system: Optional[str] = None
    body_site_code: Optional[str] = None
    body_site_display: Optional[str] = None
    body_site_text: Optional[str] = None

    # method
    method_system: Optional[str] = None
    method_code: Optional[str] = None
    method_display: Optional[str] = None
    method_text: Optional[str] = None

    # specimen (0..1)
    specimen: Optional[str] = Field(None, description="Reference to Specimen e.g. 'Specimen/10001'.")
    specimen_display: Optional[str] = None

    # device (0..1)
    device: Optional[str] = Field(None, description="Reference to Device|DeviceMetric e.g. 'Device/10001'.")
    device_display: Optional[str] = None

    # child arrays
    identifier: Optional[List[StagingObservationIdentifierInput]] = None
    based_on: Optional[List[StagingObservationBasedOnInput]] = None
    part_of: Optional[List[StagingObservationPartOfInput]] = None
    category: Optional[List[StagingObservationCategoryInput]] = None
    focus: Optional[List[StagingObservationFocusInput]] = None
    performer: Optional[List[StagingObservationPerformerInput]] = None
    interpretation: Optional[List[StagingObservationInterpretationInput]] = None
    note: Optional[List[StagingObservationNoteInput]] = None
    reference_range: Optional[List[StagingObservationReferenceRangeInput]] = None
    has_member: Optional[List[StagingObservationHasMemberInput]] = None
    derived_from: Optional[List[StagingObservationDerivedFromInput]] = None
    component: Optional[List[StagingObservationComponentInput]] = None


