from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Sequence,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import FHIRBase as Base
from app.models.diagnostic_report.enums import (
    DiagnosticReportParticipantType,
    DiagnosticReportStatus,
    DiagnosticReportSubjectType,
)

diagnostic_report_id_seq = Sequence("diagnostic_report_id_seq", start=110000, increment=1)


class DiagnosticReportModel(Base):
    __tablename__ = "diagnostic_report"

    # Internal PK — never exposed
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # Public ID — used in all API responses and FHIR output
    diagnostic_report_id = Column(
        Integer,
        diagnostic_report_id_seq,
        server_default=diagnostic_report_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    user_id = Column(String, nullable=True, index=True)
    org_id = Column(String, nullable=True, index=True)

    # ── Required ───────────────────────────────────────────────────────────────

    status = Column(
        Enum(DiagnosticReportStatus, name="dr_status"), nullable=False, index=True
    )

    # code (1..1 CodeableConcept) — what diagnostic was requested/performed
    code_system = Column(String, nullable=True)
    code_code = Column(String, nullable=True, index=True)
    code_display = Column(String, nullable=True)
    code_text = Column(String, nullable=True)

    # ── subject (0..1 Reference — Patient | Group | Device | Location) ────────

    subject_type = Column(
        Enum(DiagnosticReportSubjectType, name="dr_subject_type"), nullable=True
    )
    subject_id = Column(Integer, nullable=True, index=True)
    subject_display = Column(String, nullable=True)

    # ── encounter (0..1 Reference(Encounter)) ─────────────────────────────────

    encounter_id = Column(Integer, ForeignKey("encounter.id"), nullable=True, index=True)

    # ── effective[x] (0..1 — dateTime | Period) ───────────────────────────────

    effective_datetime = Column(DateTime(timezone=True), nullable=True)
    effective_period_start = Column(DateTime(timezone=True), nullable=True)
    effective_period_end = Column(DateTime(timezone=True), nullable=True)

    # ── issued (0..1 instant) — when report was released ─────────────────────

    issued = Column(DateTime(timezone=True), nullable=True, index=True)

    # ── conclusion (0..1 string) — narrative summary ──────────────────────────

    conclusion = Column(Text, nullable=True)

    # ── Audit ─────────────────────────────────────────────────────────────────

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────

    encounter = relationship("EncounterModel", foreign_keys=[encounter_id])

    identifiers = relationship(
        "DiagnosticReportIdentifier",
        back_populates="diagnostic_report",
        cascade="all, delete-orphan",
    )
    based_on = relationship(
        "DiagnosticReportBasedOn",
        back_populates="diagnostic_report",
        cascade="all, delete-orphan",
    )
    categories = relationship(
        "DiagnosticReportCategory",
        back_populates="diagnostic_report",
        cascade="all, delete-orphan",
    )
    performers = relationship(
        "DiagnosticReportPerformer",
        back_populates="diagnostic_report",
        cascade="all, delete-orphan",
    )
    results_interpreters = relationship(
        "DiagnosticReportResultsInterpreter",
        back_populates="diagnostic_report",
        cascade="all, delete-orphan",
    )
    specimens = relationship(
        "DiagnosticReportSpecimen",
        back_populates="diagnostic_report",
        cascade="all, delete-orphan",
    )
    results = relationship(
        "DiagnosticReportResult",
        back_populates="diagnostic_report",
        cascade="all, delete-orphan",
    )
    imaging_studies = relationship(
        "DiagnosticReportImagingStudy",
        back_populates="diagnostic_report",
        cascade="all, delete-orphan",
    )
    media = relationship(
        "DiagnosticReportMedia",
        back_populates="diagnostic_report",
        cascade="all, delete-orphan",
    )
    conclusion_codes = relationship(
        "DiagnosticReportConclusionCode",
        back_populates="diagnostic_report",
        cascade="all, delete-orphan",
    )
    presented_forms = relationship(
        "DiagnosticReportPresentedForm",
        back_populates="diagnostic_report",
        cascade="all, delete-orphan",
    )


# ── Sub-resource tables ────────────────────────────────────────────────────────


class DiagnosticReportIdentifier(Base):
    """identifier[] — business identifiers for this report."""

    __tablename__ = "diagnostic_report_identifier"

    id = Column(Integer, primary_key=True, autoincrement=True)
    diagnostic_report_id = Column(
        Integer, ForeignKey("diagnostic_report.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    # Full Identifier spec: use | type | system | value | period | assigner
    use = Column(String, nullable=True)        # usual | official | temp | secondary | old
    type_system = Column(String, nullable=True)
    type_code = Column(String, nullable=True)
    type_display = Column(String, nullable=True)
    system = Column(String, nullable=True)
    value = Column(String, nullable=False)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)
    assigner = Column(String, nullable=True)

    diagnostic_report = relationship("DiagnosticReportModel", back_populates="identifiers")


class DiagnosticReportBasedOn(Base):
    """basedOn[] — Reference(CarePlan|ImmunizationRecommendation|MedicationRequest|NutritionOrder|ServiceRequest)."""

    __tablename__ = "diagnostic_report_based_on"

    id = Column(Integer, primary_key=True, autoincrement=True)
    diagnostic_report_id = Column(
        Integer, ForeignKey("diagnostic_report.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    # Allowed: CarePlan | ImmunizationRecommendation | MedicationRequest | NutritionOrder | ServiceRequest
    reference_type = Column(String, nullable=True)
    reference_id = Column(Integer, nullable=True)
    reference_display = Column(String, nullable=True)

    diagnostic_report = relationship("DiagnosticReportModel", back_populates="based_on")


class DiagnosticReportCategory(Base):
    """category[] — CodeableConcept classifying the diagnostic discipline (0..* in R4)."""

    __tablename__ = "diagnostic_report_category"

    id = Column(Integer, primary_key=True, autoincrement=True)
    diagnostic_report_id = Column(
        Integer, ForeignKey("diagnostic_report.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    coding_system = Column(String, nullable=True)
    coding_code = Column(String, nullable=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)

    diagnostic_report = relationship("DiagnosticReportModel", back_populates="categories")


class DiagnosticReportPerformer(Base):
    """performer[] — plain Reference (not BackboneElement in R4) to responsible diagnostic service."""

    __tablename__ = "diagnostic_report_performer"

    id = Column(Integer, primary_key=True, autoincrement=True)
    diagnostic_report_id = Column(
        Integer, ForeignKey("diagnostic_report.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    # Allowed: Practitioner | PractitionerRole | Organization | CareTeam
    reference_type = Column(
        Enum(DiagnosticReportParticipantType, name="dr_performer_type"), nullable=True
    )
    reference_id = Column(Integer, nullable=True)
    reference_display = Column(String, nullable=True)

    diagnostic_report = relationship("DiagnosticReportModel", back_populates="performers")


class DiagnosticReportResultsInterpreter(Base):
    """resultsInterpreter[] — who is responsible for the report's conclusions."""

    __tablename__ = "diagnostic_report_results_interpreter"

    id = Column(Integer, primary_key=True, autoincrement=True)
    diagnostic_report_id = Column(
        Integer, ForeignKey("diagnostic_report.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    # Allowed: Practitioner | PractitionerRole | Organization | CareTeam
    reference_type = Column(
        Enum(DiagnosticReportParticipantType, name="dr_interpreter_type"), nullable=True
    )
    reference_id = Column(Integer, nullable=True)
    reference_display = Column(String, nullable=True)

    diagnostic_report = relationship(
        "DiagnosticReportModel", back_populates="results_interpreters"
    )


class DiagnosticReportSpecimen(Base):
    """specimen[] — Reference(Specimen) this report is based on."""

    __tablename__ = "diagnostic_report_specimen"

    id = Column(Integer, primary_key=True, autoincrement=True)
    diagnostic_report_id = Column(
        Integer, ForeignKey("diagnostic_report.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    # Specimen is not a tracked resource; stored as type+id for forward-compat.
    reference_type = Column(String, nullable=True, default="Specimen")
    reference_id = Column(Integer, nullable=True)
    reference_display = Column(String, nullable=True)

    diagnostic_report = relationship("DiagnosticReportModel", back_populates="specimens")


class DiagnosticReportResult(Base):
    """result[] — Reference(Observation) observations that are part of this report."""

    __tablename__ = "diagnostic_report_result"

    id = Column(Integer, primary_key=True, autoincrement=True)
    diagnostic_report_id = Column(
        Integer, ForeignKey("diagnostic_report.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    # Observation is not a tracked resource; stored as type+id for forward-compat.
    reference_type = Column(String, nullable=True, default="Observation")
    reference_id = Column(Integer, nullable=True)
    reference_display = Column(String, nullable=True)

    diagnostic_report = relationship("DiagnosticReportModel", back_populates="results")


class DiagnosticReportImagingStudy(Base):
    """imagingStudy[] — Reference(ImagingStudy) — R4 field name, not 'study' (R5)."""

    __tablename__ = "diagnostic_report_imaging_study"

    id = Column(Integer, primary_key=True, autoincrement=True)
    diagnostic_report_id = Column(
        Integer, ForeignKey("diagnostic_report.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    # ImagingStudy is not a tracked resource; stored as type+id for forward-compat.
    reference_type = Column(String, nullable=True, default="ImagingStudy")
    reference_id = Column(Integer, nullable=True)
    reference_display = Column(String, nullable=True)

    diagnostic_report = relationship("DiagnosticReportModel", back_populates="imaging_studies")


class DiagnosticReportMedia(Base):
    """media[] BackboneElement — key images associated with this report.

    BackboneElement fields (per spec):
      - comment  (0..1 string)       — comment about the image
      - link     (1..1 Reference(Media)) — reference to the image source (required)
    """

    __tablename__ = "diagnostic_report_media"

    id = Column(Integer, primary_key=True, autoincrement=True)
    diagnostic_report_id = Column(
        Integer, ForeignKey("diagnostic_report.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    # comment (0..1 string)
    comment = Column(String, nullable=True)

    # link (1..1 Reference(Media)) — Media is not tracked; stored as type+id.
    link_reference_type = Column(String, nullable=True, default="Media")
    link_reference_id = Column(Integer, nullable=True)
    link_display = Column(String, nullable=True)

    diagnostic_report = relationship("DiagnosticReportModel", back_populates="media")


class DiagnosticReportConclusionCode(Base):
    """conclusionCode[] — CodeableConcept codes representing the summary conclusion."""

    __tablename__ = "diagnostic_report_conclusion_code"

    id = Column(Integer, primary_key=True, autoincrement=True)
    diagnostic_report_id = Column(
        Integer, ForeignKey("diagnostic_report.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    coding_system = Column(String, nullable=True)
    coding_code = Column(String, nullable=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)

    diagnostic_report = relationship(
        "DiagnosticReportModel", back_populates="conclusion_codes"
    )


class DiagnosticReportPresentedForm(Base):
    """presentedForm[] — Attachment with the full report content.

    Attachment datatype fields (per spec):
      - contentType  (0..1 code)          MIME type
      - language     (0..1 code)          BCP-47 language code
      - data         (0..1 base64Binary)  actual binary content
      - url          (0..1 url)           location where data can be accessed
      - size         (0..1 unsignedInt)   byte count before base64 encoding
      - hash         (0..1 base64Binary)  SHA-1 hash of the data
      - title        (0..1 string)        label to display in place of data
      - creation     (0..1 dateTime)      when attachment was first created
    """

    __tablename__ = "diagnostic_report_presented_form"

    id = Column(Integer, primary_key=True, autoincrement=True)
    diagnostic_report_id = Column(
        Integer, ForeignKey("diagnostic_report.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    content_type = Column(String, nullable=True)   # MIME type e.g. "application/pdf"
    language = Column(String, nullable=True)        # BCP-47 e.g. "en-US"
    data = Column(Text, nullable=True)              # base64-encoded binary content
    url = Column(String, nullable=True)             # external URL to the document
    size = Column(Integer, nullable=True)           # byte size before base64 encoding
    hash = Column(String, nullable=True)            # base64-encoded SHA-1 hash
    title = Column(String, nullable=True)           # human-readable label
    creation = Column(DateTime(timezone=True), nullable=True)

    diagnostic_report = relationship(
        "DiagnosticReportModel", back_populates="presented_forms"
    )
