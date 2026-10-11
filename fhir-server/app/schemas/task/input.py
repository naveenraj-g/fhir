from datetime import date as Date, datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.task.enums import TaskIntent, TaskPriority, TaskStatus


class TaskIdentifierInput(BaseModel):
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


class TaskBasedOnInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: str = Field(..., description="FHIR reference, e.g. 'ServiceRequest/80001'.")
    reference_display: Optional[str] = None


class TaskPartOfInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: str = Field(..., description="Reference to a parent Task, e.g. 'Task/280001'.")
    reference_display: Optional[str] = None


class TaskPerformerTypeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class TaskInsuranceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: str = Field(..., description="Reference to Coverage or ClaimResponse, e.g. 'Coverage/240001'.")
    reference_display: Optional[str] = None


class TaskNoteInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(..., description="Annotation text content.")
    time: Optional[datetime] = None
    author_string: Optional[str] = None
    author_reference: Optional[str] = Field(None, description="Reference to author, e.g. 'Practitioner/30001'.")
    author_reference_display: Optional[str] = None


class TaskRelevantHistoryInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: str = Field(..., description="Reference to Provenance, e.g. 'Provenance/270001'.")
    reference_display: Optional[str] = None


class TaskRestrictionRecipientInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: str = Field(
        ...,
        description=(
            "Reference to recipient. Allowed: Patient/<id>, Practitioner/<id>, "
            "PractitionerRole/<id>, RelatedPerson/<id>, Group/<id>, Organization/<id>."
        ),
    )
    reference_display: Optional[str] = None


