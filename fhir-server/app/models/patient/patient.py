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
from app.models.patient.enums import (
    PatientGender,
    PatientGeneralPractitionerType,
    PatientLinkOtherType,
    PatientLinkType,
)

patient_id_seq = Sequence("patient_id_seq", start=10000, increment=1)


class PatientModel(Base):
    __tablename__ = "patient"

    # Internal PK — never exposed
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
    org_id = Column(String, nullable=True, index=True)

    # ── active (0..1 boolean) ─────────────────────────────────────────────────

    active = Column(Boolean, nullable=True, default=True)

    # ── gender (0..1 code) ────────────────────────────────────────────────────

    gender = Column(Enum(PatientGender, name="patient_gender"), nullable=True)

    # ── birthDate (0..1 date) ─────────────────────────────────────────────────

    birth_date = Column(Date, nullable=True)

    # ── deceased[x] (0..1 — boolean | dateTime) ───────────────────────────────

    deceased_boolean = Column(Boolean, nullable=True)
    deceased_datetime = Column(DateTime(timezone=True), nullable=True)

    # ── maritalStatus (0..1 CodeableConcept) ──────────────────────────────────

    marital_status_system = Column(String, nullable=True)
    marital_status_code = Column(String, nullable=True)
    marital_status_display = Column(String, nullable=True)
    marital_status_text = Column(String, nullable=True)

    # ── multipleBirth[x] (0..1 — boolean | integer) ───────────────────────────

    multiple_birth_boolean = Column(Boolean, nullable=True)
    multiple_birth_integer = Column(Integer, nullable=True)

    # ── managingOrganization (0..1 Reference(Organization)) ───────────────────

    managing_organization_id = Column(Integer, nullable=True)
    managing_organization_display = Column(String, nullable=True)

    # ── Audit ─────────────────────────────────────────────────────────────────

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────

    identifiers = relationship(
        "PatientIdentifier",
        back_populates="patient",
        cascade="all, delete-orphan",
    )
    names = relationship(
        "PatientName",
        back_populates="patient",
        cascade="all, delete-orphan",
    )
    telecoms = relationship(
        "PatientTelecom",
        back_populates="patient",
        cascade="all, delete-orphan",
    )
    addresses = relationship(
        "PatientAddress",
        back_populates="patient",
        cascade="all, delete-orphan",
    )
    photos = relationship(
        "PatientPhoto",
        back_populates="patient",
        cascade="all, delete-orphan",
    )
    contacts = relationship(
        "PatientContact",
        back_populates="patient",
        cascade="all, delete-orphan",
    )
    communications = relationship(
        "PatientCommunication",
        back_populates="patient",
        cascade="all, delete-orphan",
    )
    general_practitioners = relationship(
        "PatientGeneralPractitioner",
        back_populates="patient",
        cascade="all, delete-orphan",
    )
    links = relationship(
        "PatientLink",
        back_populates="patient",
        cascade="all, delete-orphan",
    )


# ── Sub-resource tables ────────────────────────────────────────────────────────


class PatientIdentifier(Base):
    """identifier[] — business identifiers for this patient."""

    __tablename__ = "patient_identifier"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patient.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    use = Column(String, nullable=True)
    type_system = Column(String, nullable=True)
    type_code = Column(String, nullable=True)
    type_display = Column(String, nullable=True)
    system = Column(String, nullable=True)
    value = Column(String, nullable=False)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)
    assigner = Column(String, nullable=True)

    patient = relationship("PatientModel", back_populates="identifiers")


class PatientName(Base):
    """name[] — HumanName — names associated with the patient.

    HumanName fields: use | text | family | given (0..*) | prefix (0..*) | suffix (0..*) | period
    given/prefix/suffix stored comma-separated — never individually filtered.
    """

    __tablename__ = "patient_name"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patient.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    use = Column(String, nullable=True)       # usual|official|temp|nickname|anonymous|old|maiden
    text = Column(String, nullable=True)      # full name as display string
    family = Column(String, nullable=True)
    given = Column(Text, nullable=True)       # comma-separated given names
    prefix = Column(Text, nullable=True)      # comma-separated prefixes (Mr., Dr., etc.)
    suffix = Column(Text, nullable=True)      # comma-separated suffixes (Jr., MD, etc.)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    patient = relationship("PatientModel", back_populates="names")


class PatientTelecom(Base):
    """telecom[] — ContactPoint — contact details for the patient.

    ContactPoint fields: system | value | use | rank | period
    """

    __tablename__ = "patient_telecom"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patient.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    system = Column(String, nullable=True)    # phone|fax|email|pager|url|sms|other
    value = Column(String, nullable=True)
    use = Column(String, nullable=True)       # home|work|temp|old|mobile
    rank = Column(Integer, nullable=True)     # preferred order (1 = highest)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    patient = relationship("PatientModel", back_populates="telecoms")


