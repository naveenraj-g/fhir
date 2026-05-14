from sqlalchemy import (
    Column,
    Date,
    Boolean,
    Integer,
    String,
    DateTime,
    Enum,
    Sequence,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import FHIRBase as Base
from app.models.enums import GenderType
from app.models.datatypes import CodeableConcept  # noqa: F401 — registers table with metadata

patient_id_seq = Sequence("patient_id_seq", start=10000, increment=1)


class PatientModel(Base):
    __tablename__ = "patient"

    # Internal PK — never exposed outside the backend
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # Public ID — used in all API responses and FHIR output
    patient_id = Column(
        Integer,
        patient_id_seq,
        server_default=patient_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    user_id = Column(String, nullable=True, index=True)
    org_id = Column(String, nullable=True)

    given_name = Column(String, nullable=True)
    family_name = Column(String, nullable=True)
    gender = Column(Enum(GenderType, name="gender_type"), nullable=True)
    birth_date = Column(Date, nullable=True)
    active = Column(Boolean, nullable=True, default=True)
    deceased_boolean = Column(Boolean, nullable=True, default=False)
    deceased_datetime = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Normalized sub-resource relationships (all FK → patient.id)
    identifiers = relationship(
        "PatientIdentifier", back_populates="patient", cascade="all, delete-orphan"
    )
    telecoms = relationship(
        "PatientTelecom", back_populates="patient", cascade="all, delete-orphan"
    )
    addresses = relationship(
        "PatientAddress", back_populates="patient", cascade="all, delete-orphan"
    )


class PatientIdentifier(Base):
    __tablename__ = "patient_identifier"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patient.id"), nullable=False, index=True)

    use = Column(String, nullable=True)
    type_id = Column(Integer, ForeignKey("codeable_concept.id"), nullable=True)
    system = Column(String, nullable=True)
    value = Column(String, nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)
    assigner = Column(String, nullable=True)

    patient = relationship("PatientModel", back_populates="identifiers")
    type = relationship("CodeableConcept", foreign_keys=[type_id])


class PatientTelecom(Base):
    __tablename__ = "patient_telecom"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patient.id"), nullable=False, index=True)

    system = Column(String, nullable=True)  # phone | fax | email | url | sms | other
    value = Column(String, nullable=True)
    use = Column(String, nullable=True)  # home | work | temp | old | mobile

    patient = relationship("PatientModel", back_populates="telecoms")


class PatientAddress(Base):
    __tablename__ = "patient_address"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patient.id"), nullable=False, index=True)

    line = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    country = Column(String, nullable=True)

    patient = relationship("PatientModel", back_populates="addresses")
