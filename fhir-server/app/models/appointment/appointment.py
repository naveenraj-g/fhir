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
from app.models.appointment.enums import (
    AppointmentStatus,
    AppointmentParticipantActorType,
)
from app.models.enums import SubjectReferenceType

appointment_id_seq = Sequence("appointment_id_seq", start=40000, increment=1)


class AppointmentModel(Base):
    __tablename__ = "appointment"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    appointment_id = Column(
        Integer,
        appointment_id_seq,
        server_default=appointment_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    user_id = Column(String, nullable=True, index=True)
    org_id = Column(String, nullable=True, index=True)

    # status (1..1)
    status = Column(Enum(AppointmentStatus, name="appointment_status"), nullable=False)

    # cancelationReason (0..1 CodeableConcept) — R4 single-'l' spelling
    cancelation_reason_system = Column(String, nullable=True)
    cancelation_reason_code = Column(String, nullable=True)
    cancelation_reason_display = Column(String, nullable=True)
    cancelation_reason_text = Column(String, nullable=True)

    # appointmentType (0..1 CodeableConcept) — flat columns
    appointment_type_system = Column(String, nullable=True)
    appointment_type_code = Column(String, nullable=True)
    appointment_type_display = Column(String, nullable=True)
    appointment_type_text = Column(String, nullable=True)

    # subject (0..1 Reference(Patient|Group))
    subject_type = Column(
        Enum(SubjectReferenceType, name="subject_reference_type"),
        nullable=True,
    )
    subject_id = Column(Integer, nullable=True)
    subject_display = Column(String, nullable=True)

    # Encounter FK (operational, not FHIR R4 standard)
    encounter_id = Column(Integer, ForeignKey("encounter.id"), nullable=True, index=True)

    # Scheduling
    start = Column(DateTime(timezone=True), nullable=True)
    end = Column(DateTime(timezone=True), nullable=True)
    minutes_duration = Column(Integer, nullable=True)
    created = Column(DateTime(timezone=True), nullable=True)

    # Descriptive
    description = Column(Text, nullable=True)
    patient_instruction = Column(Text, nullable=True)  # R4: 0..1 string
    comment = Column(Text, nullable=True)              # R4: 0..1 string
    priority_value = Column(Integer, nullable=True)    # R4: unsignedInt

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)

    # Relationships
    encounter = relationship("EncounterModel", foreign_keys=[encounter_id])
    identifiers = relationship(
        "AppointmentIdentifier", back_populates="appointment", cascade="all, delete-orphan"
    )
    service_categories = relationship(
        "AppointmentServiceCategory", back_populates="appointment", cascade="all, delete-orphan"
    )
    service_types = relationship(
        "AppointmentServiceType", back_populates="appointment", cascade="all, delete-orphan"
    )
    specialties = relationship(
        "AppointmentSpecialty", back_populates="appointment", cascade="all, delete-orphan"
    )
    reason_codes = relationship(
        "AppointmentReasonCode", back_populates="appointment", cascade="all, delete-orphan"
    )
    reason_references = relationship(
        "AppointmentReasonReference", back_populates="appointment", cascade="all, delete-orphan"
    )
    supporting_informations = relationship(
        "AppointmentSupportingInformation", back_populates="appointment", cascade="all, delete-orphan"
    )
    slots = relationship(
        "AppointmentSlot", back_populates="appointment", cascade="all, delete-orphan"
    )
    based_ons = relationship(
        "AppointmentBasedOn", back_populates="appointment", cascade="all, delete-orphan"
    )
    participants = relationship(
        "AppointmentParticipant", back_populates="appointment", cascade="all, delete-orphan"
    )
    requested_periods = relationship(
        "AppointmentRequestedPeriod", back_populates="appointment", cascade="all, delete-orphan"
    )
    recurrence_template = relationship(
        "AppointmentRecurrenceTemplate",
        back_populates="appointment",
        cascade="all, delete-orphan",
        uselist=False,
    )


class AppointmentIdentifier(Base):
    __tablename__ = "appointment_identifier"

    id = Column(Integer, primary_key=True, autoincrement=True)
    appointment_id = Column(Integer, ForeignKey("appointment.id"), nullable=False, index=True)
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

    appointment = relationship("AppointmentModel", back_populates="identifiers")


