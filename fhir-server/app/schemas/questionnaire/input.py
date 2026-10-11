"""
Input schemas for the Questionnaire resource (FHIR R4).

https://www.hl7.org/fhir/R4/questionnaire.html

Choice types (answer[x] / value[x]) are flat optional fields, one group per
variant. The sub-schemas enforce "exactly one variant" and the R4 item
invariants (que-1 .. que-13) so bad forms are rejected at the boundary.
"""

from datetime import date as Date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.questionnaire.enums import (
    QuestionnaireEnableBehavior,
    QuestionnaireItemOperator,
    QuestionnaireItemType,
    QuestionnaireStatus,
    QuestionnaireUseContextReferenceType,
)

# Item types that cannot carry answers, so answer-related elements are disallowed.
_NON_QUESTION = {QuestionnaireItemType.group, QuestionnaireItemType.display}
# Types for which maxLength is meaningful (que-10: simple question types).
_MAX_LENGTH_TYPES = {
    QuestionnaireItemType.boolean, QuestionnaireItemType.decimal, QuestionnaireItemType.integer,
    QuestionnaireItemType.date, QuestionnaireItemType.dateTime, QuestionnaireItemType.time,
    QuestionnaireItemType.string, QuestionnaireItemType.text, QuestionnaireItemType.url,
}


# ── Reusable datatype inputs ───────────────────────────────────────────────────


class QuestionnaireIdentifierInput(BaseModel):
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


class QuestionnaireCodingInput(BaseModel):
    """Coding datatype (system | code | display)."""

    model_config = ConfigDict(extra="forbid")

    system: Optional[str] = None
    code: Optional[str] = None
    display: Optional[str] = None


class QuestionnaireCodeableConceptInput(BaseModel):
    """CodeableConcept child entry (one coding + free text)."""

    model_config = ConfigDict(extra="forbid")

    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class QuestionnaireContactTelecomInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    system: Optional[str] = Field(None, description="phone|fax|email|pager|url|sms|other")
    value: Optional[str] = None
    use: Optional[str] = Field(None, description="home|work|temp|old|mobile")
    rank: Optional[int] = Field(None, ge=1)
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class QuestionnaireContactInput(BaseModel):
    """contact[] — ContactDetail."""

    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    telecom: Optional[List[QuestionnaireContactTelecomInput]] = None


class QuestionnaireUseContextInput(BaseModel):
    """useContext[] — UsageContext: code + exactly one value[x]."""

    model_config = ConfigDict(extra="forbid")

    code_system: Optional[str] = None
    code_code: str = Field(..., description="UsageContext.code (e.g. 'gender', 'age', 'focus').")
    code_display: Optional[str] = None

    # value[x] — CodeableConcept
    value_cc_system: Optional[str] = None
    value_cc_code: Optional[str] = None
    value_cc_display: Optional[str] = None
    value_cc_text: Optional[str] = None
    # value[x] — Quantity
    value_quantity_value: Optional[float] = None
    value_quantity_unit: Optional[str] = None
    value_quantity_system: Optional[str] = None
    value_quantity_code: Optional[str] = None
    # value[x] — Range
    value_range_low_value: Optional[float] = None
    value_range_low_unit: Optional[str] = None
    value_range_high_value: Optional[float] = None
    value_range_high_unit: Optional[str] = None
    # value[x] — Reference
    value_reference: Optional[str] = Field(
        None, description="FHIR reference: PlanDefinition|ResearchStudy|InsurancePlan|HealthcareService|Group|Location|Organization."
    )
    value_reference_display: Optional[str] = None

    @model_validator(mode="after")
    def _one_value(self):
        groups = {
            "CodeableConcept": any([self.value_cc_system, self.value_cc_code, self.value_cc_display, self.value_cc_text]),
            "Quantity": any(v is not None for v in (self.value_quantity_value, self.value_quantity_unit,
                                                    self.value_quantity_system, self.value_quantity_code)),
            "Range": any(v is not None for v in (self.value_range_low_value, self.value_range_low_unit,
                                                 self.value_range_high_value, self.value_range_high_unit)),
            "Reference": self.value_reference is not None,
        }
        used = [k for k, v in groups.items() if v]
        if len(used) != 1:
            raise ValueError(f"useContext requires exactly one value[x] variant; got {used or 'none'}.")
        return self