class PatientAddress(Base):
    """address[] — Address — addresses for the patient.

    Address fields: use | type | text | line (0..*) | city | district | state | postalCode | country | period
    line stored comma-separated — address lines are never individually filtered.
    """

    __tablename__ = "patient_address"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patient.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    use = Column(String, nullable=True)       # home|work|temp|old|billing
    type = Column(String, nullable=True)      # postal|physical|both
    text = Column(String, nullable=True)
    line = Column(Text, nullable=True)        # comma-separated address lines
    city = Column(String, nullable=True)
    district = Column(String, nullable=True)
    state = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    country = Column(String, nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    patient = relationship("PatientModel", back_populates="addresses")


class PatientPhoto(Base):
    """photo[] — Attachment — images of the patient (R4 Attachment fields only)."""

    __tablename__ = "patient_photo"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patient.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    content_type = Column(String, nullable=True)   # MIME type e.g. image/png
    language = Column(String, nullable=True)        # BCP-47 language code
    data = Column(Text, nullable=True)              # base64-encoded binary
    url = Column(String, nullable=True)
    size = Column(Integer, nullable=True)           # bytes before base64 encoding
    hash = Column(String, nullable=True)            # base64-encoded SHA-1
    title = Column(String, nullable=True)
    creation = Column(DateTime(timezone=True), nullable=True)

    patient = relationship("PatientModel", back_populates="photos")


class PatientContact(Base):
    """contact[] BackboneElement — guardian, next-of-kin, or emergency contact.

    BackboneElement fields:
      - relationship (0..*) CodeableConcept  → grandchild PatientContactRelationship
      - name         (0..1) HumanName        → flattened onto this table
      - telecom      (0..*) ContactPoint     → grandchild PatientContactTelecom
      - address      (0..1) Address          → flattened onto this table
      - gender       (0..1) code
      - organization (0..1) Reference(Organization)
      - period       (0..1) Period
    """

    __tablename__ = "patient_contact"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patient.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    # name (0..1 HumanName) — flattened
    name_use = Column(String, nullable=True)
    name_text = Column(String, nullable=True)
    name_family = Column(String, nullable=True)
    name_given = Column(Text, nullable=True)      # comma-separated
    name_prefix = Column(Text, nullable=True)     # comma-separated
    name_suffix = Column(Text, nullable=True)     # comma-separated

    # address (0..1 Address) — flattened
    address_use = Column(String, nullable=True)
    address_type = Column(String, nullable=True)
    address_text = Column(String, nullable=True)
    address_line = Column(Text, nullable=True)    # comma-separated
    address_city = Column(String, nullable=True)
    address_district = Column(String, nullable=True)
    address_state = Column(String, nullable=True)
    address_postal_code = Column(String, nullable=True)
    address_country = Column(String, nullable=True)
    address_period_start = Column(DateTime(timezone=True), nullable=True)
    address_period_end = Column(DateTime(timezone=True), nullable=True)

    # gender (0..1 code)
    gender = Column(String, nullable=True)

    # organization (0..1 Reference(Organization))
    organization_id = Column(Integer, nullable=True)
    organization_display = Column(String, nullable=True)

    # period (0..1 Period)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    patient = relationship("PatientModel", back_populates="contacts")
    relationships = relationship(
        "PatientContactRelationship",
        back_populates="contact",
        cascade="all, delete-orphan",
    )
    telecoms = relationship(
        "PatientContactTelecom",
        back_populates="contact",
        cascade="all, delete-orphan",
    )


class PatientContactRelationship(Base):
    """contact[].relationship[] — CodeableConcept — nature of relationship to patient."""

    __tablename__ = "patient_contact_relationship"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contact_id = Column(Integer, ForeignKey("patient_contact.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    coding_system = Column(String, nullable=True)
    coding_code = Column(String, nullable=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)

    contact = relationship("PatientContact", back_populates="relationships")


class PatientContactTelecom(Base):
    """contact[].telecom[] — ContactPoint — contact details for the contact person."""

    __tablename__ = "patient_contact_telecom"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contact_id = Column(Integer, ForeignKey("patient_contact.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    system = Column(String, nullable=True)
    value = Column(String, nullable=True)
    use = Column(String, nullable=True)
    rank = Column(Integer, nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    contact = relationship("PatientContact", back_populates="telecoms")


class PatientCommunication(Base):
    """communication[] BackboneElement — languages the patient can use for healthcare.

    BackboneElement fields:
      - language  (1..1) CodeableConcept  — ISO-639-1 language code
      - preferred (0..1) boolean
    """

    __tablename__ = "patient_communication"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patient.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    language_system = Column(String, nullable=True)
    language_code = Column(String, nullable=True)
    language_display = Column(String, nullable=True)
    language_text = Column(String, nullable=True)
    preferred = Column(Boolean, nullable=True)

    patient = relationship("PatientModel", back_populates="communications")


class PatientGeneralPractitioner(Base):
    """generalPractitioner[] — Reference(Organization|Practitioner|PractitionerRole)."""

    __tablename__ = "patient_general_practitioner"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patient.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    reference_type = Column(
        Enum(PatientGeneralPractitionerType, name="patient_gp_type"),
        nullable=True,
    )
    reference_id = Column(Integer, nullable=True)
    reference_display = Column(String, nullable=True)

    patient = relationship("PatientModel", back_populates="general_practitioners")


class PatientLink(Base):
    """link[] BackboneElement — links to related Patient or RelatedPerson records.

    BackboneElement fields:
      - other (1..1) Reference(Patient|RelatedPerson)
      - type  (1..1) code — replaced-by|replaces|refer|seealso
    """

    __tablename__ = "patient_link"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patient.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    other_type = Column(
        Enum(PatientLinkOtherType, name="patient_link_other_type"),
        nullable=True,
    )
    other_id = Column(Integer, nullable=True)
    other_display = Column(String, nullable=True)
    type = Column(
        Enum(PatientLinkType, name="patient_link_type"),
        nullable=False,
    )

    patient = relationship("PatientModel", back_populates="links")