class AppointmentServiceCategory(Base):
    """serviceCategory[] (0..*) CodeableConcept."""

    __tablename__ = "appointment_service_category"

    id = Column(Integer, primary_key=True, autoincrement=True)
    appointment_id = Column(Integer, ForeignKey("appointment.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    coding_system = Column(String, nullable=True)
    coding_code = Column(String, nullable=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)

    appointment = relationship("AppointmentModel", back_populates="service_categories")


class AppointmentServiceType(Base):
    """serviceType[] (0..*) CodeableConcept."""

    __tablename__ = "appointment_service_type"

    id = Column(Integer, primary_key=True, autoincrement=True)
    appointment_id = Column(Integer, ForeignKey("appointment.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    coding_system = Column(String, nullable=True)
    coding_code = Column(String, nullable=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)

    appointment = relationship("AppointmentModel", back_populates="service_types")


class AppointmentSpecialty(Base):
    """specialty[] (0..*) CodeableConcept."""

    __tablename__ = "appointment_specialty"

    id = Column(Integer, primary_key=True, autoincrement=True)
    appointment_id = Column(Integer, ForeignKey("appointment.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    coding_system = Column(String, nullable=True)
    coding_code = Column(String, nullable=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)

    appointment = relationship("AppointmentModel", back_populates="specialties")


class AppointmentReasonCode(Base):
    """reasonCode[] (0..*) CodeableConcept."""

    __tablename__ = "appointment_reason_code"

    id = Column(Integer, primary_key=True, autoincrement=True)
    appointment_id = Column(Integer, ForeignKey("appointment.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    coding_system = Column(String, nullable=True)
    coding_code = Column(String, nullable=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)

    appointment = relationship("AppointmentModel", back_populates="reason_codes")


class AppointmentReasonReference(Base):
    """reasonReference[] (0..*) Reference(Condition|Procedure|Observation|ImmunizationRecommendation)."""

    __tablename__ = "appointment_reason_reference"

    id = Column(Integer, primary_key=True, autoincrement=True)
    appointment_id = Column(Integer, ForeignKey("appointment.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    reference_type = Column(String, nullable=True)
    reference_id = Column(Integer, nullable=True)
    reference_display = Column(String, nullable=True)

    appointment = relationship("AppointmentModel", back_populates="reason_references")


class AppointmentSupportingInformation(Base):
    """supportingInformation[] (0..*) Reference(Any)."""

    __tablename__ = "appointment_supporting_information"

    id = Column(Integer, primary_key=True, autoincrement=True)
    appointment_id = Column(Integer, ForeignKey("appointment.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    reference_type = Column(String, nullable=True)
    reference_id = Column(Integer, nullable=True)
    reference_display = Column(String, nullable=True)

    appointment = relationship("AppointmentModel", back_populates="supporting_informations")


class AppointmentSlot(Base):
    """slot[] (0..*) Reference(Slot)."""

    __tablename__ = "appointment_slot"

    id = Column(Integer, primary_key=True, autoincrement=True)
    appointment_id = Column(Integer, ForeignKey("appointment.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    slot_id = Column(Integer, nullable=True)
    slot_display = Column(String, nullable=True)

    appointment = relationship("AppointmentModel", back_populates="slots")


class AppointmentBasedOn(Base):
    """basedOn[] (0..*) Reference(ServiceRequest)."""

    __tablename__ = "appointment_based_on"

    id = Column(Integer, primary_key=True, autoincrement=True)
    appointment_id = Column(Integer, ForeignKey("appointment.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    service_request_id = Column(Integer, nullable=True)
    service_request_display = Column(String, nullable=True)

    appointment = relationship("AppointmentModel", back_populates="based_ons")


class AppointmentParticipant(Base):
    __tablename__ = "appointment_participant"

    id = Column(Integer, primary_key=True, autoincrement=True)
    appointment_id = Column(Integer, ForeignKey("appointment.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    actor_type = Column(
        Enum(AppointmentParticipantActorType, name="appointment_participant_actor_type"),
        nullable=True,
    )
    actor_id = Column(Integer, nullable=True)
    actor_display = Column(String, nullable=True)

    required = Column(String, nullable=True)   # required | optional | information-only
    status = Column(String, nullable=False, default="needs-action")

    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    appointment = relationship("AppointmentModel", back_populates="participants")
    types = relationship(
        "AppointmentParticipantType", back_populates="participant", cascade="all, delete-orphan"
    )


class AppointmentParticipantType(Base):
    """participant.type[] (0..*) CodeableConcept."""

    __tablename__ = "appointment_participant_type"

    id = Column(Integer, primary_key=True, autoincrement=True)
    participant_id = Column(
        Integer, ForeignKey("appointment_participant.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    coding_system = Column(String, nullable=True)
    coding_code = Column(String, nullable=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)

    participant = relationship("AppointmentParticipant", back_populates="types")


class AppointmentRequestedPeriod(Base):
    """requestedPeriod[] (0..*) Period."""

    __tablename__ = "appointment_requested_period"

    id = Column(Integer, primary_key=True, autoincrement=True)
    appointment_id = Column(Integer, ForeignKey("appointment.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    appointment = relationship("AppointmentModel", back_populates="requested_periods")


class AppointmentRecurrenceTemplate(Base):
    """Operational recurrence pattern (not standard FHIR R4 — kept for scheduling use)."""

    __tablename__ = "appointment_recurrence_template"

    id = Column(Integer, primary_key=True, autoincrement=True)
    appointment_id = Column(
        Integer, ForeignKey("appointment.id"), nullable=False, unique=True, index=True
    )

    recurrence_type_code = Column(String, nullable=False)
    recurrence_type_display = Column(String, nullable=True)
    recurrence_type_system = Column(String, nullable=True)

    timezone_code = Column(String, nullable=True)
    timezone_display = Column(String, nullable=True)

    last_occurrence_date = Column(Date, nullable=True)
    occurrence_count = Column(Integer, nullable=True)

    occurrence_dates = Column(Text, nullable=True)
    excluding_dates = Column(Text, nullable=True)
    excluding_recurrence_ids = Column(Text, nullable=True)

    weekly_monday = Column(Boolean, nullable=True)
    weekly_tuesday = Column(Boolean, nullable=True)
    weekly_wednesday = Column(Boolean, nullable=True)
    weekly_thursday = Column(Boolean, nullable=True)
    weekly_friday = Column(Boolean, nullable=True)
    weekly_saturday = Column(Boolean, nullable=True)
    weekly_sunday = Column(Boolean, nullable=True)
    weekly_week_interval = Column(Integer, nullable=True)

    monthly_day_of_month = Column(Integer, nullable=True)
    monthly_nth_week_code = Column(String, nullable=True)
    monthly_nth_week_display = Column(String, nullable=True)
    monthly_day_of_week_code = Column(String, nullable=True)
    monthly_day_of_week_display = Column(String, nullable=True)
    monthly_month_interval = Column(Integer, nullable=True)

    yearly_year_interval = Column(Integer, nullable=True)

    appointment = relationship("AppointmentModel", back_populates="recurrence_template")
