"""Response schemas for an extracted Observation, nested in a staging record.

The Plain (snake_case) half of fhir-server's
app/schemas/observation/response.py, ported verbatim. Its FHIR camelCase
schemas and Bundle are deliberately NOT carried across: this service has no
FHIR wire format, only FHIR-shaped tables.

Every sub-resource model carries `id`, because callers need it to reason about
which rows changed across a PATCH that replaces the list.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict



class PlainStagingObservationIdentifier(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    use: Optional[str] = None
    type_system: Optional[str] = None
    type_code: Optional[str] = None
    type_display: Optional[str] = None
    type_text: Optional[str] = None
    system: Optional[str] = None
    value: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    assigner: Optional[str] = None


class PlainStagingObservationBasedOn(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    reference_display: Optional[str] = None


class PlainStagingObservationPartOf(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    reference_display: Optional[str] = None


class PlainStagingObservationCategory(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class PlainStagingObservationFocus(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    reference_display: Optional[str] = None


class PlainStagingObservationPerformer(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    reference_display: Optional[str] = None


class PlainStagingObservationInterpretation(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class PlainStagingObservationNote(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    text: Optional[str] = None
    time: Optional[str] = None
    author_string: Optional[str] = None
    author_reference_type: Optional[str] = None
    author_reference_id: Optional[int] = None
    author_reference_display: Optional[str] = None


class PlainStagingObservationAppliesTo(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class PlainStagingObservationReferenceRange(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
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
    applies_to: Optional[List[PlainStagingObservationAppliesTo]] = None


class PlainStagingObservationHasMember(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    reference_display: Optional[str] = None


class PlainStagingObservationDerivedFrom(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    reference_display: Optional[str] = None


class PlainStagingObservationComponentInterpretation(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class PlainStagingObservationComponentReferenceRangeAppliesTo(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class PlainStagingObservationComponentReferenceRange(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
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
    applies_to: Optional[List[PlainStagingObservationComponentReferenceRangeAppliesTo]] = None


class PlainStagingObservationComponent(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    code_system: Optional[str] = None
    code_code: Optional[str] = None
    code_display: Optional[str] = None
    code_text: Optional[str] = None
    value_quantity_value: Optional[float] = None
    value_quantity_comparator: Optional[str] = None
    value_quantity_unit: Optional[str] = None
    value_quantity_system: Optional[str] = None
    value_quantity_code: Optional[str] = None
    value_codeable_concept_system: Optional[str] = None
    value_codeable_concept_code: Optional[str] = None
    value_codeable_concept_display: Optional[str] = None
    value_codeable_concept_text: Optional[str] = None
    value_string: Optional[str] = None
    value_boolean: Optional[bool] = None
    value_integer: Optional[int] = None
    value_time: Optional[str] = None
    value_date_time: Optional[str] = None
    value_period_start: Optional[str] = None
    value_period_end: Optional[str] = None
    value_range_low_value: Optional[float] = None
    value_range_low_unit: Optional[str] = None
    value_range_low_system: Optional[str] = None
    value_range_low_code: Optional[str] = None
    value_range_high_value: Optional[float] = None
    value_range_high_unit: Optional[str] = None
    value_range_high_system: Optional[str] = None
    value_range_high_code: Optional[str] = None
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
    data_absent_reason_system: Optional[str] = None
    data_absent_reason_code: Optional[str] = None
    data_absent_reason_display: Optional[str] = None
    data_absent_reason_text: Optional[str] = None
    interpretation: Optional[List[PlainStagingObservationComponentInterpretation]] = None
    reference_range: Optional[List[PlainStagingObservationComponentReferenceRange]] = None


class PlainStagingObservationResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    # Public staging_medical_record_id of the parent — not the internal FK. Present so
    # a caller holding a detached staging_observation can find its way back.
    staging_medical_record_id: Optional[int] = None
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    status: Optional[str] = None
    code_system: Optional[str] = None
    code_code: Optional[str] = None
    code_display: Optional[str] = None
    code_text: Optional[str] = None
    subject_type: Optional[str] = None
    subject_id: Optional[int] = None
    subject_display: Optional[str] = None
    encounter_type: Optional[str] = None
    encounter_id: Optional[int] = None
    encounter_display: Optional[str] = None
    effective_date_time: Optional[str] = None
    effective_period_start: Optional[str] = None
    effective_period_end: Optional[str] = None
    effective_instant: Optional[str] = None
    effective_timing_event: Optional[str] = None
    effective_timing_code_system: Optional[str] = None
    effective_timing_code_code: Optional[str] = None
    effective_timing_code_display: Optional[str] = None
    effective_timing_code_text: Optional[str] = None
    # Timing.repeat — accepted on write, stored, and (unlike in fhir-server,
    # whose plain mapper drops them) returned on read.
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
    effective_timing_repeat_bounds_period_start: Optional[str] = None
    effective_timing_repeat_bounds_period_end: Optional[str] = None
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
    effective_timing_repeat_day_of_week: Optional[str] = None
    effective_timing_repeat_time_of_day: Optional[str] = None
    effective_timing_repeat_when: Optional[str] = None
    effective_timing_repeat_offset: Optional[int] = None
    issued: Optional[str] = None
    value_quantity_value: Optional[float] = None
    value_quantity_comparator: Optional[str] = None
    value_quantity_unit: Optional[str] = None
    value_quantity_system: Optional[str] = None
    value_quantity_code: Optional[str] = None
    value_codeable_concept_system: Optional[str] = None
    value_codeable_concept_code: Optional[str] = None
    value_codeable_concept_display: Optional[str] = None
    value_codeable_concept_text: Optional[str] = None
    value_string: Optional[str] = None
    value_boolean: Optional[bool] = None
    value_integer: Optional[int] = None
    value_time: Optional[str] = None
    value_date_time: Optional[str] = None
    value_period_start: Optional[str] = None
    value_period_end: Optional[str] = None
    value_range_low_value: Optional[float] = None
    value_range_low_unit: Optional[str] = None
    value_range_low_system: Optional[str] = None
    value_range_low_code: Optional[str] = None
    value_range_high_value: Optional[float] = None
    value_range_high_unit: Optional[str] = None
    value_range_high_system: Optional[str] = None
    value_range_high_code: Optional[str] = None
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
    data_absent_reason_system: Optional[str] = None
    data_absent_reason_code: Optional[str] = None
    data_absent_reason_display: Optional[str] = None
    data_absent_reason_text: Optional[str] = None
    body_site_system: Optional[str] = None
    body_site_code: Optional[str] = None
    body_site_display: Optional[str] = None
    body_site_text: Optional[str] = None
    method_system: Optional[str] = None
    method_code: Optional[str] = None
    method_display: Optional[str] = None
    method_text: Optional[str] = None
    specimen_type: Optional[str] = None
    specimen_id: Optional[int] = None
    specimen_display: Optional[str] = None
    device_type: Optional[str] = None
    device_id: Optional[int] = None
    device_display: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    identifier: Optional[List[PlainStagingObservationIdentifier]] = None
    based_on: Optional[List[PlainStagingObservationBasedOn]] = None
    part_of: Optional[List[PlainStagingObservationPartOf]] = None
    category: Optional[List[PlainStagingObservationCategory]] = None
    focus: Optional[List[PlainStagingObservationFocus]] = None
    performer: Optional[List[PlainStagingObservationPerformer]] = None
    interpretation: Optional[List[PlainStagingObservationInterpretation]] = None
    note: Optional[List[PlainStagingObservationNote]] = None
    reference_range: Optional[List[PlainStagingObservationReferenceRange]] = None
    has_member: Optional[List[PlainStagingObservationHasMember]] = None
    derived_from: Optional[List[PlainStagingObservationDerivedFrom]] = None
    component: Optional[List[PlainStagingObservationComponent]] = None
