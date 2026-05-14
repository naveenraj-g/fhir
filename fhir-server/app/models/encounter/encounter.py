from sqlalchemy import Column, String, DateTime, Integer, Enum, ForeignKey, Sequence
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import FHIRBase as Base
from app.models.encounter.enums import (
    EncounterStatus,
    EncounterClass,
    EncounterParticipantReferenceType,
    EncounterBasedOnReferenceType,
)
from app.models.enums import SubjectReferenceType

encounter_id_seq = Sequence("encounter_id_seq", start=20000, increment=1)


class EncounterModel(Base):
    __tablename__ = "encounter"

    # Internal PK — never exposed
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # Public ID — used in all API responses and FHIR output
    encounter_id = Column(
        Integer,
        encounter_id_seq,
        server_default=encounter_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    user_id = Column(String, nullable=True, index=True)
    org_id = Column(String, nullable=True, index=True)
    status = Column(
        Enum(EncounterStatus), nullable=True
    )  # planned, in-progress, finished, cancelled
    class_code = Column(
        Enum(EncounterClass), nullable=True
    )  # inpatient, outpatient, emergency, etc.
    priority = Column(String, nullable=True)

    # Subject reference — stored as type enum + integer ID
    subject_type = Column(
        Enum(SubjectReferenceType, name="subject_reference_type"),
        nullable=True,
    )
    subject_id = Column(Integer, nullable=True)
    subject_display = Column(String, nullable=True)

    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    based_ons = relationship(
        "BasedOn", back_populates="encounter", cascade="all, delete-orphan"
    )
    types = relationship(
        "EncounterType", back_populates="encounter", cascade="all, delete-orphan"
    )
    participants = relationship(
        "EncounterParticipant", back_populates="encounter", cascade="all, delete-orphan"
    )
    diagnoses = relationship(
        "EncounterDiagnosis", back_populates="encounter", cascade="all, delete-orphan"
    )
    locations = relationship(
        "EncounterLocation", back_populates="encounter", cascade="all, delete-orphan"
    )
    reason_codes = relationship(
        "EncounterReasonCode", back_populates="encounter", cascade="all, delete-orphan"
    )
    appointments = relationship("AppointmentModel", back_populates="encounter")
    questionnaire_responses = relationship(
        "QuestionnaireResponseModel", back_populates="encounter"
    )


class EncounterType(Base):
    __tablename__ = "encounter_type"

    id = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(
        Integer, ForeignKey("encounter.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    coding_system = Column(String, nullable=True)
    coding_code = Column(String, nullable=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)

    encounter = relationship("EncounterModel", back_populates="types")


class BasedOn(Base):
    __tablename__ = "based_on"
    id = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(
        Integer, ForeignKey("encounter.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    reference_type = Column(
        Enum(EncounterBasedOnReferenceType, name="based_on_reference_type"),
        nullable=True,
    )
    reference_id = Column(Integer, nullable=True)
    reference_display = Column(String, nullable=True)

    encounter = relationship("EncounterModel", back_populates="based_ons")


class EncounterParticipant(Base):
    __tablename__ = "encounter_participant"

    id = Column(Integer, primary_key=True, autoincrement=True)

    encounter_id = Column(
        Integer, ForeignKey("encounter.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    type_text = Column(
        String, nullable=True
    )  # e.g., "Primary Physician", "Consulting Physician"

    # Individual reference — stored as type enum + integer ID
    reference_type = Column(
        Enum(EncounterParticipantReferenceType, name="participant_reference_type"),
        nullable=True,
    )
    individual_reference = Column(Integer, nullable=True)

    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    encounter = relationship("EncounterModel", back_populates="participants")


class EncounterDiagnosis(Base):
    __tablename__ = "encounter_diagnosis"

    id = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(
        Integer, ForeignKey("encounter.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    condition_reference = Column(
        String, nullable=True
    )  # Reference to Condition resource
    use_text = Column(
        String, nullable=True
    )  # e.g., "admission", "discharge", "billing"
    rank = Column(String, nullable=True)  # Integer as string for simplicity

    encounter = relationship("EncounterModel", back_populates="diagnoses")


class EncounterLocation(Base):
    __tablename__ = "encounter_location"

    id = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(
        Integer, ForeignKey("encounter.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    location_reference = Column(String, nullable=True)  # Reference to Location
    status = Column(String, nullable=True)  # planned, active, reserved, completed
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    encounter = relationship("EncounterModel", back_populates="locations")


class EncounterReasonCode(Base):
    __tablename__ = "encounter_reason_code"

    id = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(
        Integer, ForeignKey("encounter.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    coding_system = Column(String, nullable=True)
    coding_code = Column(String, nullable=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)

    encounter = relationship("EncounterModel", back_populates="reason_codes")
