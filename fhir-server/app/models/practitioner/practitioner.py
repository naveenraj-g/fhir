from sqlalchemy import (
    Boolean,
    Column,
    Date,
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
from app.models.practitioner.enums import PractitionerRole

practitioner_id_seq = Sequence("practitioner_id_seq", start=30000, increment=1)


class PractitionerModel(Base):
    __tablename__ = "practitioner"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    practitioner_id = Column(
        Integer,
        practitioner_id_seq,
        server_default=practitioner_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    user_id = Column(String, nullable=True, index=True)
    org_id = Column(String, nullable=True)
    active = Column(Boolean, nullable=True)
    gender = Column(String, nullable=True)
    birth_date = Column(Date, nullable=True)
    deceased_boolean = Column(Boolean, nullable=True)
    deceased_datetime = Column(DateTime(timezone=True), nullable=True)

    # App-specific (not in FHIR spec — kept for operational convenience)
    role = Column(Enum(PractitionerRole, name="practitioner_role"), nullable=True)
    specialty = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)

    names = relationship("PractitionerName", back_populates="practitioner", cascade="all, delete-orphan")
    identifiers = relationship("PractitionerIdentifier", back_populates="practitioner", cascade="all, delete-orphan")
    telecoms = relationship("PractitionerTelecom", back_populates="practitioner", cascade="all, delete-orphan")
    addresses = relationship("PractitionerAddress", back_populates="practitioner", cascade="all, delete-orphan")
    photos = relationship("PractitionerPhoto", back_populates="practitioner", cascade="all, delete-orphan")
    qualifications = relationship("PractitionerQualification", back_populates="practitioner", cascade="all, delete-orphan")
    communications = relationship("PractitionerCommunication", back_populates="practitioner", cascade="all, delete-orphan")


class PractitionerName(Base):
    __tablename__ = "practitioner_name"

    id = Column(Integer, primary_key=True, autoincrement=True)
    practitioner_id = Column(Integer, ForeignKey("practitioner.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    use = Column(String, nullable=True)
    text = Column(String, nullable=True)
    family = Column(String, nullable=True)
    given = Column(Text, nullable=True)   # comma-separated
    prefix = Column(Text, nullable=True)  # comma-separated
    suffix = Column(Text, nullable=True)  # comma-separated
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    practitioner = relationship("PractitionerModel", back_populates="names")


class PractitionerIdentifier(Base):
    __tablename__ = "practitioner_identifier"

    id = Column(Integer, primary_key=True, autoincrement=True)
    practitioner_id = Column(Integer, ForeignKey("practitioner.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    use = Column(String, nullable=True)
    type_system = Column(String, nullable=True)
    type_code = Column(String, nullable=True)
    type_display = Column(String, nullable=True)
    type_text = Column(String, nullable=True)
    system = Column(String, nullable=True)
    value = Column(String, nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)
    assigner = Column(String, nullable=True)

    practitioner = relationship("PractitionerModel", back_populates="identifiers")


class PractitionerTelecom(Base):
    __tablename__ = "practitioner_telecom"

    id = Column(Integer, primary_key=True, autoincrement=True)
    practitioner_id = Column(Integer, ForeignKey("practitioner.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    system = Column(String, nullable=True)
    value = Column(String, nullable=True)
    use = Column(String, nullable=True)
    rank = Column(Integer, nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    practitioner = relationship("PractitionerModel", back_populates="telecoms")


class PractitionerAddress(Base):
    __tablename__ = "practitioner_address"

    id = Column(Integer, primary_key=True, autoincrement=True)
    practitioner_id = Column(Integer, ForeignKey("practitioner.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    use = Column(String, nullable=True)
    type = Column(String, nullable=True)
    text = Column(String, nullable=True)
    line = Column(Text, nullable=True)  # comma-separated
    city = Column(String, nullable=True)
    district = Column(String, nullable=True)
    state = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    country = Column(String, nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    practitioner = relationship("PractitionerModel", back_populates="addresses")


class PractitionerPhoto(Base):
    __tablename__ = "practitioner_photo"

    id = Column(Integer, primary_key=True, autoincrement=True)
    practitioner_id = Column(Integer, ForeignKey("practitioner.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    content_type = Column(String, nullable=True)
    language = Column(String, nullable=True)
    data = Column(Text, nullable=True)
    url = Column(String, nullable=True)
    size = Column(Integer, nullable=True)
    hash = Column(String, nullable=True)
    title = Column(String, nullable=True)
    creation = Column(DateTime(timezone=True), nullable=True)

    practitioner = relationship("PractitionerModel", back_populates="photos")


class PractitionerQualification(Base):
    __tablename__ = "practitioner_qualification"

    id = Column(Integer, primary_key=True, autoincrement=True)
    practitioner_id = Column(Integer, ForeignKey("practitioner.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    # qualification.identifier (one flat identifier per qualification — common case)
    identifier_system = Column(String, nullable=True)
    identifier_value = Column(String, nullable=True)

    # qualification.code (1..1 CodeableConcept — flattened)
    code_system = Column(String, nullable=True)
    code_code = Column(String, nullable=True)
    code_display = Column(String, nullable=True)
    code_text = Column(String, nullable=True)

    # qualification.period (0..1)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # qualification.issuer (0..1 Reference(Organization) — flattened)
    issuer_id = Column(Integer, nullable=True)
    issuer_display = Column(String, nullable=True)

    practitioner = relationship("PractitionerModel", back_populates="qualifications")


class PractitionerCommunication(Base):
    __tablename__ = "practitioner_communication"

    id = Column(Integer, primary_key=True, autoincrement=True)
    practitioner_id = Column(Integer, ForeignKey("practitioner.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    language_system = Column(String, nullable=True)
    language_code = Column(String, nullable=False)
    language_display = Column(String, nullable=True)
    language_text = Column(String, nullable=True)
    preferred = Column(Boolean, nullable=True)

    practitioner = relationship("PractitionerModel", back_populates="communications")
