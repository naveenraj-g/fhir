from sqlalchemy import (
    Boolean,
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
from app.models.encounter.enums import (
    EncounterStatus,
    EncounterLocationStatus,
    EncounterParticipantReferenceType,
    EncounterBasedOnReferenceType,
    EncounterDiagnosisConditionType,
)
from app.models.enums import SubjectReferenceType

encounter_id_seq = Sequence("encounter_id_seq", start=20000, increment=1)


class EncounterModel(Base):
    __tablename__ = "encounter"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
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

    # status (1..1)
    status = Column(Enum(EncounterStatus, name="encounter_status"), nullable=True)

    # class (1..1 Coding) — flat columns replace the old Enum column
    class_system = Column(String, nullable=True)
    class_version = Column(String, nullable=True)
    class_code = Column(String, nullable=True)
    class_display = Column(String, nullable=True)

    # type (0..*) → child table encounter_type

    # serviceType (0..1 CodeableConcept) — flat columns
    service_type_system = Column(String, nullable=True)
    service_type_code = Column(String, nullable=True)
    service_type_display = Column(String, nullable=True)
    service_type_text = Column(String, nullable=True)

    # priority (0..1 CodeableConcept) — flat columns
    priority_system = Column(String, nullable=True)
    priority_code = Column(String, nullable=True)
    priority_display = Column(String, nullable=True)
    priority_text = Column(String, nullable=True)

    # subject (0..1 Reference(Patient|Group))
    subject_type = Column(
        Enum(SubjectReferenceType, name="subject_reference_type"),
        nullable=True,
    )
    subject_id = Column(Integer, nullable=True)
    subject_display = Column(String, nullable=True)

    # period (0..1)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # length (0..1 Duration) — flat columns
    length_value = Column(Float, nullable=True)
    length_comparator = Column(String, nullable=True)
    length_unit = Column(String, nullable=True)
    length_system = Column(String, nullable=True)
    length_code = Column(String, nullable=True)

    # hospitalization (0..1 BackboneElement) — flat columns for 0..1 sub-fields
    # preAdmissionIdentifier (0..1 Identifier)
    hosp_pre_admission_identifier_system = Column(String, nullable=True)
    hosp_pre_admission_identifier_value = Column(String, nullable=True)
    # origin (0..1 Reference(Location|Organization))
    hosp_origin_type = Column(String, nullable=True)
    hosp_origin_id = Column(Integer, nullable=True)
    hosp_origin_display = Column(String, nullable=True)
    # admitSource (0..1 CodeableConcept)
    hosp_admit_source_system = Column(String, nullable=True)
    hosp_admit_source_code = Column(String, nullable=True)
    hosp_admit_source_display = Column(String, nullable=True)
    hosp_admit_source_text = Column(String, nullable=True)
    # reAdmission (0..1 CodeableConcept)
    hosp_re_admission_system = Column(String, nullable=True)
    hosp_re_admission_code = Column(String, nullable=True)
    hosp_re_admission_display = Column(String, nullable=True)
    hosp_re_admission_text = Column(String, nullable=True)
    # destination (0..1 Reference(Location|Organization))
    hosp_destination_type = Column(String, nullable=True)
    hosp_destination_id = Column(Integer, nullable=True)
    hosp_destination_display = Column(String, nullable=True)
    # dischargeDisposition (0..1 CodeableConcept)
    hosp_discharge_disposition_system = Column(String, nullable=True)
    hosp_discharge_disposition_code = Column(String, nullable=True)
    hosp_discharge_disposition_display = Column(String, nullable=True)
    hosp_discharge_disposition_text = Column(String, nullable=True)

    # serviceProvider (0..1 Reference(Organization))
    service_provider_id = Column(Integer, nullable=True)
    service_provider_display = Column(String, nullable=True)

    # partOf (0..1 Reference(Encounter)) — store the public encounter_id
    part_of_id = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)

    # Relationships
    identifiers = relationship(
        "EncounterIdentifier", back_populates="encounter", cascade="all, delete-orphan"
    )
    status_history = relationship(
        "EncounterStatusHistory", back_populates="encounter", cascade="all, delete-orphan"
    )
    class_history = relationship(
        "EncounterClassHistory", back_populates="encounter", cascade="all, delete-orphan"
    )
    types = relationship(
        "EncounterType", back_populates="encounter", cascade="all, delete-orphan"
    )
    episode_of_cares = relationship(
        "EncounterEpisodeOfCare", back_populates="encounter", cascade="all, delete-orphan"
    )
    based_ons = relationship(
        "EncounterBasedOn", back_populates="encounter", cascade="all, delete-orphan"
    )
    participants = relationship(
        "EncounterParticipant", back_populates="encounter", cascade="all, delete-orphan"
    )
    appointment_refs = relationship(
        "EncounterAppointmentRef", back_populates="encounter", cascade="all, delete-orphan"
    )
    reason_codes = relationship(
        "EncounterReasonCode", back_populates="encounter", cascade="all, delete-orphan"
    )
    reason_references = relationship(
        "EncounterReasonReference", back_populates="encounter", cascade="all, delete-orphan"
    )
    diagnoses = relationship(
        "EncounterDiagnosis", back_populates="encounter", cascade="all, delete-orphan"
    )
    accounts = relationship(
        "EncounterAccount", back_populates="encounter", cascade="all, delete-orphan"
    )
    hosp_diet_preferences = relationship(
        "EncounterHospDietPreference", back_populates="encounter", cascade="all, delete-orphan"
    )
    hosp_special_arrangements = relationship(
        "EncounterHospSpecialArrangement", back_populates="encounter", cascade="all, delete-orphan"
    )
    hosp_special_courtesies = relationship(
        "EncounterHospSpecialCourtesy", back_populates="encounter", cascade="all, delete-orphan"
    )
    locations = relationship(
        "EncounterLocation", back_populates="encounter", cascade="all, delete-orphan"
    )
    questionnaire_responses = relationship(
        "QuestionnaireResponseModel", back_populates="encounter"
    )


