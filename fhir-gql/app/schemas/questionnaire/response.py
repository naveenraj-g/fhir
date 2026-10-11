"""
Response schemas for Questionnaire resources (fhir-gql gateway).

Plain classes mirror the fhir-server PlainQuestionnaire* shapes (snake_case,
`application/json`); Fhir* classes document the `application/fhir+json` shape
for Swagger only. `extra="allow"` keeps new fhir-server fields flowing through.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field



# ── FHIR (camelCase) response schemas ─────────────────────────────────────────
# Item answer/value choice elements (answerX / valueX) vary per type, so each
# item is documented as an object; the nested `item` array recurses.


class FhirQuestionnaireItem(BaseModel):
    """FHIR R4 Questionnaire.item — one question/group/display; nested items recurse via `item`."""

    model_config = ConfigDict(extra="allow")

    linkId: str
    definition: Optional[str] = None
    code: Optional[List[Dict[str, Any]]] = None
    prefix: Optional[str] = None
    text: Optional[str] = None
    type: str
    enableWhen: Optional[List[Dict[str, Any]]] = None
    enableBehavior: Optional[str] = None
    required: Optional[bool] = None
    repeats: Optional[bool] = None
    readOnly: Optional[bool] = None
    maxLength: Optional[int] = None
    answerValueSet: Optional[str] = None
    answerOption: Optional[List[Dict[str, Any]]] = None
    initial: Optional[List[Dict[str, Any]]] = None
    item: Optional[List[Dict[str, Any]]] = Field(None, description="Nested items (same shape, recursive).")


class FhirQuestionnaireResponse(BaseModel):
    """FHIR R4 Questionnaire — shape returned for Accept: application/fhir+json (Swagger docs only)."""

    resourceType: str = Field("Questionnaire", description="Always 'Questionnaire'.")
    id: str = Field(..., description="Public questionnaire_id as a string.")
    url: Optional[str] = None
    identifier: Optional[List[Dict[str, Any]]] = None
    version: Optional[str] = None
    name: Optional[str] = None
    title: Optional[str] = None
    derivedFrom: Optional[List[str]] = None
    status: str
    experimental: Optional[bool] = None
    subjectType: Optional[List[str]] = None
    date: Optional[str] = None
    publisher: Optional[str] = None
    contact: Optional[List[Dict[str, Any]]] = None
    description: Optional[str] = None
    useContext: Optional[List[Dict[str, Any]]] = None
    jurisdiction: Optional[List[Dict[str, Any]]] = None
    purpose: Optional[str] = None
    copyright: Optional[str] = None
    approvalDate: Optional[str] = None
    lastReviewDate: Optional[str] = None
    effectivePeriod: Optional[Dict[str, Any]] = None
    code: Optional[List[Dict[str, Any]]] = None
    item: Optional[List[FhirQuestionnaireItem]] = None


class FhirBundleEntry(BaseModel):
    """A single entry in a FHIR Bundle — wraps one Questionnaire resource."""

    resource: FhirQuestionnaireResponse


class FhirBundleResponse(BaseModel):
    """FHIR R4 Bundle (searchset) for the Questionnaire list endpoint."""

    resourceType: str = "Bundle"
    type: str = "searchset"
    total: Optional[int] = None
    entry: Optional[List[FhirBundleEntry]] = None


# ── Plain (snake_case) response schemas ───────────────────────────────────────


class PlainQuestionnaireIdentifier(BaseModel):
    """Identifier child entry (Questionnaire.identifier)."""

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


class PlainQuestionnaireSubjectType(BaseModel):
    """subjectType child entry — a ResourceType code."""

    model_config = ConfigDict(extra="allow")
    id: int
    code: str


class PlainQuestionnaireTelecom(BaseModel):
    """ContactPoint child entry (contact.telecom)."""

    model_config = ConfigDict(extra="allow")
    id: int
    system: Optional[str] = None
    value: Optional[str] = None
    use: Optional[str] = None
    rank: Optional[int] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None


class PlainQuestionnaireContact(BaseModel):
    """ContactDetail child entry (contact) with its telecom list."""

    model_config = ConfigDict(extra="allow")
    id: int
    name: Optional[str] = None
    telecom: Optional[List[PlainQuestionnaireTelecom]] = None


class PlainQuestionnaireUseContext(BaseModel):
    """UsageContext child entry: code + one populated value[x] group."""

    model_config = ConfigDict(extra="allow")
    id: int
    code_system: Optional[str] = None
    code_code: Optional[str] = None
    code_display: Optional[str] = None
    value_cc_system: Optional[str] = None
    value_cc_code: Optional[str] = None
    value_cc_display: Optional[str] = None
    value_cc_text: Optional[str] = None
    value_quantity_value: Optional[float] = None
    value_quantity_unit: Optional[str] = None
    value_quantity_system: Optional[str] = None
    value_quantity_code: Optional[str] = None
    value_range_low_value: Optional[float] = None
    value_range_low_unit: Optional[str] = None
    value_range_high_value: Optional[float] = None
    value_range_high_unit: Optional[str] = None
    value_reference_type: Optional[str] = None
    value_reference_id: Optional[int] = None
    value_reference_display: Optional[str] = None


class PlainQuestionnaireJurisdiction(BaseModel):
    """Jurisdiction CodeableConcept child entry."""

    model_config = ConfigDict(extra="allow")
    id: int
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class PlainQuestionnaireCoding(BaseModel):
    """Coding child entry (Questionnaire.code and item.code)."""

    model_config = ConfigDict(extra="allow")
    id: int
    system: Optional[str] = None
    code: Optional[str] = None
    display: Optional[str] = None


class PlainQuestionnaireEnableWhen(BaseModel):
    """item.enableWhen entry: question, operator and one populated answer[x] group."""

    model_config = ConfigDict(extra="allow")
    id: int
    question: Optional[str] = None
    operator: Optional[str] = None
    answer_boolean: Optional[bool] = None
    answer_decimal: Optional[float] = None
    answer_integer: Optional[int] = None
    answer_date: Optional[str] = None
    answer_datetime: Optional[str] = None
    answer_time: Optional[str] = None
    answer_string: Optional[str] = None
    answer_coding_system: Optional[str] = None
    answer_coding_code: Optional[str] = None
    answer_coding_display: Optional[str] = None
    answer_quantity_value: Optional[float] = None
    answer_quantity_unit: Optional[str] = None
    answer_quantity_system: Optional[str] = None
    answer_quantity_code: Optional[str] = None
    answer_reference_type: Optional[str] = None
    answer_reference_id: Optional[int] = None
    answer_reference_display: Optional[str] = None


class PlainQuestionnaireAnswerOption(BaseModel):
    """item.answerOption entry: one populated value[x] group plus initialSelected."""

    model_config = ConfigDict(extra="allow")
    id: int
    initial_selected: Optional[bool] = None
    value_integer: Optional[int] = None
    value_date: Optional[str] = None
    value_time: Optional[str] = None
    value_string: Optional[str] = None
    value_coding_system: Optional[str] = None
    value_coding_code: Optional[str] = None
    value_coding_display: Optional[str] = None
    value_reference_type: Optional[str] = None
    value_reference_id: Optional[int] = None
    value_reference_display: Optional[str] = None


class PlainQuestionnaireInitial(BaseModel):
    """item.initial entry: one populated value[x] group."""

    model_config = ConfigDict(extra="allow")
    id: int
    value_boolean: Optional[bool] = None
    value_decimal: Optional[float] = None
    value_integer: Optional[int] = None
    value_date: Optional[str] = None
    value_datetime: Optional[str] = None
    value_time: Optional[str] = None
    value_string: Optional[str] = None
    value_uri: Optional[str] = None
    value_attachment_content_type: Optional[str] = None
    value_attachment_language: Optional[str] = None
    value_attachment_data: Optional[str] = None
    value_attachment_url: Optional[str] = None
    value_attachment_size: Optional[int] = None
    value_attachment_hash: Optional[str] = None
    value_attachment_title: Optional[str] = None
    value_attachment_creation: Optional[str] = None
    value_coding_system: Optional[str] = None
    value_coding_code: Optional[str] = None
    value_coding_display: Optional[str] = None
    value_quantity_value: Optional[float] = None
    value_quantity_unit: Optional[str] = None
    value_quantity_system: Optional[str] = None
    value_quantity_code: Optional[str] = None
    value_reference_type: Optional[str] = None
    value_reference_id: Optional[int] = None
    value_reference_display: Optional[str] = None


class PlainQuestionnaireItem(BaseModel):
    """One item of the form; nested items are returned (recursively) in `item`."""

    model_config = ConfigDict(extra="allow")
    id: int
    link_id: str
    definition: Optional[str] = None
    code: Optional[List[PlainQuestionnaireCoding]] = None
    prefix: Optional[str] = None
    text: Optional[str] = None
    type: Optional[str] = None
    enable_when: Optional[List[PlainQuestionnaireEnableWhen]] = None
    enable_behavior: Optional[str] = None
    required: Optional[bool] = None
    repeats: Optional[bool] = None
    read_only: Optional[bool] = None
    max_length: Optional[int] = None
    answer_value_set: Optional[str] = None
    answer_option: Optional[List[PlainQuestionnaireAnswerOption]] = None
    initial: Optional[List[PlainQuestionnaireInitial]] = None
    item: Optional[List[Dict[str, Any]]] = Field(None, description="Nested items (same shape, recursive).")


class QuestionnaireDefinitionResponse(BaseModel):
    """Full plain JSON response for a single Questionnaire (the form definition)."""

    model_config = ConfigDict(extra="allow")
    id: int
    url: Optional[str] = None
    version: Optional[str] = None
    name: Optional[str] = None
    title: Optional[str] = None
    status: Optional[str] = None
    experimental: Optional[bool] = None
    date: Optional[str] = None
    publisher: Optional[str] = None
    description: Optional[str] = None
    purpose: Optional[str] = None
    copyright: Optional[str] = None
    approval_date: Optional[str] = None
    last_review_date: Optional[str] = None
    effective_period_start: Optional[str] = None
    effective_period_end: Optional[str] = None
    derived_from: Optional[List[str]] = None
    identifier: Optional[List[PlainQuestionnaireIdentifier]] = None
    subject_type: Optional[List[PlainQuestionnaireSubjectType]] = None
    contact: Optional[List[PlainQuestionnaireContact]] = None
    use_context: Optional[List[PlainQuestionnaireUseContext]] = None
    jurisdiction: Optional[List[PlainQuestionnaireJurisdiction]] = None
    code: Optional[List[PlainQuestionnaireCoding]] = None
    item: Optional[List[PlainQuestionnaireItem]] = None
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None


class PaginatedQuestionnaireResponse(BaseModel):
    """Paginated list wrapper for Questionnaire resources."""

    total: int
    limit: int
    offset: int
    data: List[QuestionnaireDefinitionResponse]
