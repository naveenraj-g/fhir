"""
Response schemas for Task resources (fhir-gql gateway).

Plain* classes mirror the fhir-server snake_case output (`application/json`);
Fhir* classes document the `application/fhir+json` shape for Swagger only.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field



# ---------------------------------------------------------------------------
# FHIR (camelCase) sub-schemas
# ---------------------------------------------------------------------------

class FHIRReference(BaseModel):
    """FHIR Reference datatype (reference + display)."""

    reference: Optional[str] = None
    display: Optional[str] = None


class FHIRCodeableConcept(BaseModel):
    """FHIR CodeableConcept datatype (coding[] + text)."""

    coding: Optional[List[Dict[str, Any]]] = None
    text: Optional[str] = None



class FHIRTaskNote(BaseModel):
    """FHIRTaskNote — see the fhir-server schema of the same name."""

    text: str
    time: Optional[str] = None
    authorString: Optional[str] = None
    authorReference: Optional[FHIRReference] = None


class FHIRTaskRestriction(BaseModel):
    """FHIRTaskRestriction — see the fhir-server schema of the same name."""

    repetitions: Optional[int] = None
    period: Optional[Dict[str, Any]] = None
    recipient: Optional[List[FHIRReference]] = None


class FHIRTaskInputItem(BaseModel):
    """FHIRTaskInputItem — see the fhir-server schema of the same name."""

    type: FHIRCodeableConcept
    valueBoolean: Optional[bool] = None
    valueCode: Optional[str] = None
    valueDate: Optional[str] = None
    valueDateTime: Optional[str] = None
    valueDecimal: Optional[float] = None
    valueInteger: Optional[int] = None
    valueString: Optional[str] = None
    valueUri: Optional[str] = None
    valueReference: Optional[FHIRReference] = None
    valueTime: Optional[str] = None
    valueInstant: Optional[str] = None
    valueMarkdown: Optional[str] = None
    valueCanonical: Optional[str] = None
    valueUrl: Optional[str] = None
    valuePositiveInt: Optional[int] = None
    valueUnsignedInt: Optional[int] = None
    valueBase64Binary: Optional[str] = None
    valueId: Optional[str] = None
    valueCoding: Optional[Dict[str, Any]] = None
    valueCodeableConcept: Optional[FHIRCodeableConcept] = None
    valueQuantity: Optional[Dict[str, Any]] = None
    valuePeriod: Optional[Dict[str, Any]] = None
    valueRange: Optional[Dict[str, Any]] = None
    valueAttachment: Optional[Dict[str, Any]] = None
    valueIdentifier: Optional[Dict[str, Any]] = None
    valueMoney: Optional[Dict[str, Any]] = None
    valueRatio: Optional[Dict[str, Any]] = None


class FHIRTaskOutputItem(BaseModel):
    """FHIRTaskOutputItem — see the fhir-server schema of the same name."""

    type: FHIRCodeableConcept
    valueBoolean: Optional[bool] = None
    valueCode: Optional[str] = None
    valueDate: Optional[str] = None
    valueDateTime: Optional[str] = None
    valueDecimal: Optional[float] = None
    valueInteger: Optional[int] = None
    valueString: Optional[str] = None
    valueUri: Optional[str] = None
    valueReference: Optional[FHIRReference] = None
    valueTime: Optional[str] = None
    valueInstant: Optional[str] = None
    valueMarkdown: Optional[str] = None
    valueCanonical: Optional[str] = None
    valueUrl: Optional[str] = None
    valuePositiveInt: Optional[int] = None
    valueUnsignedInt: Optional[int] = None
    valueBase64Binary: Optional[str] = None
    valueId: Optional[str] = None
    valueCoding: Optional[Dict[str, Any]] = None
    valueCodeableConcept: Optional[FHIRCodeableConcept] = None
    valueQuantity: Optional[Dict[str, Any]] = None
    valuePeriod: Optional[Dict[str, Any]] = None
    valueRange: Optional[Dict[str, Any]] = None
    valueAttachment: Optional[Dict[str, Any]] = None
    valueIdentifier: Optional[Dict[str, Any]] = None
    valueMoney: Optional[Dict[str, Any]] = None
    valueRatio: Optional[Dict[str, Any]] = None


class FhirTaskResponse(BaseModel):
    """FhirTaskResponse — see the fhir-server schema of the same name."""

    resourceType: str = Field("Task", description="Always 'Task'.")
    id: str
    identifier: Optional[List[Dict[str, Any]]] = None
    instantiatesCanonical: Optional[str] = None
    instantiatesUri: Optional[str] = None
    basedOn: Optional[List[FHIRReference]] = None
    groupIdentifier: Optional[Dict[str, Any]] = None
    partOf: Optional[List[FHIRReference]] = None
    status: str
    statusReason: Optional[FHIRCodeableConcept] = None
    businessStatus: Optional[FHIRCodeableConcept] = None
    intent: str
    priority: Optional[str] = None
    code: Optional[FHIRCodeableConcept] = None
    description: Optional[str] = None
    focus: Optional[FHIRReference] = None
    for_: Optional[FHIRReference] = Field(None, alias="for")
    encounter: Optional[FHIRReference] = None
    executionPeriod: Optional[Dict[str, Any]] = None
    authoredOn: Optional[str] = None
    lastModified: Optional[str] = None
    requester: Optional[FHIRReference] = None
    performerType: Optional[List[FHIRCodeableConcept]] = None
    owner: Optional[FHIRReference] = None
    location: Optional[FHIRReference] = None
    reasonCode: Optional[FHIRCodeableConcept] = None
    reasonReference: Optional[FHIRReference] = None
    insurance: Optional[List[FHIRReference]] = None
    note: Optional[List[FHIRTaskNote]] = None
    relevantHistory: Optional[List[FHIRReference]] = None
    restriction: Optional[FHIRTaskRestriction] = None
    input: Optional[List[FHIRTaskInputItem]] = None
    output: Optional[List[FHIRTaskOutputItem]] = None

    model_config = ConfigDict(populate_by_name=True)


class FhirBundleEntry(BaseModel):
    """FhirBundleEntry — see the fhir-server schema of the same name."""

    resource: FhirTaskResponse


class FhirBundleResponse(BaseModel):
    """FHIR R4 Bundle (searchset) for the Task list endpoint."""

    resourceType: str = "Bundle"
    type: str = "searchset"
    total: Optional[int] = None
    entry: Optional[List[FhirBundleEntry]] = None


# ---------------------------------------------------------------------------
# Plain (snake_case) sub-schemas
# ---------------------------------------------------------------------------


class PlainTaskIdentifier(BaseModel):
    """PlainTaskIdentifier — see the fhir-server schema of the same name."""

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


class PlainTaskBasedOn(BaseModel):
    """PlainTaskBasedOn — see the fhir-server schema of the same name."""

    model_config = ConfigDict(extra="allow")
    id: int
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    reference_display: Optional[str] = None


class PlainTaskPartOf(BaseModel):
    """PlainTaskPartOf — see the fhir-server schema of the same name."""

    model_config = ConfigDict(extra="allow")
    id: int
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    reference_display: Optional[str] = None


class PlainTaskPerformerType(BaseModel):
    """PlainTaskPerformerType — see the fhir-server schema of the same name."""

    model_config = ConfigDict(extra="allow")
    id: int
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class PlainTaskInsurance(BaseModel):
    """PlainTaskInsurance — see the fhir-server schema of the same name."""

    model_config = ConfigDict(extra="allow")
    id: int
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    reference_display: Optional[str] = None


class PlainTaskNote(BaseModel):
    """PlainTaskNote — see the fhir-server schema of the same name."""

    model_config = ConfigDict(extra="allow")
    id: int
    text: str
    time: Optional[str] = None
    author_string: Optional[str] = None
    author_reference_type: Optional[str] = None
    author_reference_id: Optional[int] = None
    author_reference_display: Optional[str] = None


class PlainTaskRelevantHistory(BaseModel):
    """PlainTaskRelevantHistory — see the fhir-server schema of the same name."""

    model_config = ConfigDict(extra="allow")
    id: int
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    reference_display: Optional[str] = None


class PlainTaskRestrictionRecipient(BaseModel):
    """PlainTaskRestrictionRecipient — see the fhir-server schema of the same name."""

    model_config = ConfigDict(extra="allow")
    id: int
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    reference_display: Optional[str] = None


class PlainTaskInputItem(BaseModel):
    """PlainTaskInputItem — see the fhir-server schema of the same name."""

    model_config = ConfigDict(extra="allow")
    id: int
    type_system: Optional[str] = None
    type_code: Optional[str] = None
    type_display: Optional[str] = None
    type_text: Optional[str] = None
    value_boolean: Optional[bool] = None
    value_code: Optional[str] = None
    value_date: Optional[str] = None
    value_date_time: Optional[str] = None
    value_decimal: Optional[float] = None
    value_integer: Optional[int] = None
    value_string: Optional[str] = None
    value_uri: Optional[str] = None
    value_reference_type: Optional[str] = None
    value_reference_id: Optional[int] = None
    value_reference_display: Optional[str] = None
    value_time: Optional[str] = None
    value_instant: Optional[str] = None
    value_markdown: Optional[str] = None
    value_canonical: Optional[str] = None
    value_url: Optional[str] = None
    value_positive_int: Optional[int] = None
    value_unsigned_int: Optional[int] = None
    value_base64_binary: Optional[str] = None
    value_id: Optional[str] = None
    value_coding_system: Optional[str] = None
    value_coding_code: Optional[str] = None
    value_coding_display: Optional[str] = None
    value_codeable_concept_system: Optional[str] = None
    value_codeable_concept_code: Optional[str] = None
    value_codeable_concept_display: Optional[str] = None
    value_codeable_concept_text: Optional[str] = None
    value_quantity_value: Optional[float] = None
    value_quantity_unit: Optional[str] = None
    value_quantity_system: Optional[str] = None
    value_quantity_code: Optional[str] = None
    value_period_start: Optional[str] = None
    value_period_end: Optional[str] = None
    value_range_low_value: Optional[float] = None
    value_range_low_unit: Optional[str] = None
    value_range_high_value: Optional[float] = None
    value_range_high_unit: Optional[str] = None
    value_attachment_content_type: Optional[str] = None
    value_attachment_language: Optional[str] = None
    value_attachment_data: Optional[str] = None
    value_attachment_url: Optional[str] = None
    value_attachment_size: Optional[int] = None
    value_attachment_hash: Optional[str] = None
    value_attachment_title: Optional[str] = None
    value_attachment_creation: Optional[str] = None
    value_identifier_use: Optional[str] = None
    value_identifier_system: Optional[str] = None
    value_identifier_value: Optional[str] = None
    value_money_value: Optional[float] = None
    value_money_currency: Optional[str] = None
    value_ratio_numerator_value: Optional[float] = None
    value_ratio_numerator_unit: Optional[str] = None
    value_ratio_denominator_value: Optional[float] = None
    value_ratio_denominator_unit: Optional[str] = None


class PlainTaskOutputItem(BaseModel):
    """PlainTaskOutputItem — see the fhir-server schema of the same name."""

    model_config = ConfigDict(extra="allow")
    id: int
    type_system: Optional[str] = None
    type_code: Optional[str] = None
    type_display: Optional[str] = None
    type_text: Optional[str] = None
    value_boolean: Optional[bool] = None
    value_code: Optional[str] = None
    value_date: Optional[str] = None
    value_date_time: Optional[str] = None
    value_decimal: Optional[float] = None
    value_integer: Optional[int] = None
    value_string: Optional[str] = None
    value_uri: Optional[str] = None
    value_reference_type: Optional[str] = None
    value_reference_id: Optional[int] = None
    value_reference_display: Optional[str] = None
    value_time: Optional[str] = None
    value_instant: Optional[str] = None
    value_markdown: Optional[str] = None
    value_canonical: Optional[str] = None
    value_url: Optional[str] = None
    value_positive_int: Optional[int] = None
    value_unsigned_int: Optional[int] = None
    value_base64_binary: Optional[str] = None
    value_id: Optional[str] = None
    value_coding_system: Optional[str] = None
    value_coding_code: Optional[str] = None
    value_coding_display: Optional[str] = None
    value_codeable_concept_system: Optional[str] = None
    value_codeable_concept_code: Optional[str] = None
    value_codeable_concept_display: Optional[str] = None
    value_codeable_concept_text: Optional[str] = None
    value_quantity_value: Optional[float] = None
    value_quantity_unit: Optional[str] = None
    value_quantity_system: Optional[str] = None
    value_quantity_code: Optional[str] = None
    value_period_start: Optional[str] = None
    value_period_end: Optional[str] = None
    value_range_low_value: Optional[float] = None
    value_range_low_unit: Optional[str] = None
    value_range_high_value: Optional[float] = None
    value_range_high_unit: Optional[str] = None
    value_attachment_content_type: Optional[str] = None
    value_attachment_language: Optional[str] = None
    value_attachment_data: Optional[str] = None
    value_attachment_url: Optional[str] = None
    value_attachment_size: Optional[int] = None
    value_attachment_hash: Optional[str] = None
    value_attachment_title: Optional[str] = None
    value_attachment_creation: Optional[str] = None
    value_identifier_use: Optional[str] = None
    value_identifier_system: Optional[str] = None
    value_identifier_value: Optional[str] = None
    value_money_value: Optional[float] = None
    value_money_currency: Optional[str] = None
    value_ratio_numerator_value: Optional[float] = None
    value_ratio_numerator_unit: Optional[str] = None
    value_ratio_denominator_value: Optional[float] = None
    value_ratio_denominator_unit: Optional[str] = None


class TaskRecord(BaseModel):
    """TaskRecord — see the fhir-server schema of the same name."""

    model_config = ConfigDict(extra="allow")
    id: int
    status: Optional[str] = None
    intent: Optional[str] = None
    priority: Optional[str] = None
    description: Optional[str] = None
    instantiates_canonical: Optional[str] = None
    instantiates_uri: Optional[str] = None
    group_identifier_use: Optional[str] = None
    group_identifier_system: Optional[str] = None
    group_identifier_value: Optional[str] = None
    group_identifier_type_system: Optional[str] = None
    group_identifier_type_code: Optional[str] = None
    group_identifier_type_display: Optional[str] = None
    group_identifier_type_text: Optional[str] = None
    status_reason_system: Optional[str] = None
    status_reason_code: Optional[str] = None
    status_reason_display: Optional[str] = None
    status_reason_text: Optional[str] = None
    business_status_system: Optional[str] = None
    business_status_code: Optional[str] = None
    business_status_display: Optional[str] = None
    business_status_text: Optional[str] = None
    code_system: Optional[str] = None
    code_code: Optional[str] = None
    code_display: Optional[str] = None
    code_text: Optional[str] = None
    focus_type: Optional[str] = None
    focus_id: Optional[int] = None
    focus_display: Optional[str] = None
    for_type: Optional[str] = None
    for_id: Optional[int] = None
    for_display: Optional[str] = None
    encounter_type: Optional[str] = None
    encounter_id: Optional[int] = None
    encounter_display: Optional[str] = None
    execution_period_start: Optional[str] = None
    execution_period_end: Optional[str] = None
    authored_on: Optional[str] = None
    last_modified: Optional[str] = None
    requester_type: Optional[str] = None
    requester_id: Optional[int] = None
    requester_display: Optional[str] = None
    owner_type: Optional[str] = None
    owner_id: Optional[int] = None
    owner_display: Optional[str] = None
    location_type: Optional[str] = None
    location_id: Optional[int] = None
    location_display: Optional[str] = None
    reason_code_system: Optional[str] = None
    reason_code_code: Optional[str] = None
    reason_code_display: Optional[str] = None
    reason_code_text: Optional[str] = None
    reason_reference_type: Optional[str] = None
    reason_reference_id: Optional[int] = None
    reason_reference_display: Optional[str] = None
    restriction_repetitions: Optional[int] = None
    restriction_period_start: Optional[str] = None
    restriction_period_end: Optional[str] = None
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    identifiers: Optional[List[PlainTaskIdentifier]] = None
    based_on: Optional[List[PlainTaskBasedOn]] = None
    part_of: Optional[List[PlainTaskPartOf]] = None
    performer_types: Optional[List[PlainTaskPerformerType]] = None
    insurance: Optional[List[PlainTaskInsurance]] = None
    notes: Optional[List[PlainTaskNote]] = None
    relevant_history: Optional[List[PlainTaskRelevantHistory]] = None
    restriction_recipients: Optional[List[PlainTaskRestrictionRecipient]] = None
    inputs: Optional[List[PlainTaskInputItem]] = None
    outputs: Optional[List[PlainTaskOutputItem]] = None


class PaginatedTaskResponse(BaseModel):
    """PaginatedTaskResponse — see the fhir-server schema of the same name."""

    total: int
    limit: int
    offset: int
    data: List[TaskRecord]