# ── item sub-elements ──────────────────────────────────────────────────────────


class QuestionnaireEnableWhenInput(BaseModel):
    """item.enableWhen[] — question, operator and exactly one answer[x]."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(..., description="linkId of the question whose answer controls this item.")
    operator: QuestionnaireItemOperator = Field(..., description="exists|=|!=|>|<|>=|<=")

    answer_boolean: Optional[bool] = None
    answer_decimal: Optional[float] = None
    answer_integer: Optional[int] = None
    answer_date: Optional[Date] = None
    answer_datetime: Optional[datetime] = None
    answer_time: Optional[str] = Field(None, description="HH:MM:SS")
    answer_string: Optional[str] = None
    answer_coding_system: Optional[str] = None
    answer_coding_code: Optional[str] = None
    answer_coding_display: Optional[str] = None
    answer_quantity_value: Optional[float] = None
    answer_quantity_unit: Optional[str] = None
    answer_quantity_system: Optional[str] = None
    answer_quantity_code: Optional[str] = None
    answer_reference: Optional[str] = Field(None, description="FHIR reference to any resource e.g. 'Patient/10001'.")
    answer_reference_display: Optional[str] = None

    @model_validator(mode="after")
    def _one_answer(self):
        groups = {
            "boolean": self.answer_boolean is not None,
            "decimal": self.answer_decimal is not None,
            "integer": self.answer_integer is not None,
            "date": self.answer_date is not None,
            "dateTime": self.answer_datetime is not None,
            "time": self.answer_time is not None,
            "string": self.answer_string is not None,
            "Coding": any([self.answer_coding_system, self.answer_coding_code, self.answer_coding_display]),
            "Quantity": any(v is not None for v in (self.answer_quantity_value, self.answer_quantity_unit,
                                                    self.answer_quantity_system, self.answer_quantity_code)),
            "Reference": self.answer_reference is not None,
        }
        used = [k for k, v in groups.items() if v]
        if len(used) != 1:
            raise ValueError(f"enableWhen requires exactly one answer[x] variant; got {used or 'none'}.")
        # que-7: operator 'exists' requires a boolean answer.
        if self.operator == QuestionnaireItemOperator.exists and used != ["boolean"]:
            raise ValueError("enableWhen operator 'exists' requires answer_boolean.")
        return self


class QuestionnaireAnswerOptionInput(BaseModel):
    """item.answerOption[] — exactly one value[x] plus initialSelected."""

    model_config = ConfigDict(extra="forbid")

    initial_selected: Optional[bool] = None

    value_integer: Optional[int] = None
    value_date: Optional[Date] = None
    value_time: Optional[str] = Field(None, description="HH:MM:SS")
    value_string: Optional[str] = None
    value_coding_system: Optional[str] = None
    value_coding_code: Optional[str] = None
    value_coding_display: Optional[str] = None
    value_reference: Optional[str] = Field(None, description="FHIR reference to any resource e.g. 'Practitioner/30001'.")
    value_reference_display: Optional[str] = None

    @model_validator(mode="after")
    def _one_value(self):
        groups = {
            "integer": self.value_integer is not None,
            "date": self.value_date is not None,
            "time": self.value_time is not None,
            "string": self.value_string is not None,
            "Coding": any([self.value_coding_system, self.value_coding_code, self.value_coding_display]),
            "Reference": self.value_reference is not None,
        }
        used = [k for k, v in groups.items() if v]
        if len(used) != 1:
            raise ValueError(f"answerOption requires exactly one value[x] variant; got {used or 'none'}.")
        return self


class QuestionnaireInitialInput(BaseModel):
    """item.initial[] — exactly one value[x]."""

    model_config = ConfigDict(extra="forbid")

    value_boolean: Optional[bool] = None
    value_decimal: Optional[float] = None
    value_integer: Optional[int] = None
    value_date: Optional[Date] = None
    value_datetime: Optional[datetime] = None
    value_time: Optional[str] = Field(None, description="HH:MM:SS")
    value_string: Optional[str] = None
    value_uri: Optional[str] = None
    value_attachment_content_type: Optional[str] = None
    value_attachment_language: Optional[str] = None
    value_attachment_data: Optional[str] = Field(None, description="base64Binary content.")
    value_attachment_url: Optional[str] = None
    value_attachment_size: Optional[int] = Field(None, ge=0)
    value_attachment_hash: Optional[str] = None
    value_attachment_title: Optional[str] = None
    value_attachment_creation: Optional[datetime] = None
    value_coding_system: Optional[str] = None
    value_coding_code: Optional[str] = None
    value_coding_display: Optional[str] = None
    value_quantity_value: Optional[float] = None
    value_quantity_unit: Optional[str] = None
    value_quantity_system: Optional[str] = None
    value_quantity_code: Optional[str] = None
    value_reference: Optional[str] = Field(None, description="FHIR reference to any resource e.g. 'Patient/10001'.")
    value_reference_display: Optional[str] = None

    @model_validator(mode="after")
    def _one_value(self):
        attachment = (
            self.value_attachment_content_type, self.value_attachment_language, self.value_attachment_data,
            self.value_attachment_url, self.value_attachment_size, self.value_attachment_hash,
            self.value_attachment_title, self.value_attachment_creation,
        )
        groups = {
            "boolean": self.value_boolean is not None,
            "decimal": self.value_decimal is not None,
            "integer": self.value_integer is not None,
            "date": self.value_date is not None,
            "dateTime": self.value_datetime is not None,
            "time": self.value_time is not None,
            "string": self.value_string is not None,
            "uri": self.value_uri is not None,
            "Attachment": any(v is not None for v in attachment),
            "Coding": any([self.value_coding_system, self.value_coding_code, self.value_coding_display]),
            "Quantity": any(v is not None for v in (self.value_quantity_value, self.value_quantity_unit,
                                                    self.value_quantity_system, self.value_quantity_code)),
            "Reference": self.value_reference is not None,
        }
        used = [k for k, v in groups.items() if v]
        if len(used) != 1:
            raise ValueError(f"initial requires exactly one value[x] variant; got {used or 'none'}.")
        return self


class QuestionnaireItemInput(BaseModel):
    """item[] — a question, group or display element; nests recursively via `item`."""

    model_config = ConfigDict(extra="forbid")

    link_id: str = Field(..., description="Unique id for the item within the Questionnaire.")
    definition: Optional[str] = Field(None, description="ElementDefinition URI this item is derived from.")
    code: Optional[List[QuestionnaireCodingInput]] = Field(None, description="Coding(s) corresponding to this item.")
    prefix: Optional[str] = Field(None, description="E.g. '1(a)'.")
    text: Optional[str] = None
    type: QuestionnaireItemType = Field(
        ..., description="group|display|boolean|decimal|integer|date|dateTime|time|string|text|url|choice|open-choice|attachment|reference|quantity"
    )
    enable_when: Optional[List[QuestionnaireEnableWhenInput]] = None
    enable_behavior: Optional[QuestionnaireEnableBehavior] = Field(None, description="all|any — required when >1 enable_when.")
    required: Optional[bool] = None
    repeats: Optional[bool] = None
    read_only: Optional[bool] = None
    max_length: Optional[int] = Field(None, ge=0)
    answer_value_set: Optional[str] = Field(None, description="canonical(ValueSet) of permitted answers.")
    answer_option: Optional[List[QuestionnaireAnswerOptionInput]] = None
    initial: Optional[List[QuestionnaireInitialInput]] = None
    item: Optional[List["QuestionnaireItemInput"]] = Field(None, description="Nested items.")

    @model_validator(mode="after")
    def _r4_invariants(self):
        """Enforce the R4 Questionnaire.item invariants that depend only on this node."""
        t = self.type
        if t == QuestionnaireItemType.group and not self.item:
            raise ValueError("que-1: group items must have nested items.")
        if t == QuestionnaireItemType.display and self.item:
            raise ValueError("que-2: display items cannot have nested items.")
        if t == QuestionnaireItemType.display and self.code:
            raise ValueError("que-3: display items cannot have a code.")
        if self.answer_option and self.answer_value_set:
            raise ValueError("que-4: a question cannot have both answer_option and answer_value_set.")
        if self.answer_value_set and t not in (QuestionnaireItemType.choice, QuestionnaireItemType.open_choice):
            raise ValueError("que-5: only choice and open-choice items can have answer_value_set.")
        if t == QuestionnaireItemType.display and (self.required is not None or self.repeats is not None):
            raise ValueError("que-6: required and repeats are not permitted on display items.")
        if self.initial and t in _NON_QUESTION:
            raise ValueError("que-8: initial values cannot be specified for groups or display items.")
        if self.read_only is not None and t == QuestionnaireItemType.display:
            raise ValueError("que-9: read_only cannot be specified for display items.")
        if self.max_length is not None and t not in _MAX_LENGTH_TYPES:
            raise ValueError("que-10: max_length applies only to simple question types.")
        if self.answer_option and self.initial:
            raise ValueError("que-11: if answer_option is present, initial must be missing.")
        if self.enable_when and len(self.enable_when) > 1 and self.enable_behavior is None:
            raise ValueError("que-12: enable_behavior is required when there is more than one enable_when.")
        if self.initial and len(self.initial) > 1 and not self.repeats:
            raise ValueError("que-13: multiple initial values are only allowed for repeating items.")
        return self


QuestionnaireItemInput.model_rebuild()


def _check_unique_link_ids(items):
    """Raise if any item link_id repeats anywhere in the (recursive) item tree."""
    seen: set = set()

    def walk(nodes):
        for n in nodes or []:
            if n.link_id in seen:
                raise ValueError(f"Duplicate item link_id '{n.link_id}'.")
            seen.add(n.link_id)
            walk(n.item)

    walk(items)
    return items


# ── Create / Patch ─────────────────────────────────────────────────────────────


class QuestionnaireCreateSchema(BaseModel):
    """Request body for POST /questionnaires. Only `status` is required (R4 1..1)."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "user_id": "user-123",
                "org_id": "org-456",
                "url": "http://example.org/fhir/Questionnaire/phq-2",
                "version": "1.0.0",
                "name": "phq_2",
                "title": "PHQ-2 depression screener",
                "status": "active",
                "subject_type": ["Patient"],
                "publisher": "Example Health",
                "code": [{"system": "http://loinc.org", "code": "55757-9", "display": "PHQ-2"}],
                "item": [
                    {
                        "link_id": "1",
                        "text": "Little interest or pleasure in doing things?",
                        "type": "choice",
                        "required": True,
                        "answer_option": [
                            {"value_coding_system": "http://loinc.org", "value_coding_code": "LA6568-5", "value_coding_display": "Not at all"},
                            {"value_coding_system": "http://loinc.org", "value_coding_code": "LA6569-3", "value_coding_display": "Several days"},
                        ],
                    },
                    {
                        "link_id": "2",
                        "text": "Describe your symptoms",
                        "type": "string",
                        "enable_when": [{"question": "1", "operator": "!=", "answer_coding_code": "LA6568-5"}],
                    },
                ],
            }
        },
    )

    # Tenant scoping — supplied by the caller from the JWT-bound gateway.
    user_id: Optional[str] = Field(None, description="JWT sub of the record owner.")
    org_id: Optional[str] = Field(None, description="Active organization ID from JWT.")
    created_by: Optional[str] = None

    url: Optional[str] = Field(None, description="Canonical identifier (uri) for this questionnaire.")
    version: Optional[str] = None
    name: Optional[str] = Field(None, description="Computer-friendly name.")
    title: Optional[str] = Field(None, description="Human-friendly name.")
    status: QuestionnaireStatus = Field(..., description="draft|active|retired|unknown")
    experimental: Optional[bool] = None
    date: Optional[datetime] = Field(None, description="Date last changed.")
    publisher: Optional[str] = None
    description: Optional[str] = Field(None, description="Natural-language description (markdown).")
    purpose: Optional[str] = Field(None, description="Why this questionnaire is defined (markdown).")
    copyright: Optional[str] = Field(None, description="Use and/or publishing restrictions (markdown).")
    approval_date: Optional[Date] = None
    last_review_date: Optional[Date] = None
    effective_period_start: Optional[datetime] = None
    effective_period_end: Optional[datetime] = None
    derived_from: Optional[List[str]] = Field(None, description="Canonical URLs of Questionnaires this is based on.")

    identifier: Optional[List[QuestionnaireIdentifierInput]] = None
    subject_type: Optional[List[str]] = Field(None, description="ResourceType codes that can be the subject, e.g. ['Patient'].")
    contact: Optional[List[QuestionnaireContactInput]] = None
    use_context: Optional[List[QuestionnaireUseContextInput]] = None
    jurisdiction: Optional[List[QuestionnaireCodeableConceptInput]] = None
    code: Optional[List[QuestionnaireCodingInput]] = Field(None, description="Codes that map the questionnaire as a whole.")
    item: Optional[List[QuestionnaireItemInput]] = None

    @field_validator("item")
    @classmethod
    def _unique_link_ids(cls, items):
        """link_id must be unique across the whole item tree (R4: unique within the Questionnaire)."""
        return _check_unique_link_ids(items)


