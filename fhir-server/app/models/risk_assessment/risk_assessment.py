from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Sequence,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import FHIRBase as Base
from app.models.enums import EncounterReferenceType
from app.models.risk_assessment.enums import (
    RiskAssessmentConditionReferenceType,
    RiskAssessmentNoteAuthorReferenceType,
    RiskAssessmentPerformerType,
    RiskAssessmentReasonReferenceType,
    RiskAssessmentStatus,
    RiskAssessmentSubjectType,
)

risk_assessment_id_seq = Sequence("risk_assessment_pub_seq", start=380000, increment=1, metadata=Base.metadata)


class RiskAssessmentModel(Base):
    """FHIR R4 RiskAssessment — an assessment of the likely outcome(s) for a patient or group."""

    __tablename__ = "risk_assessment"

    # Internal PK — never exposed
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # Public ID — used in all API responses and FHIR output
    risk_assessment_id = Column(
        Integer,
        risk_assessment_id_seq,
        server_default=risk_assessment_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    user_id = Column(String, nullable=True, index=True)
    org_id = Column(String, nullable=True, index=True)

    # ── status (1..1 code) ────────────────────────────────────────────────────

    status = Column(Enum(RiskAssessmentStatus, name="risk_assessment_status"), nullable=False, index=True)

    # ── method (0..1 CodeableConcept) ─────────────────────────────────────────

    method_system = Column(String, nullable=True)
    method_code = Column(String, nullable=True, index=True)
    method_display = Column(String, nullable=True)
    method_text = Column(String, nullable=True)

    # ── code (0..1 CodeableConcept) ───────────────────────────────────────────

    code_system = Column(String, nullable=True)
    code_code = Column(String, nullable=True, index=True)
    code_display = Column(String, nullable=True)
    code_text = Column(String, nullable=True)

    # ── basedOn (0..1 Reference(Any)) / parent (0..1 Reference(Any)) — open types ──

    based_on_type = Column(String, nullable=True)
    based_on_id = Column(Integer, nullable=True)
    based_on_display = Column(String, nullable=True)

    parent_type = Column(String, nullable=True)
    parent_id = Column(Integer, nullable=True)
    parent_display = Column(String, nullable=True)

    # ── subject (1..1 Reference(Patient | Group)) ─────────────────────────────

    subject_type = Column(Enum(RiskAssessmentSubjectType, name="risk_assessment_subject_type"), nullable=True)
    subject_id = Column(Integer, nullable=True, index=True)
    subject_display = Column(String, nullable=True)

    # ── encounter (0..1 Reference(Encounter)) ─────────────────────────────────

    encounter_type = Column(
        Enum(EncounterReferenceType, name="encounter_reference_type", create_type=False), nullable=True
    )
    encounter_id = Column(Integer, nullable=True, index=True)  # public encounter_id (no FK to other resources)
    encounter_display = Column(String, nullable=True)

    # ── occurrence[x] (0..1 — dateTime | Period) ──────────────────────────────

    occurrence_datetime = Column(DateTime(timezone=True), nullable=True)
    occurrence_period_start = Column(DateTime(timezone=True), nullable=True)
    occurrence_period_end = Column(DateTime(timezone=True), nullable=True)

    # ── condition (0..1 Reference(Condition)) ─────────────────────────────────

    condition_type = Column(
        Enum(RiskAssessmentConditionReferenceType, name="risk_assessment_condition_ref_type"), nullable=True
    )
    condition_id = Column(Integer, nullable=True, index=True)
    condition_display = Column(String, nullable=True)

    # ── performer (0..1 Reference(Practitioner | PractitionerRole | Device)) ──

    performer_type = Column(Enum(RiskAssessmentPerformerType, name="risk_assessment_performer_type"), nullable=True)
    performer_id = Column(Integer, nullable=True, index=True)
    performer_display = Column(String, nullable=True)

    # ── mitigation (0..1 string) ──────────────────────────────────────────────

    mitigation = Column(Text, nullable=True)

    # ── Audit ─────────────────────────────────────────────────────────────────

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────


    identifiers = relationship("RiskAssessmentIdentifier", back_populates="risk_assessment", cascade="all, delete-orphan")
    reason_codes = relationship("RiskAssessmentReasonCode", back_populates="risk_assessment", cascade="all, delete-orphan")
    reason_references = relationship("RiskAssessmentReasonReference", back_populates="risk_assessment", cascade="all, delete-orphan")
    basis = relationship("RiskAssessmentBasis", back_populates="risk_assessment", cascade="all, delete-orphan")
    predictions = relationship(
        "RiskAssessmentPrediction", back_populates="risk_assessment", cascade="all, delete-orphan",
        order_by="RiskAssessmentPrediction.id",
    )
    notes = relationship("RiskAssessmentNote", back_populates="risk_assessment", cascade="all, delete-orphan")


# ── Child tables ───────────────────────────────────────────────────────────────


class RiskAssessmentIdentifier(Base):
    """identifier[] — business identifiers."""

    __tablename__ = "risk_assessment_identifier"

    id = Column(Integer, primary_key=True, autoincrement=True)
    risk_assessment_id = Column(Integer, ForeignKey("risk_assessment.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    use = Column(String, nullable=True)
    type_system = Column(String, nullable=True)
    type_code = Column(String, nullable=True)
    type_display = Column(String, nullable=True)
    type_text = Column(String, nullable=True)
    system = Column(String, nullable=True)
    value = Column(String, nullable=False)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)
    assigner = Column(String, nullable=True)

    risk_assessment = relationship("RiskAssessmentModel", back_populates="identifiers")


class RiskAssessmentReasonCode(Base):
    """reasonCode[] — why the assessment was necessary (CodeableConcept)."""

    __tablename__ = "risk_assessment_reason_code"

    id = Column(Integer, primary_key=True, autoincrement=True)
    risk_assessment_id = Column(Integer, ForeignKey("risk_assessment.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    coding_system = Column(String, nullable=True)
    coding_code = Column(String, nullable=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)

    risk_assessment = relationship("RiskAssessmentModel", back_populates="reason_codes")


class RiskAssessmentReasonReference(Base):
    """reasonReference[] — Reference(Condition | Observation | DiagnosticReport | DocumentReference)."""

    __tablename__ = "risk_assessment_reason_reference"

    id = Column(Integer, primary_key=True, autoincrement=True)
    risk_assessment_id = Column(Integer, ForeignKey("risk_assessment.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    reference_type = Column(
        Enum(RiskAssessmentReasonReferenceType, name="risk_assessment_reason_ref_type"), nullable=True
    )
    reference_id = Column(Integer, nullable=True)
    reference_display = Column(String, nullable=True)

    risk_assessment = relationship("RiskAssessmentModel", back_populates="reason_references")


class RiskAssessmentBasis(Base):
    """basis[] — information used in the assessment, Reference(Any) so the type is a free string."""

    __tablename__ = "risk_assessment_basis"

    id = Column(Integer, primary_key=True, autoincrement=True)
    risk_assessment_id = Column(Integer, ForeignKey("risk_assessment.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    reference_type = Column(String, nullable=True)
    reference_id = Column(Integer, nullable=True)
    reference_display = Column(String, nullable=True)

    risk_assessment = relationship("RiskAssessmentModel", back_populates="basis")


class RiskAssessmentPrediction(Base):
    """prediction[] BackboneElement — an outcome with its likelihood."""

    __tablename__ = "risk_assessment_prediction"

    id = Column(Integer, primary_key=True, autoincrement=True)
    risk_assessment_id = Column(Integer, ForeignKey("risk_assessment.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    # outcome (0..1 CodeableConcept)
    outcome_system = Column(String, nullable=True)
    outcome_code = Column(String, nullable=True)
    outcome_display = Column(String, nullable=True)
    outcome_text = Column(String, nullable=True)

    # probability[x] (0..1 — decimal | Range). Range bounds are percentages (ras-1).
    probability_decimal = Column(Float, nullable=True, index=True)
    probability_range_low_value = Column(Float, nullable=True)
    probability_range_low_unit = Column(String, nullable=True)
    probability_range_low_system = Column(String, nullable=True)
    probability_range_low_code = Column(String, nullable=True)
    probability_range_high_value = Column(Float, nullable=True)
    probability_range_high_unit = Column(String, nullable=True)
    probability_range_high_system = Column(String, nullable=True)
    probability_range_high_code = Column(String, nullable=True)

    # qualitativeRisk (0..1 CodeableConcept — RiskProbability)
    qualitative_risk_system = Column(String, nullable=True)
    qualitative_risk_code = Column(String, nullable=True, index=True)
    qualitative_risk_display = Column(String, nullable=True)
    qualitative_risk_text = Column(String, nullable=True)

    # relativeRisk (0..1 decimal)
    relative_risk = Column(Float, nullable=True)

    # when[x] (0..1 — Period | Range)
    when_period_start = Column(DateTime(timezone=True), nullable=True)
    when_period_end = Column(DateTime(timezone=True), nullable=True)
    when_range_low_value = Column(Float, nullable=True)
    when_range_low_unit = Column(String, nullable=True)
    when_range_low_system = Column(String, nullable=True)
    when_range_low_code = Column(String, nullable=True)
    when_range_high_value = Column(Float, nullable=True)
    when_range_high_unit = Column(String, nullable=True)
    when_range_high_system = Column(String, nullable=True)
    when_range_high_code = Column(String, nullable=True)

    # rationale (0..1 string)
    rationale = Column(Text, nullable=True)

    risk_assessment = relationship("RiskAssessmentModel", back_populates="predictions")


class RiskAssessmentNote(Base):
    """note[] — Annotation comments about the assessment."""

    __tablename__ = "risk_assessment_note"

    id = Column(Integer, primary_key=True, autoincrement=True)
    risk_assessment_id = Column(Integer, ForeignKey("risk_assessment.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    text = Column(Text, nullable=False)
    time = Column(DateTime(timezone=True), nullable=True)
    author_string = Column(String, nullable=True)
    author_reference_type = Column(
        Enum(RiskAssessmentNoteAuthorReferenceType, name="risk_assessment_note_author_ref_type"), nullable=True
    )
    author_reference_id = Column(Integer, nullable=True)
    author_reference_display = Column(String, nullable=True)

    risk_assessment = relationship("RiskAssessmentModel", back_populates="notes")
