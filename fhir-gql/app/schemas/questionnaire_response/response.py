"""
Response schemas for QuestionnaireResponse resources (fhir-gql gateway).

Plain* classes mirror the fhir-server snake_case output (`application/json`);
Fhir* classes document the `application/fhir+json` shape for Swagger only.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class FHIRReference(BaseModel):
    """FHIR Reference datatype (reference + display)."""

    reference: Optional[str] = None
    display: Optional[str] = None


# ── FHIR answer sub-types ──────────────────────────────────────────────────────


class FHIRAnswerCoding(BaseModel):
    """FHIRAnswerCoding — see the fhir-server schema of the same name."""

    system: Optional[str] = None
    code: Optional[str] = None
    display: Optional[str] = None


class FHIRAnswerQuantity(BaseModel):
    """FHIRAnswerQuantity — see the fhir-server schema of the same name."""

    value: Optional[float] = None
    unit: Optional[str] = None
    system: Optional[str] = None
    code: Optional[str] = None


class FHIRAnswerValueReference(BaseModel):
    """FHIRAnswerValueReference — see the fhir-server schema of the same name."""

    reference: Optional[str] = None
    display: Optional[str] = None


class FHIRAnswerAttachment(BaseModel):
    """FHIRAnswerAttachment — see the fhir-server schema of the same name."""

    contentType: Optional[str] = None
    language: Optional[str] = None
    data: Optional[str] = None
    url: Optional[str] = None
    size: Optional[int] = None
    hash: Optional[str] = None
    title: Optional[str] = None
    creation: Optional[str] = None


class FHIRAnswer(BaseModel):
    """FHIRAnswer — see the fhir-server schema of the same name."""

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
    valueAttachment: Optional[FHIRAnswerAttachment] = None
    item: Optional[List["FHIRQRItem"]] = None


class FHIRQRItem(BaseModel):
    """FHIRQRItem — see the fhir-server schema of the same name."""

    linkId: str
    text: Optional[str] = None
    definition: Optional[str] = None
    answer: Optional[List[FHIRAnswer]] = None
    item: Optional[List["FHIRQRItem"]] = None


FHIRAnswer.model_rebuild()
FHIRQRItem.model_rebuild()


# ── FHIR QuestionnaireResponse schema ─────────────────────────────────────────


class FhirQuestionnaireResponse(BaseModel):
    """FhirQuestionnaireResponse — see the fhir-server schema of the same name."""

    resourceType: str = Field("QuestionnaireResponse", description="Always 'QuestionnaireResponse'.")
    id: str = Field(..., description="Public questionnaire_response_id as a string.")
    identifier: Optional[Dict[str, Any]] = None
    basedOn: Optional[List[FHIRReference]] = None
    partOf: Optional[List[FHIRReference]] = None
    questionnaire: Optional[str] = Field(None, description="Canonical URL of the answered Questionnaire.")
    status: str = Field(..., description="in-progress | completed | amended | entered-in-error | stopped")
    subject: Optional[FHIRReference] = None
    encounter: Optional[FHIRReference] = None
    authored: Optional[str] = None
    author: Optional[FHIRReference] = None
    source: Optional[FHIRReference] = None
    item: Optional[List[FHIRQRItem]] = None


class FhirBundleEntry(BaseModel):
    """FhirBundleEntry — see the fhir-server schema of the same name."""

    resource: FhirQuestionnaireResponse


class FhirBundleResponse(BaseModel):
    """FHIR R4 Bundle (searchset) for the QuestionnaireResponse list endpoint."""

    resourceType: str = "Bundle"
    type: str = "searchset"
    total: Optional[int] = None
    entry: Optional[List[FhirBundleEntry]] = None


# ── Plain (snake_case) sub-types ──────────────────────────────────────────────


class PlainAnswerCoding(BaseModel):
    """PlainAnswerCoding — see the fhir-server schema of the same name."""

    system: Optional[str] = None
    code: Optional[str] = None
    display: Optional[str] = None


class PlainAnswerQuantity(BaseModel):
    """PlainAnswerQuantity — see the fhir-server schema of the same name."""

    value: Optional[float] = None
    unit: Optional[str] = None
    system: Optional[str] = None
    code: Optional[str] = None


class PlainAnswerAttachment(BaseModel):
    """PlainAnswerAttachment — see the fhir-server schema of the same name."""

    content_type: Optional[str] = None
    language: Optional[str] = None
    data: Optional[str] = None
    url: Optional[str] = None
    size: Optional[int] = None
    hash: Optional[str] = None
    title: Optional[str] = None
    creation: Optional[str] = None


class PlainQRAnswer(BaseModel):
    """PlainQRAnswer — see the fhir-server schema of the same name."""

    value_type: Optional[str] = Field(
        None,
        description="boolean | decimal | integer | date | dateTime | time | string | uri | coding | quantity | reference | attachment",
    )
    value_boolean: Optional[bool] = None
    value_decimal: Optional[float] = None
    value_integer: Optional[int] = None
    value_date: Optional[str] = Field(None, description="Date answer, YYYY-MM-DD.")
    value_datetime: Optional[str] = Field(None, description="ISO 8601 datetime string.")
    value_time: Optional[str] = Field(None, description="Time answer, HH:MM:SS.")
    value_string: Optional[str] = None
    value_uri: Optional[str] = None
    value_coding: Optional[PlainAnswerCoding] = None
    value_quantity: Optional[PlainAnswerQuantity] = None
    value_reference: Optional[str] = None
    value_reference_display: Optional[str] = None
    value_attachment: Optional[PlainAnswerAttachment] = None
    item: Optional[List["PlainQRItem"]] = None


class PlainQRItem(BaseModel):
    """PlainQRItem — see the fhir-server schema of the same name."""

    link_id: str
    text: Optional[str] = None
    definition: Optional[str] = None
    answer: Optional[List[PlainQRAnswer]] = None
    item: Optional[List["PlainQRItem"]] = None


PlainQRAnswer.model_rebuild()
PlainQRItem.model_rebuild()


class PlainQRBasedOn(BaseModel):
    """PlainQRBasedOn — see the fhir-server schema of the same name."""

    reference_type: Optional[str] = Field(None, description="CarePlan | ServiceRequest")
    reference_id: Optional[int] = None
    reference_display: Optional[str] = None


class PlainQRPartOf(BaseModel):
    """PlainQRPartOf — see the fhir-server schema of the same name."""

    reference_type: Optional[str] = Field(None, description="Observation | Procedure")
    reference_id: Optional[int] = None
    reference_display: Optional[str] = None


# ── Plain QuestionnaireResponse response ──────────────────────────────────────


class QuestionnaireResponseRecord(BaseModel):
    """QuestionnaireResponseRecord — see the fhir-server schema of the same name."""

    id: int = Field(..., description="Public questionnaire_response_id.")
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    questionnaire: Optional[str] = Field(None, description="Canonical URL of the answered Questionnaire.")
    status: Optional[str] = Field(None, description="in-progress | completed | amended | entered-in-error | stopped")

    # identifier (0..1 in R4)
    identifier_use: Optional[str] = Field(None, description="usual | official | temp | secondary | old")
    identifier_type_system: Optional[str] = None
    identifier_type_code: Optional[str] = None
    identifier_type_display: Optional[str] = None
    identifier_type_text: Optional[str] = None
    identifier_system: Optional[str] = None
    identifier_value: Optional[str] = None
    identifier_period_start: Optional[str] = None
    identifier_period_end: Optional[str] = None
    identifier_assigner: Optional[str] = None

    # basedOn / partOf
    based_on: Optional[List[PlainQRBasedOn]] = None
    part_of: Optional[List[PlainQRPartOf]] = None

    subject_type: Optional[str] = Field(None, description="Any resource type, e.g. 'Patient'")
    subject_id: Optional[int] = None
    subject_display: Optional[str] = None
    encounter_type: Optional[str] = Field(None, description="Always 'Encounter' when set.")
    encounter_id: Optional[int] = Field(None, description="Public encounter_id of the linked Encounter.")
    encounter_display: Optional[str] = None
    authored: Optional[str] = Field(None, description="ISO 8601 datetime string.")
    author_type: Optional[str] = Field(None, description="e.g. 'Practitioner' | 'Patient'")
    author_id: Optional[int] = None
    author_display: Optional[str] = None
    source_type: Optional[str] = Field(None, description="e.g. 'Patient' | 'Practitioner'")
    source_id: Optional[int] = None
    source_display: Optional[str] = None
    item: Optional[List[PlainQRItem]] = None

    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None


# ── Paginated response ────────────────────────────────────────────────────────


class PaginatedQuestionnaireResponseResponse(BaseModel):
    """PaginatedQuestionnaireResponseResponse — see the fhir-server schema of the same name."""

    total: int = Field(..., description="Total number of matching questionnaire responses.")
    limit: int = Field(..., description="Page size requested.")
    offset: int = Field(..., description="Number of records skipped.")
    data: List[QuestionnaireResponseRecord] = Field(
        ..., description="Array of plain-JSON QuestionnaireResponse objects."
    )
