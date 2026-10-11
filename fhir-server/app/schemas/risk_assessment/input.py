"""
Input schemas for the RiskAssessment resource (FHIR R4).

https://www.hl7.org/fhir/R4/riskassessment.html

Choice types (occurrence[x], prediction.probability[x], prediction.when[x]) are
flat optional fields, one group per variant; each schema enforces "at most one
variant". References are `Type/id` strings (format validated, existence never).
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.risk_assessment.enums import RiskAssessmentStatus


def _any(*values) -> bool:
    return any(v is not None for v in values)


# ── Child (0..*) inputs ────────────────────────────────────────────────────────


class RiskAssessmentIdentifierInput(BaseModel):
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


class RiskAssessmentCodeableConceptInput(BaseModel):
    """CodeableConcept child entry (one coding + free text); used by reason_code."""

    model_config = ConfigDict(extra="forbid")

    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class RiskAssessmentReasonReferenceInput(BaseModel):
    """reasonReference — Condition | Observation | DiagnosticReport | DocumentReference."""

    model_config = ConfigDict(extra="forbid")

    reference: str = Field(..., description="FHIR reference e.g. 'Condition/120001'.")
    reference_display: Optional[str] = None


class RiskAssessmentBasisInput(BaseModel):
    """basis — information used in the assessment, a Reference(Any)."""

    model_config = ConfigDict(extra="forbid")

    reference: str = Field(..., description="FHIR reference to any resource e.g. 'Observation/160001'.")
    reference_display: Optional[str] = None


class RiskAssessmentNoteInput(BaseModel):
    """note — Annotation comment about the assessment."""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(..., description="Annotation text (markdown).")
    time: Optional[datetime] = None
    author_string: Optional[str] = None
    author_reference: Optional[str] = Field(
        None,
        description="FHIR reference: Practitioner|Patient|RelatedPerson|Organization. Mutually exclusive with author_string.",
    )
    author_reference_display: Optional[str] = None


class RiskAssessmentPredictionInput(BaseModel):
    """prediction — an outcome with its likelihood (probability[x] and when[x] are choice types)."""

    model_config = ConfigDict(extra="forbid")

    # outcome (0..1 CodeableConcept)
    outcome_system: Optional[str] = None
    outcome_code: Optional[str] = None
    outcome_display: Optional[str] = None
    outcome_text: Optional[str] = None

    # probability[x] — decimal | Range (percent)
    probability_decimal: Optional[float] = Field(None, ge=0, description="Probability as a percentage; must be <= 100 (ras-2).")
    probability_range_low_value: Optional[float] = None
    probability_range_low_unit: Optional[str] = None
    probability_range_low_system: Optional[str] = None
    probability_range_low_code: Optional[str] = Field(None, description="UCUM code; must be '%' if given (ras-1).")
    probability_range_high_value: Optional[float] = None
    probability_range_high_unit: Optional[str] = None
    probability_range_high_system: Optional[str] = None
    probability_range_high_code: Optional[str] = Field(None, description="UCUM code; must be '%' if given (ras-1).")

    # qualitativeRisk (0..1 CodeableConcept — RiskProbability)
    qualitative_risk_system: Optional[str] = None
    qualitative_risk_code: Optional[str] = None
    qualitative_risk_display: Optional[str] = None
    qualitative_risk_text: Optional[str] = None

    relative_risk: Optional[float] = Field(None, description="Relative likelihood vs. the general population.")

    # when[x] — Period | Range
    when_period_start: Optional[datetime] = None
    when_period_end: Optional[datetime] = None
    when_range_low_value: Optional[float] = None
    when_range_low_unit: Optional[str] = None
    when_range_low_system: Optional[str] = None
    when_range_low_code: Optional[str] = None
    when_range_high_value: Optional[float] = None
    when_range_high_unit: Optional[str] = None
    when_range_high_system: Optional[str] = None
    when_range_high_code: Optional[str] = None

    rationale: Optional[str] = None

    @model_validator(mode="after")
    def _r4_rules(self):
        range_vals = (
            self.probability_range_low_value, self.probability_range_low_unit, self.probability_range_low_system,
            self.probability_range_low_code, self.probability_range_high_value, self.probability_range_high_unit,
            self.probability_range_high_system, self.probability_range_high_code,
        )
        if self.probability_decimal is not None and _any(*range_vals):
            raise ValueError("probability[x]: supply probability_decimal OR probability_range_*, not both.")
        # ras-2: a decimal probability must be <= 100.
        if self.probability_decimal is not None and self.probability_decimal > 100:
            raise ValueError("ras-2: probability_decimal must be <= 100.")
        # ras-1: range bounds are percentages.
        for code in (self.probability_range_low_code, self.probability_range_high_code):
            if code is not None and code != "%":
                raise ValueError("ras-1: probability range bounds must be percentages (UCUM code '%').")
        for v in (self.probability_range_low_value, self.probability_range_high_value):
            if v is not None and not 0 <= v <= 100:
                raise ValueError("ras-1: probability range bounds must be between 0 and 100.")
        period = _any(self.when_period_start, self.when_period_end)
        when_range = _any(
            self.when_range_low_value, self.when_range_low_unit, self.when_range_low_system, self.when_range_low_code,
            self.when_range_high_value, self.when_range_high_unit, self.when_range_high_system, self.when_range_high_code,
        )
        if period and when_range:
            raise ValueError("when[x]: supply when_period_* OR when_range_*, not both.")
        return self


# ── Create / Patch ─────────────────────────────────────────────────────────────


class RiskAssessmentCreateSchema(BaseModel):
    """Request body for POST /risk-assessments. `status` and `subject` are required (R4 1..1)."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "user_id": "user-123",
                "org_id": "org-456",
                "status": "final",
                "code_system": "http://snomed.info/sct",
                "code_code": "225338004",
                "code_display": "Risk assessment",
                "subject": "Patient/10001",
                "encounter_id": 20001,
                "occurrence_datetime": "2024-03-15T10:30:00Z",
                "condition": "Condition/120001",
                "performer": "Practitioner/30001",
                "method_text": "Framingham risk score",
                "prediction": [
                    {
                        "outcome_system": "http://snomed.info/sct",
                        "outcome_code": "53741008",
                        "outcome_display": "Coronary arteriosclerosis",
                        "probability_decimal": 12.5,
                        "qualitative_risk_system": "http://terminology.hl7.org/CodeSystem/risk-probability",
                        "qualitative_risk_code": "moderate",
                        "when_range_low_value": 0,
                        "when_range_high_value": 10,
                        "when_range_high_unit": "years",
                        "rationale": "Age, smoking history and blood pressure.",
                    }
                ],
                "mitigation": "Statin therapy and lifestyle changes.",
                "note": [{"text": "Reassess in 12 months."}],
            }
        },
    )

    user_id: Optional[str] = Field(None, description="JWT sub of the record owner.")
    org_id: Optional[str] = Field(None, description="Active organization ID from JWT.")
    created_by: Optional[str] = None

    status: RiskAssessmentStatus = Field(
        ..., description="registered|preliminary|final|amended|corrected|cancelled|entered-in-error|unknown"
    )

    method_system: Optional[str] = None
    method_code: Optional[str] = None
    method_display: Optional[str] = None
    method_text: Optional[str] = None

    code_system: Optional[str] = None
    code_code: Optional[str] = None
    code_display: Optional[str] = None
    code_text: Optional[str] = None

    based_on: Optional[str] = Field(None, description="Request fulfilled by this assessment — reference to any resource.")
    based_on_display: Optional[str] = None
    parent: Optional[str] = Field(None, description="Part of this occurrence — reference to any resource.")
    parent_display: Optional[str] = None

    subject: str = Field(..., description="FHIR reference e.g. 'Patient/10001' or 'Group/1'.")
    subject_display: Optional[str] = None

    encounter_id: Optional[int] = Field(None, description="Public encounter_id of the linked Encounter.")
    encounter_display: Optional[str] = None

    occurrence_datetime: Optional[datetime] = None
    occurrence_period_start: Optional[datetime] = None
    occurrence_period_end: Optional[datetime] = None

    condition: Optional[str] = Field(None, description="FHIR reference e.g. 'Condition/120001'.")
    condition_display: Optional[str] = None
    performer: Optional[str] = Field(None, description="FHIR reference: Practitioner|PractitionerRole|Device.")
    performer_display: Optional[str] = None

    mitigation: Optional[str] = Field(None, description="How to reduce the risk.")

    identifier: Optional[List[RiskAssessmentIdentifierInput]] = None
    reason_code: Optional[List[RiskAssessmentCodeableConceptInput]] = None
    reason_reference: Optional[List[RiskAssessmentReasonReferenceInput]] = None
    basis: Optional[List[RiskAssessmentBasisInput]] = None
    prediction: Optional[List[RiskAssessmentPredictionInput]] = None
    note: Optional[List[RiskAssessmentNoteInput]] = None

    @model_validator(mode="after")
    def _occurrence_one_variant(self):
        if self.occurrence_datetime is not None and _any(self.occurrence_period_start, self.occurrence_period_end):
            raise ValueError("occurrence[x]: supply occurrence_datetime OR occurrence_period_*, not both.")
        return self