class _TaskValueItemInput(BaseModel):
    """
    Shared shape of Task.input and Task.output: a `type` CodeableConcept plus exactly one
    value[x] (R4 cardinality 1..1). Supported variants: boolean, code, date, dateTime, decimal,
    integer, string, uri, time, instant, markdown, canonical, url, positiveInt, unsignedInt,
    base64Binary, id, Reference, Coding, CodeableConcept, Quantity, Period, Range, Attachment,
    Identifier, Money and Ratio. (Address, HumanName, Timing, Dosage and the other rare complex
    types are not stored.)
    """

    model_config = ConfigDict(extra="forbid")

    # type (1..1 CodeableConcept)
    type_system: Optional[str] = None
    type_code: Optional[str] = None
    type_display: Optional[str] = None
    type_text: Optional[str] = None

    # ── value[x] — primitives ──
    value_boolean: Optional[bool] = None
    value_code: Optional[str] = None
    value_date: Optional[Date] = None
    value_date_time: Optional[datetime] = None
    value_decimal: Optional[float] = None
    value_integer: Optional[int] = None
    value_string: Optional[str] = None
    value_uri: Optional[str] = None
    value_time: Optional[str] = Field(None, description="HH:MM:SS")
    value_instant: Optional[datetime] = None
    value_markdown: Optional[str] = None
    value_canonical: Optional[str] = None
    value_url: Optional[str] = None
    value_positive_int: Optional[int] = Field(None, ge=1)
    value_unsigned_int: Optional[int] = Field(None, ge=0)
    value_base64_binary: Optional[str] = None
    value_id: Optional[str] = None

    # ── value[x] — Reference(Any) ──
    value_reference: Optional[str] = Field(None, description="Open reference, e.g. 'Observation/160001'.")
    value_reference_display: Optional[str] = None

    # ── value[x] — complex types ──
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

    value_period_start: Optional[datetime] = None
    value_period_end: Optional[datetime] = None

    value_range_low_value: Optional[float] = None
    value_range_low_unit: Optional[str] = None
    value_range_high_value: Optional[float] = None
    value_range_high_unit: Optional[str] = None

    value_attachment_content_type: Optional[str] = None
    value_attachment_language: Optional[str] = None
    value_attachment_data: Optional[str] = Field(None, description="base64Binary content.")
    value_attachment_url: Optional[str] = None
    value_attachment_size: Optional[int] = Field(None, ge=0)
    value_attachment_hash: Optional[str] = None
    value_attachment_title: Optional[str] = None
    value_attachment_creation: Optional[datetime] = None

    value_identifier_use: Optional[str] = None
    value_identifier_system: Optional[str] = None
    value_identifier_value: Optional[str] = None

    value_money_value: Optional[float] = None
    value_money_currency: Optional[str] = Field(None, description="ISO 4217 currency code.")

    value_ratio_numerator_value: Optional[float] = None
    value_ratio_numerator_unit: Optional[str] = None
    value_ratio_denominator_value: Optional[float] = None
    value_ratio_denominator_unit: Optional[str] = None

    @model_validator(mode="after")
    def _exactly_one_value(self):
        """value[x] is 1..1 — exactly one variant must be supplied."""
        def any_set(*vals):
            return any(v is not None for v in vals)

        groups = {
            "boolean": any_set(self.value_boolean),
            "code": any_set(self.value_code),
            "date": any_set(self.value_date),
            "dateTime": any_set(self.value_date_time),
            "decimal": any_set(self.value_decimal),
            "integer": any_set(self.value_integer),
            "string": any_set(self.value_string),
            "uri": any_set(self.value_uri),
            "time": any_set(self.value_time),
            "instant": any_set(self.value_instant),
            "markdown": any_set(self.value_markdown),
            "canonical": any_set(self.value_canonical),
            "url": any_set(self.value_url),
            "positiveInt": any_set(self.value_positive_int),
            "unsignedInt": any_set(self.value_unsigned_int),
            "base64Binary": any_set(self.value_base64_binary),
            "id": any_set(self.value_id),
            "Reference": any_set(self.value_reference),
            "Coding": any_set(self.value_coding_system, self.value_coding_code, self.value_coding_display),
            "CodeableConcept": any_set(
                self.value_codeable_concept_system, self.value_codeable_concept_code,
                self.value_codeable_concept_display, self.value_codeable_concept_text),
            "Quantity": any_set(self.value_quantity_value, self.value_quantity_unit,
                                self.value_quantity_system, self.value_quantity_code),
            "Period": any_set(self.value_period_start, self.value_period_end),
            "Range": any_set(self.value_range_low_value, self.value_range_low_unit,
                             self.value_range_high_value, self.value_range_high_unit),
            "Attachment": any_set(
                self.value_attachment_content_type, self.value_attachment_language, self.value_attachment_data,
                self.value_attachment_url, self.value_attachment_size, self.value_attachment_hash,
                self.value_attachment_title, self.value_attachment_creation),
            "Identifier": any_set(self.value_identifier_use, self.value_identifier_system, self.value_identifier_value),
            "Money": any_set(self.value_money_value, self.value_money_currency),
            "Ratio": any_set(self.value_ratio_numerator_value, self.value_ratio_numerator_unit,
                             self.value_ratio_denominator_value, self.value_ratio_denominator_unit),
        }
        used = [name for name, present in groups.items() if present]
        if len(used) != 1:
            raise ValueError(f"value[x] requires exactly one variant; got {used or 'none'}.")
        return self


class TaskInputItemInput(_TaskValueItemInput):
    """Task.input — a labelled input value for the task."""


class TaskOutputItemInput(_TaskValueItemInput):
    """Task.output — a labelled output value produced by the task."""


def _utc(d: datetime) -> datetime:
    """Treat naive datetimes as UTC so naive and aware values compare safely."""
    return d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d


class TaskCreateSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "user_id": "u-test",
                    "org_id": "org-test",
                    "status": "requested",
                    "intent": "order",
                    "priority": "routine",
                    "code_system": "http://snomed.info/sct",
                    "code_code": "3457005",
                    "code_display": "Patient referral",
                    "description": "Refer patient to specialist",
                    "focus": "ServiceRequest/80001",
                    "for": "Patient/10001",
                    "authored_on": "2024-01-15T10:30:00Z",
                    "requester": "Practitioner/30001",
                    "owner": "Practitioner/30002",
                }
            ]
        },
    )

    user_id: str
    org_id: str
    created_by: Optional[str] = None

    # required
    status: TaskStatus = Field(..., description="draft | requested | received | accepted | rejected | ready | cancelled | in-progress | on-hold | failed | completed | entered-in-error")
    intent: TaskIntent = Field(..., description="unknown | proposal | plan | order | original-order | reflex-order | filler-order | instance-order | option")

    # optional scalar
    priority: Optional[TaskPriority] = Field(None, description="routine | urgent | asap | stat")
    description: Optional[str] = None
    instantiates_canonical: Optional[str] = None
    instantiates_uri: Optional[str] = None
    authored_on: Optional[datetime] = None
    last_modified: Optional[datetime] = None

    # groupIdentifier (0..1 Identifier — flat)
    group_identifier_use: Optional[str] = None
    group_identifier_system: Optional[str] = None
    group_identifier_value: Optional[str] = None
    group_identifier_type_system: Optional[str] = None
    group_identifier_type_code: Optional[str] = None
    group_identifier_type_display: Optional[str] = None
    group_identifier_type_text: Optional[str] = None

    # statusReason (0..1 CodeableConcept)
    status_reason_system: Optional[str] = None
    status_reason_code: Optional[str] = None
    status_reason_display: Optional[str] = None
    status_reason_text: Optional[str] = None

    # businessStatus (0..1 CodeableConcept)
    business_status_system: Optional[str] = None
    business_status_code: Optional[str] = None
    business_status_display: Optional[str] = None
    business_status_text: Optional[str] = None

    # code (0..1 CodeableConcept)
    code_system: Optional[str] = None
    code_code: Optional[str] = None
    code_display: Optional[str] = None
    code_text: Optional[str] = None

    # focus (0..1 Reference(Any) open)
    focus: Optional[str] = Field(None, description="Open reference to resource being actioned, e.g. 'ServiceRequest/80001'.")
    focus_display: Optional[str] = None

    # for (0..1 Reference(Any) open)
    for_reference: Optional[str] = Field(
        None,
        alias="for",
        description="Open reference to entity benefiting from task, e.g. 'Patient/10001'.",
    )
    for_display: Optional[str] = None

    # encounter (0..1 Reference(Encounter))
    encounter: Optional[str] = Field(None, description="FHIR reference, e.g. 'Encounter/20001'.")
    encounter_display: Optional[str] = None

    # executionPeriod (0..1 Period)
    execution_period_start: Optional[datetime] = None
    execution_period_end: Optional[datetime] = None

    # requester (0..1 Reference — closed)
    requester: Optional[str] = Field(
        None,
        description="Reference to requester. Allowed: Device/<id>, Organization/<id>, Patient/<id>, Practitioner/<id>, PractitionerRole/<id>, RelatedPerson/<id>.",
    )
    requester_display: Optional[str] = None

    # owner (0..1 Reference — closed)
    owner: Optional[str] = Field(
        None,
        description="Reference to owner. Allowed: Practitioner/<id>, PractitionerRole/<id>, Organization/<id>, CareTeam/<id>, HealthcareService/<id>, Patient/<id>, Device/<id>, RelatedPerson/<id>.",
    )
    owner_display: Optional[str] = None

    # location (0..1 Reference(Location))
    location: Optional[str] = Field(None, description="FHIR reference, e.g. 'Location/230001'.")
    location_display: Optional[str] = None

    # reasonCode (0..1 CodeableConcept)
    reason_code_system: Optional[str] = None
    reason_code_code: Optional[str] = None
    reason_code_display: Optional[str] = None
    reason_code_text: Optional[str] = None

    # reasonReference (0..1 Reference(Any) open)
    reason_reference: Optional[str] = Field(None, description="Open reference to reason resource.")
    reason_reference_display: Optional[str] = None

    # restriction (0..1 BackboneElement — scalar parts flat)
    restriction_repetitions: Optional[int] = None
    restriction_period_start: Optional[datetime] = None
    restriction_period_end: Optional[datetime] = None

    # child arrays
    identifiers: Optional[List[TaskIdentifierInput]] = None
    based_on: Optional[List[TaskBasedOnInput]] = None
    part_of: Optional[List[TaskPartOfInput]] = None
    performer_types: Optional[List[TaskPerformerTypeInput]] = None
    insurance: Optional[List[TaskInsuranceInput]] = None
    notes: Optional[List[TaskNoteInput]] = None
    relevant_history: Optional[List[TaskRelevantHistoryInput]] = None
    restriction_recipients: Optional[List[TaskRestrictionRecipientInput]] = None
    inputs: Optional[List[TaskInputItemInput]] = None
    outputs: Optional[List[TaskOutputItemInput]] = None

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    @model_validator(mode="after")
    def _last_modified_not_before_authored(self):
        """tsk-1: lastModified must be on or after authoredOn."""
        if self.authored_on and self.last_modified and _utc(self.last_modified) < _utc(self.authored_on):
            raise ValueError("last_modified must be on or after authored_on.")
        return self


class TaskPatchSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    status: Optional[TaskStatus] = Field(None, description="Cannot be null.")
    intent: Optional[TaskIntent] = Field(None, description="Cannot be null.")
    priority: Optional[TaskPriority] = None
    description: Optional[str] = None
    instantiates_canonical: Optional[str] = None
    instantiates_uri: Optional[str] = None
    authored_on: Optional[datetime] = None
    last_modified: Optional[datetime] = None

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

    focus: Optional[str] = None
    focus_display: Optional[str] = None

    for_reference: Optional[str] = Field(None, alias="for")
    for_display: Optional[str] = None

    encounter: Optional[str] = None
    encounter_display: Optional[str] = None

    execution_period_start: Optional[datetime] = None
    execution_period_end: Optional[datetime] = None

    requester: Optional[str] = None
    requester_display: Optional[str] = None

    owner: Optional[str] = None
    owner_display: Optional[str] = None

    location: Optional[str] = None
    location_display: Optional[str] = None

    reason_code_system: Optional[str] = None
    reason_code_code: Optional[str] = None
    reason_code_display: Optional[str] = None
    reason_code_text: Optional[str] = None

    reason_reference: Optional[str] = None
    reason_reference_display: Optional[str] = None

    restriction_repetitions: Optional[int] = None
    restriction_period_start: Optional[datetime] = None
    restriction_period_end: Optional[datetime] = None

    identifiers: Optional[List[TaskIdentifierInput]] = None
    based_on: Optional[List[TaskBasedOnInput]] = None
    part_of: Optional[List[TaskPartOfInput]] = None
    performer_types: Optional[List[TaskPerformerTypeInput]] = None
    insurance: Optional[List[TaskInsuranceInput]] = None
    notes: Optional[List[TaskNoteInput]] = None
    relevant_history: Optional[List[TaskRelevantHistoryInput]] = None
    restriction_recipients: Optional[List[TaskRestrictionRecipientInput]] = None
    inputs: Optional[List[TaskInputItemInput]] = None
    outputs: Optional[List[TaskOutputItemInput]] = None
    updated_by: Optional[str] = None

    # NOTE: the child lists above (identifiers, based_on, part_of, performer_types, insurance, notes,
    # relevant_history, restriction_recipients, inputs, outputs) use REPLACE semantics — a list that is
    # sent replaces the stored one in full, [] (or null) clears it, an omitted list is left untouched.
    # References (focus, for, encounter, requester, owner, location, reason_reference) are 'Type/id'
    # strings; send null to clear one.

    @field_validator("status", "intent")
    @classmethod
    def _not_null(cls, v):
        if v is None:
            raise ValueError("must not be null")
        return v
