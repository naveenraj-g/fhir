"""
Response schemas for RiskAssessment resources (fhir-gql gateway).

Plain* classes mirror the fhir-server snake_case output (`application/json`);
Fhir* classes document the `application/fhir+json` shape for Swagger only.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field



class FHIRReference(BaseModel):
    """FHIR Reference datatype (reference + display)."""

    reference: Optional[str] = None
    display: Optional[str] = None


class FHIRCodeableConcept(BaseModel):
    """FHIR CodeableConcept datatype (coding[] + text)."""

    coding: Optional[List[Dict[str, Any]]] = None
    text: Optional[str] = None


# ── FHIR (camelCase) response schemas ─────────────────────────────────────────


class FhirRiskAssessmentPrediction(BaseModel):
    """FhirRiskAssessmentPrediction — see the fhir-server schema of the same name."""

    model_config = ConfigDict(extra="allow")

    outcome: Optional[FHIRCodeableConcept] = None
    probabilityDecimal: Optional[float] = None
    probabilityRange: Optional[Dict[str, Any]] = None
    qualitativeRisk: Optional[FHIRCodeableConcept] = None
    relativeRisk: Optional[float] = None
    whenPeriod: Optional[Dict[str, Any]] = None
    whenRange: Optional[Dict[str, Any]] = None
    rationale: Optional[str] = None


class FhirRiskAssessmentResponse(BaseModel):
    """FhirRiskAssessmentResponse — see the fhir-server schema of the same name."""

    resourceType: str = Field("RiskAssessment", description="Always 'RiskAssessment'.")
    id: str = Field(..., description="Public risk_assessment_id as a string.")
    identifier: Optional[List[Dict[str, Any]]] = None
    basedOn: Optional[FHIRReference] = None
    parent: Optional[FHIRReference] = None
    status: str
    method: Optional[FHIRCodeableConcept] = None
    code: Optional[FHIRCodeableConcept] = None
    subject: Optional[FHIRReference] = None
    encounter: Optional[FHIRReference] = None
    occurrenceDateTime: Optional[str] = None
    occurrencePeriod: Optional[Dict[str, Any]] = None
    condition: Optional[FHIRReference] = None
    performer: Optional[FHIRReference] = None
    reasonCode: Optional[List[FHIRCodeableConcept]] = None
    reasonReference: Optional[List[FHIRReference]] = None
    basis: Optional[List[FHIRReference]] = None
    prediction: Optional[List[FhirRiskAssessmentPrediction]] = None
    mitigation: Optional[str] = None
    note: Optional[List[Dict[str, Any]]] = None


class FhirBundleEntry(BaseModel):
    """FhirBundleEntry — see the fhir-server schema of the same name."""

    resource: FhirRiskAssessmentResponse


class FhirBundleResponse(BaseModel):
    """FHIR R4 Bundle (searchset) for the RiskAssessment list endpoint."""

    resourceType: str = "Bundle"
    type: str = "searchset"
    total: Optional[int] = None
    entry: Optional[List[FhirBundleEntry]] = None


# ── Plain (snake_case) response schemas ───────────────────────────────────────


class PlainRiskAssessmentIdentifier(BaseModel):
    """PlainRiskAssessmentIdentifier — see the fhir-server schema of the same name."""

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


class PlainRiskAssessmentCodeableConcept(BaseModel):
    """PlainRiskAssessmentCodeableConcept — see the fhir-server schema of the same name."""

    model_config = ConfigDict(extra="allow")
    id: int
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class PlainRiskAssessmentReference(BaseModel):
    """Generic reference child entry (reasonReference, basis)."""

    model_config = ConfigDict(extra="allow")
    id: int
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    reference_display: Optional[str] = None


class PlainRiskAssessmentPrediction(BaseModel):
    """PlainRiskAssessmentPrediction — see the fhir-server schema of the same name."""

    model_config = ConfigDict(extra="allow")
    id: int
    outcome_system: Optional[str] = None
    outcome_code: Optional[str] = None
    outcome_display: Optional[str] = None
    outcome_text: Optional[str] = None
    probability_decimal: Optional[float] = None
    probability_range_low_value: Optional[float] = None
    probability_range_low_unit: Optional[str] = None
    probability_range_low_system: Optional[str] = None
    probability_range_low_code: Optional[str] = None
    probability_range_high_value: Optional[float] = None
    probability_range_high_unit: Optional[str] = None
    probability_range_high_system: Optional[str] = None
    probability_range_high_code: Optional[str] = None
    qualitative_risk_system: Optional[str] = None
    qualitative_risk_code: Optional[str] = None
    qualitative_risk_display: Optional[str] = None
    qualitative_risk_text: Optional[str] = None
    relative_risk: Optional[float] = None
    when_period_start: Optional[str] = None
    when_period_end: Optional[str] = None
    when_range_low_value: Optional[float] = None
    when_range_low_unit: Optional[str] = None
    when_range_low_system: Optional[str] = None
    when_range_low_code: Optional[str] = None
    when_range_high_value: Optional[float] = None
    when_range_high_unit: Optional[str] = None
    when_range_high_system: Optional[str] = None
    when_range_high_code: Optional[str] = None
    rationale: Optional[str] = None


class PlainRiskAssessmentNote(BaseModel):
    """PlainRiskAssessmentNote — see the fhir-server schema of the same name."""

    model_config = ConfigDict(extra="allow")
    id: int
    text: Optional[str] = None
    time: Optional[str] = None
    author_string: Optional[str] = None
    author_reference_type: Optional[str] = None
    author_reference_id: Optional[int] = None
    author_reference_display: Optional[str] = None


class RiskAssessmentRecord(BaseModel):
    """RiskAssessmentRecord — see the fhir-server schema of the same name."""

    model_config = ConfigDict(extra="allow")

    id: int
    status: Optional[str] = None
    method_system: Optional[str] = None
    method_code: Optional[str] = None
    method_display: Optional[str] = None
    method_text: Optional[str] = None
    code_system: Optional[str] = None
    code_code: Optional[str] = None
    code_display: Optional[str] = None
    code_text: Optional[str] = None
    based_on_type: Optional[str] = None
    based_on_id: Optional[int] = None
    based_on_display: Optional[str] = None
    parent_type: Optional[str] = None
    parent_id: Optional[int] = None
    parent_display: Optional[str] = None
    subject_type: Optional[str] = None
    subject_id: Optional[int] = None
    subject_display: Optional[str] = None
    encounter_type: Optional[str] = None
    encounter_id: Optional[int] = None
    encounter_display: Optional[str] = None
    occurrence_datetime: Optional[str] = None
    occurrence_period_start: Optional[str] = None
    occurrence_period_end: Optional[str] = None
    condition_type: Optional[str] = None
    condition_id: Optional[int] = None
    condition_display: Optional[str] = None
    performer_type: Optional[str] = None
    performer_id: Optional[int] = None
    performer_display: Optional[str] = None
    mitigation: Optional[str] = None
    identifier: Optional[List[PlainRiskAssessmentIdentifier]] = None
    reason_code: Optional[List[PlainRiskAssessmentCodeableConcept]] = None
    reason_reference: Optional[List[PlainRiskAssessmentReference]] = None
    basis: Optional[List[PlainRiskAssessmentReference]] = None
    prediction: Optional[List[PlainRiskAssessmentPrediction]] = None
    note: Optional[List[PlainRiskAssessmentNote]] = None
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None


class PaginatedRiskAssessmentResponse(BaseModel):
    """PaginatedRiskAssessmentResponse — see the fhir-server schema of the same name."""

    total: int
    limit: int
    offset: int
    data: List[RiskAssessmentRecord]