class RiskAssessmentPatchSchema(BaseModel):
    """
    Request body for PATCH /risk-assessments/{id}. All optional.

    Child lists (identifier, reason_code, reason_reference, basis, prediction, note) are patchable with
    REPLACE semantics. References are `Type/id` strings; send null to clear an optional one.
    `status` and `subject` cannot be null.
    """

    model_config = ConfigDict(extra="forbid")

    status: Optional[RiskAssessmentStatus] = Field(None, description="Cannot be null.")
    method_system: Optional[str] = None
    method_code: Optional[str] = None
    method_display: Optional[str] = None
    method_text: Optional[str] = None
    code_system: Optional[str] = None
    code_code: Optional[str] = None
    code_display: Optional[str] = None
    code_text: Optional[str] = None
    based_on: Optional[str] = None
    based_on_display: Optional[str] = None
    parent: Optional[str] = None
    parent_display: Optional[str] = None
    subject: Optional[str] = Field(None, description="Patient|Group reference (cannot be null).")
    subject_display: Optional[str] = None
    encounter_id: Optional[int] = Field(None, description="Public encounter_id; null unlinks.")
    encounter_display: Optional[str] = None
    occurrence_datetime: Optional[datetime] = None
    occurrence_period_start: Optional[datetime] = None
    occurrence_period_end: Optional[datetime] = None
    condition: Optional[str] = None
    condition_display: Optional[str] = None
    performer: Optional[str] = None
    performer_display: Optional[str] = None
    mitigation: Optional[str] = None
    updated_by: Optional[str] = None

    # Child lists — REPLACE semantics: a list that is sent replaces the stored one in full
    # ([] / null clears it); an omitted list is left untouched.
    identifier: Optional[List[RiskAssessmentIdentifierInput]] = None
    reason_code: Optional[List[RiskAssessmentCodeableConceptInput]] = None
    reason_reference: Optional[List[RiskAssessmentReasonReferenceInput]] = None
    basis: Optional[List[RiskAssessmentBasisInput]] = None
    prediction: Optional[List[RiskAssessmentPredictionInput]] = None
    note: Optional[List[RiskAssessmentNoteInput]] = None

    @field_validator("status", "subject")
    @classmethod
    def _not_null(cls, v):
        if v is None:
            raise ValueError("must not be null")
        return v