class EncounterIdentifier(Base):
    __tablename__ = "encounter_identifier"

    id = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(Integer, ForeignKey("encounter.id"), nullable=False, index=True)
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

    encounter = relationship("EncounterModel", back_populates="identifiers")


class EncounterStatusHistory(Base):
    __tablename__ = "encounter_status_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(Integer, ForeignKey("encounter.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    status = Column(String, nullable=False)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    encounter = relationship("EncounterModel", back_populates="status_history")


class EncounterClassHistory(Base):
    __tablename__ = "encounter_class_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(Integer, ForeignKey("encounter.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    class_system = Column(String, nullable=True)
    class_version = Column(String, nullable=True)
    class_code = Column(String, nullable=True)
    class_display = Column(String, nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    encounter = relationship("EncounterModel", back_populates="class_history")


class EncounterType(Base):
    __tablename__ = "encounter_type"

    id = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(Integer, ForeignKey("encounter.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    coding_system = Column(String, nullable=True)
    coding_code = Column(String, nullable=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)

    encounter = relationship("EncounterModel", back_populates="types")


class EncounterEpisodeOfCare(Base):
    __tablename__ = "encounter_episode_of_care"

    id = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(Integer, ForeignKey("encounter.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    episode_of_care_id = Column(Integer, nullable=True)
    display = Column(String, nullable=True)

    encounter = relationship("EncounterModel", back_populates="episode_of_cares")


class EncounterBasedOn(Base):
    __tablename__ = "encounter_based_on"

    id = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(Integer, ForeignKey("encounter.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    reference_type = Column(
        Enum(EncounterBasedOnReferenceType, name="encounter_based_on_reference_type"),
        nullable=True,
    )
    reference_id = Column(Integer, nullable=True)
    reference_display = Column(String, nullable=True)

    encounter = relationship("EncounterModel", back_populates="based_ons")


class EncounterParticipant(Base):
    __tablename__ = "encounter_participant"

    id = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(Integer, ForeignKey("encounter.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    # individual reference (0..1)
    individual_type = Column(
        Enum(EncounterParticipantReferenceType, name="encounter_participant_reference_type"),
        nullable=True,
    )
    individual_id = Column(Integer, nullable=True)
    individual_display = Column(String, nullable=True)

    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    encounter = relationship("EncounterModel", back_populates="participants")
    types = relationship(
        "EncounterParticipantType", back_populates="participant", cascade="all, delete-orphan"
    )


class EncounterParticipantType(Base):
    """participant.type[] (0..*) CodeableConcept — one row per coding entry."""

    __tablename__ = "encounter_participant_type"

    id = Column(Integer, primary_key=True, autoincrement=True)
    participant_id = Column(
        Integer, ForeignKey("encounter_participant.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    coding_system = Column(String, nullable=True)
    coding_code = Column(String, nullable=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)

    participant = relationship("EncounterParticipant", back_populates="types")


class EncounterAppointmentRef(Base):
    """appointment[] (0..*) Reference(Appointment)."""

    __tablename__ = "encounter_appointment_ref"

    id = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(Integer, ForeignKey("encounter.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    appointment_id = Column(Integer, nullable=True)
    appointment_display = Column(String, nullable=True)

    encounter = relationship("EncounterModel", back_populates="appointment_refs")


class EncounterReasonCode(Base):
    __tablename__ = "encounter_reason_code"

    id = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(Integer, ForeignKey("encounter.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    coding_system = Column(String, nullable=True)
    coding_code = Column(String, nullable=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)

    encounter = relationship("EncounterModel", back_populates="reason_codes")


class EncounterReasonReference(Base):
    """reasonReference[] (0..*) Reference(Condition|Observation|Procedure|ImmunizationRecommendation)."""

    __tablename__ = "encounter_reason_reference"

    id = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(Integer, ForeignKey("encounter.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    reference_type = Column(String, nullable=True)
    reference_id = Column(Integer, nullable=True)
    reference_display = Column(String, nullable=True)

    encounter = relationship("EncounterModel", back_populates="reason_references")


class EncounterDiagnosis(Base):
    __tablename__ = "encounter_diagnosis"

    id = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(Integer, ForeignKey("encounter.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    # condition (1..1 Reference(Condition|Procedure))
    condition_type = Column(
        Enum(EncounterDiagnosisConditionType, name="encounter_diagnosis_condition_type"),
        nullable=True,
    )
    condition_id = Column(Integer, nullable=True)
    condition_display = Column(String, nullable=True)

    # use (0..1 CodeableConcept)
    use_system = Column(String, nullable=True)
    use_code = Column(String, nullable=True)
    use_display = Column(String, nullable=True)
    use_text = Column(String, nullable=True)

    rank = Column(Integer, nullable=True)

    encounter = relationship("EncounterModel", back_populates="diagnoses")


class EncounterAccount(Base):
    """account[] (0..*) Reference(Account)."""

    __tablename__ = "encounter_account"

    id = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(Integer, ForeignKey("encounter.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    account_id = Column(Integer, nullable=True)
    account_display = Column(String, nullable=True)

    encounter = relationship("EncounterModel", back_populates="accounts")


class EncounterHospDietPreference(Base):
    """hospitalization.dietPreference[] (0..*) CodeableConcept."""

    __tablename__ = "encounter_hosp_diet_preference"

    id = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(Integer, ForeignKey("encounter.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    coding_system = Column(String, nullable=True)
    coding_code = Column(String, nullable=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)

    encounter = relationship("EncounterModel", back_populates="hosp_diet_preferences")


class EncounterHospSpecialArrangement(Base):
    """hospitalization.specialArrangement[] (0..*) CodeableConcept."""

    __tablename__ = "encounter_hosp_special_arrangement"

    id = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(Integer, ForeignKey("encounter.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    coding_system = Column(String, nullable=True)
    coding_code = Column(String, nullable=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)

    encounter = relationship("EncounterModel", back_populates="hosp_special_arrangements")


class EncounterHospSpecialCourtesy(Base):
    """hospitalization.specialCourtesy[] (0..*) CodeableConcept."""

    __tablename__ = "encounter_hosp_special_courtesy"

    id = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(Integer, ForeignKey("encounter.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    coding_system = Column(String, nullable=True)
    coding_code = Column(String, nullable=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)

    encounter = relationship("EncounterModel", back_populates="hosp_special_courtesies")


class EncounterLocation(Base):
    __tablename__ = "encounter_location"

    id = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(Integer, ForeignKey("encounter.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    # location (1..1 Reference(Location))
    location_id = Column(Integer, nullable=True)
    location_display = Column(String, nullable=True)

    status = Column(
        Enum(EncounterLocationStatus, name="encounter_location_status"),
        nullable=True,
    )

    # physicalType (0..1 CodeableConcept)
    physical_type_system = Column(String, nullable=True)
    physical_type_code = Column(String, nullable=True)
    physical_type_display = Column(String, nullable=True)
    physical_type_text = Column(String, nullable=True)

    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    encounter = relationship("EncounterModel", back_populates="locations")
