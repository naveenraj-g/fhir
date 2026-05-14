from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.fhir.common import FHIRBundle, FHIRReference


class FHIRAnswerCoding(BaseModel):
    system: Optional[str] = None
    code: Optional[str] = None
    display: Optional[str] = None


class FHIRAnswerQuantity(BaseModel):
    value: Optional[float] = None
    unit: Optional[str] = None
    system: Optional[str] = None
    code: Optional[str] = None


class FHIRAnswerValueReference(BaseModel):
    reference: Optional[str] = None
    display: Optional[str] = None


class FHIRAnswer(BaseModel):
    valueBoolean: Optional[bool] = None
    valueDecimal: Optional[float] = None
    valueInteger: Optional[int] = None
    valueDate: Optional[str] = None
    valueDateTime: Optional[str] = None
    valueTime: Optional[str] = None
    valueString: Optional[str] = None
    valueUri: Optional[str] = None
    valueCoding: Optional[FHIRAnswerCoding] = None
    valueQuantity: Optional[FHIRAnswerQuantity] = None
    valueReference: Optional[FHIRAnswerValueReference] = None


class FHIRQRItem(BaseModel):
    linkId: str
    text: Optional[str] = None
    definition: Optional[str] = None
    answer: Optional[List[FHIRAnswer]] = None
    item: Optional[List["FHIRQRItem"]] = None


FHIRQRItem.model_rebuild()


class FHIRQuestionnaireResponseSchema(BaseModel):
    resourceType: str = Field("QuestionnaireResponse", description="Always 'QuestionnaireResponse'.")
    id: str = Field(..., description="Public questionnaire_response_id as a string.")
    questionnaire: str = Field(..., description="Canonical URL of the answered Questionnaire.")
    status: str = Field(..., description="in-progress | completed | amended | entered-in-error | stopped")
    subject: Optional[FHIRReference] = None
    encounter: Optional[FHIRReference] = None
    authored: Optional[str] = None
    author: Optional[FHIRReference] = None
    source: Optional[FHIRReference] = None
    item: Optional[List[FHIRQRItem]] = None


class FHIRQuestionnaireResponseBundleEntry(BaseModel):
    resource: FHIRQuestionnaireResponseSchema


class FHIRQuestionnaireResponseBundle(FHIRBundle):
    entry: Optional[List[FHIRQuestionnaireResponseBundleEntry]] = None


# ── Plain (snake_case) sub-types ──────────────────────────────────────────────


class PlainAnswerCoding(BaseModel):
    system: Optional[str] = None
    code: Optional[str] = None
    display: Optional[str] = None


class PlainAnswerQuantity(BaseModel):
    value: Optional[float] = None
    unit: Optional[str] = None
    system: Optional[str] = None
    code: Optional[str] = None


class PlainQRAnswer(BaseModel):
    value_type: str = Field(..., description="boolean | decimal | integer | date | dateTime | time | string | uri | coding | quantity | reference")
    value_boolean: Optional[bool] = None
    value_decimal: Optional[float] = None
    value_integer: Optional[int] = None
    value_string: Optional[str] = Field(None, description="Used for string, date, time, and uri value types.")
    value_datetime: Optional[str] = Field(None, description="ISO 8601 datetime string (dateTime type).")
    value_coding: Optional[PlainAnswerCoding] = None
    value_quantity: Optional[PlainAnswerQuantity] = None
    value_reference: Optional[str] = None
    value_reference_display: Optional[str] = None


class PlainQRItem(BaseModel):
    link_id: str
    text: Optional[str] = None
    definition: Optional[str] = None
    answer: Optional[List[PlainQRAnswer]] = None
    item: Optional[List["PlainQRItem"]] = None


PlainQRItem.model_rebuild()


# ── Plain QuestionnaireResponse response ──────────────────────────────────────


class PlainQuestionnaireResponse(BaseModel):
    id: int = Field(..., description="Public questionnaire_response_id.")
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    questionnaire: Optional[str] = Field(None, description="Canonical URL of the answered Questionnaire.")
    status: Optional[str] = Field(None, description="in-progress | completed | amended | entered-in-error | stopped")
    subject_type: Optional[str] = Field(None, description="e.g. 'Patient'")
    subject_id: Optional[int] = None
    subject_display: Optional[str] = None
    encounter_id: Optional[int] = Field(None, description="Public encounter_id of the linked Encounter.")
    authored: Optional[str] = Field(None, description="ISO 8601 datetime string.")
    author_type: Optional[str] = Field(None, description="e.g. 'Practitioner' | 'Patient'")
    author_id: Optional[int] = None
    author_display: Optional[str] = None
    source_type: Optional[str] = Field(None, description="e.g. 'Patient' | 'Practitioner'")
    source_id: Optional[int] = None
    source_display: Optional[str] = None
    item: Optional[List[PlainQRItem]] = None


# ── Paginated response ────────────────────────────────────────────────────────


class PaginatedQuestionnaireResponseResponse(BaseModel):
    total: int = Field(..., description="Total number of matching questionnaire responses.")
    limit: int = Field(..., description="Page size requested.")
    offset: int = Field(..., description="Number of records skipped.")
    data: List[PlainQuestionnaireResponse] = Field(..., description="Array of plain-JSON QuestionnaireResponse objects.")