class QuestionnairePatchSchema(BaseModel):
    """
    Request body for PATCH /questionnaires/{id}. All optional.

    Child lists and the item tree are patchable with REPLACE semantics (see the
    field comments below). `status` cannot be nulled.
    """

    model_config = ConfigDict(extra="forbid")

    url: Optional[str] = None
    version: Optional[str] = None
    name: Optional[str] = None
    title: Optional[str] = None
    status: Optional[QuestionnaireStatus] = Field(None, description="draft|active|retired|unknown (cannot be null).")
    experimental: Optional[bool] = None
    date: Optional[datetime] = None
    publisher: Optional[str] = None
    description: Optional[str] = None
    purpose: Optional[str] = None
    copyright: Optional[str] = None
    approval_date: Optional[Date] = None
    last_review_date: Optional[Date] = None
    effective_period_start: Optional[datetime] = None
    effective_period_end: Optional[datetime] = None
    derived_from: Optional[List[str]] = None
    updated_by: Optional[str] = None

    # Child lists — REPLACE semantics: a list that is sent replaces the stored one in full
    # ([] / null clears it); an omitted list is left untouched. Sending `item` replaces the
    # ENTIRE item tree.
    identifier: Optional[List[QuestionnaireIdentifierInput]] = None
    subject_type: Optional[List[str]] = None
    contact: Optional[List[QuestionnaireContactInput]] = None
    use_context: Optional[List[QuestionnaireUseContextInput]] = None
    jurisdiction: Optional[List[QuestionnaireCodeableConceptInput]] = None
    code: Optional[List[QuestionnaireCodingInput]] = None
    item: Optional[List[QuestionnaireItemInput]] = None

    @field_validator("item")
    @classmethod
    def _unique_link_ids(cls, items):
        return _check_unique_link_ids(items)

    @field_validator("status")
    @classmethod
    def _status_not_null(cls, v):
        if v is None:
            raise ValueError("must not be null")
        return v
