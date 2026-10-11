from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Sequence, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import FHIRBase as Base
from app.models.enums import EncounterReferenceType
from app.models.flag.enums import FlagAuthorType, FlagStatus, FlagSubjectType

flag_id_seq = Sequence("flag_pub_seq", start=390000, increment=1, metadata=Base.metadata)


class FlagModel(Base):
    """FHIR R4 Flag — a prospective warning about potential issues when providing care."""

    __tablename__ = "flag"

    # Internal PK — never exposed
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # Public ID — used in all API responses and FHIR output
    flag_id = Column(
        Integer, flag_id_seq, server_default=flag_id_seq.next_value(), unique=True, index=True, nullable=False
    )

    user_id = Column(String, nullable=True, index=True)
    org_id = Column(String, nullable=True, index=True)

    # status (1..1 code)
    status = Column(Enum(FlagStatus, name="flag_status"), nullable=False, index=True)

    # code (1..1 CodeableConcept) — the message shown to the user
    code_system = Column(String, nullable=True)
    code_code = Column(String, nullable=True, index=True)
    code_display = Column(String, nullable=True)
    code_text = Column(String, nullable=True)

    # subject (1..1 Reference — Patient|Location|Group|Organization|Practitioner|PlanDefinition|Medication|Procedure)
    subject_type = Column(Enum(FlagSubjectType, name="flag_subject_type"), nullable=True)
    subject_id = Column(Integer, nullable=True, index=True)
    subject_display = Column(String, nullable=True)

    # period (0..1 Period) — an open end means the flag is still active
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # encounter (0..1 Reference(Encounter))
    encounter_type = Column(
        Enum(EncounterReferenceType, name="encounter_reference_type", create_type=False), nullable=True
    )
    encounter_id = Column(Integer, nullable=True, index=True)  # public encounter_id (no FK to other resources)
    encounter_display = Column(String, nullable=True)

    # author (0..1 Reference — Device|Organization|Patient|Practitioner|PractitionerRole)
    author_type = Column(Enum(FlagAuthorType, name="flag_author_type"), nullable=True)
    author_id = Column(Integer, nullable=True, index=True)
    author_display = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)

    identifiers = relationship("FlagIdentifier", back_populates="flag", cascade="all, delete-orphan")
    categories = relationship("FlagCategory", back_populates="flag", cascade="all, delete-orphan")


class FlagIdentifier(Base):
    """identifier[] — business identifiers."""

    __tablename__ = "flag_identifier"

    id = Column(Integer, primary_key=True, autoincrement=True)
    flag_id = Column(Integer, ForeignKey("flag.id"), nullable=False, index=True)
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

    flag = relationship("FlagModel", back_populates="identifiers")


class FlagCategory(Base):
    """category[] — CodeableConcept classifying the flag (clinical, administrative, ...)."""

    __tablename__ = "flag_category"

    id = Column(Integer, primary_key=True, autoincrement=True)
    flag_id = Column(Integer, ForeignKey("flag.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    coding_system = Column(String, nullable=True)
    coding_code = Column(String, nullable=True, index=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)

    flag = relationship("FlagModel", back_populates="categories")
