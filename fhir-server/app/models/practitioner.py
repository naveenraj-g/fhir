from sqlalchemy import (
    Column,
    String,
    Date,
    Boolean,
    ForeignKey,
    Integer,
    DateTime,
    Enum,
    Sequence,
)
from app.models.datatypes import CodeableConcept  # noqa: F401 — registers table with metadata
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import FHIRBase as Base
from app.models.enums import PractitionerRole

practitioner_id_seq = Sequence("practitioner_id_seq", start=30000, increment=1)


class PractitionerModel(Base):
    __tablename__ = "practitioner"

    # Internal PK — never exposed outside the backend
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # Public ID — used in all API responses and FHIR output
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
    given_name = Column(String, nullable=True)
    family_name = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    birth_date = Column(Date, nullable=True)
    role = Column(Enum(PractitionerRole, name="practitioner_role"), nullable=True)
    specialty = Column(String, nullable=True)
    deceased_boolean = Column(Boolean, nullable=True, default=False)
    deceased_datetime = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)

    # Relationships
    identifiers = relationship(
        "PractitionerIdentifier",
        back_populates="practitioner",
        cascade="all, delete-orphan",
    )
    telecoms = relationship(
        "PractitionerTelecom",
        back_populates="practitioner",
        cascade="all, delete-orphan",
    )
    addresses = relationship(
        "PractitionerAddress",
        back_populates="practitioner",
        cascade="all, delete-orphan",
    )
    qualifications = relationship(
        "PractitionerQualification",
        back_populates="practitioner",
        cascade="all, delete-orphan",
    )


class PractitionerIdentifier(Base):
    __tablename__ = "practitioner_identifier"

    id = Column(Integer, primary_key=True, autoincrement=True)
    practitioner_id = Column(
        Integer, ForeignKey("practitioner.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    use = Column(String, nullable=True)
    type_id = Column(Integer, ForeignKey("codeable_concept.id"), nullable=True)
    system = Column(String, nullable=True)
    value = Column(String, nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)
    assigner = Column(String, nullable=True)

    practitioner = relationship("PractitionerModel", back_populates="identifiers")
    type = relationship("CodeableConcept", foreign_keys=[type_id])


class PractitionerTelecom(Base):
    __tablename__ = "practitioner_telecom"

    id = Column(Integer, primary_key=True, autoincrement=True)
    practitioner_id = Column(
        Integer, ForeignKey("practitioner.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    system = Column(String, nullable=True)
    value = Column(String, nullable=True)
    use = Column(String, nullable=True)
    rank = Column(Integer, nullable=True)

    practitioner = relationship("PractitionerModel", back_populates="telecoms")


class PractitionerAddress(Base):
    __tablename__ = "practitioner_address"

    id = Column(Integer, primary_key=True, autoincrement=True)
    practitioner_id = Column(
        Integer, ForeignKey("practitioner.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    use = Column(String, nullable=True)
    type = Column(String, nullable=True)
    text = Column(String, nullable=True)
    line = Column(String, nullable=True)  # Comma separated
    city = Column(String, nullable=True)
    district = Column(String, nullable=True)
    state = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    country = Column(String, nullable=True)

    practitioner = relationship("PractitionerModel", back_populates="addresses")


class PractitionerQualification(Base):
    __tablename__ = "practitioner_qualification"

    id = Column(Integer, primary_key=True, autoincrement=True)
    practitioner_id = Column(
        Integer, ForeignKey("practitioner.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    identifier_system = Column(String, nullable=True)
    identifier_value = Column(String, nullable=True)
    code_text = Column(
        String, nullable=True
    )  # e.g., "MD", "PhD", "Board Certified in Cardiology"
    issuer = Column(String, nullable=True)  # Organization that issued the qualification

    practitioner = relationship("PractitionerModel", back_populates="qualifications")
