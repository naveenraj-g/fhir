from sqlalchemy import (
    Column,
    String,
    DateTime,
    Integer,
    ForeignKey,
    Text,
    Sequence,
    Boolean,
    Date,
    Enum,
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

    # Internal PK — never exposed
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # Public ID — used in all API responses and FHIR output
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

    # Required
    status = Column(
        Enum(AppointmentStatus), nullable=False
    )  # proposed | pending | booked | arrived | fulfilled | cancelled | noshow | entered-in-error | checked-in | waitlist

    cancellation_reason = Column(String, nullable=True)
    cancellation_date = Column(DateTime(timezone=True), nullable=True)

    # Scheduling
    start = Column(DateTime(timezone=True), nullable=True)
    end = Column(DateTime(timezone=True), nullable=True)
    minutes_duration = Column(Integer, nullable=True)
    created = Column(DateTime(timezone=True), nullable=True)

    # Descriptive
    description = Column(Text, nullable=True)
    patient_instruction = Column(Text, nullable=True)
    comment = Column(Text, nullable=True)
    priority_value = Column(Integer, nullable=True)

    # Service / type (stored as flat coded values)
    service_category_code = Column(String, nullable=True)
    service_category_display = Column(String, nullable=True)
    service_type_code = Column(String, nullable=True)
    service_type_display = Column(String, nullable=True)
    specialty_code = Column(String, nullable=True)
    specialty_display = Column(String, nullable=True)
    appointment_type_code = Column(String, nullable=True)
    appointment_type_display = Column(String, nullable=True)

    # Subject reference — stored as type enum + integer ID
    subject_type = Column(
        Enum(SubjectReferenceType, name="subject_reference_type"),
        nullable=True,
    )
    subject_id = Column(Integer, nullable=True)
    subject_display = Column(String, nullable=True)

    # Encounter reference — the encounter this appointment belongs to
    encounter_id = Column(
        Integer, ForeignKey("encounter.id"), nullable=True, index=True
    )

    # Recurrence — for individual instances of a recurring series
    recurrence_id = Column(Integer, nullable=True)  # which occurrence in the series
    occurrence_changed = Column(
        Boolean, nullable=True
    )  # was this instance changed from the template

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    encounter = relationship(
        "EncounterModel", back_populates="appointments", foreign_keys=[encounter_id]
    )
    participants = relationship(
        "AppointmentParticipant",
        back_populates="appointment",
        cascade="all, delete-orphan",
    )
    reason_codes = relationship(
        "AppointmentReasonCode",
        back_populates="appointment",
        cascade="all, delete-orphan",
    )
    recurrence_template = relationship(
        "AppointmentRecurrenceTemplate",
        back_populates="appointment",
        cascade="all, delete-orphan",
        uselist=False,
    )


class AppointmentParticipant(Base):
    __tablename__ = "appointment_participant"

    id = Column(Integer, primary_key=True, autoincrement=True)
    appointment_id = Column(
        Integer, ForeignKey("appointment.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    actor_reference_type = Column(
        Enum(AppointmentParticipantActorType), nullable=True
    )  # e.g. "Patient/123", "Practitioner/456"
    actor_reference_id = Column(Integer, nullable=True)
    actor_display = Column(String, nullable=True)

    type_code = Column(String, nullable=True)
    type_display = Column(String, nullable=True)
    type_text = Column(String, nullable=True)

    required = Column(String, nullable=True)  # required | optional | information-only
    status = Column(
        String, nullable=False, default="needs-action"
    )  # accepted | declined | tentative | needs-action

    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    appointment = relationship("AppointmentModel", back_populates="participants")


class AppointmentReasonCode(Base):
    __tablename__ = "appointment_reason_code"

    id = Column(Integer, primary_key=True, autoincrement=True)
    appointment_id = Column(
        Integer, ForeignKey("appointment.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    coding_system = Column(String, nullable=True)
    coding_code = Column(String, nullable=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)

    appointment = relationship("AppointmentModel", back_populates="reason_codes")


class AppointmentRecurrenceTemplate(Base):
    """
    Stores the recurrence pattern for a recurring Appointment series.
    One-to-one with AppointmentModel (uselist=False on the parent side).
    """

    __tablename__ = "appointment_recurrence_template"

    id = Column(Integer, primary_key=True, autoincrement=True)
    appointment_id = Column(
        Integer, ForeignKey("appointment.id"), nullable=False, unique=True, index=True
    )

    # recurrenceType (required) — code/display/system of the frequency
    recurrence_type_code = Column(
        String, nullable=False
    )  # daily | weekly | monthly | yearly
    recurrence_type_display = Column(String, nullable=True)
    recurrence_type_system = Column(String, nullable=True)

    # timezone — IANA timezone identifier code
    timezone_code = Column(String, nullable=True)
    timezone_display = Column(String, nullable=True)

    # Termination — either lastOccurrenceDate OR occurrenceCount
    last_occurrence_date = Column(Date, nullable=True)
    occurrence_count = Column(Integer, nullable=True)

    # Array fields stored as comma-separated strings
    occurrence_dates = Column(Text, nullable=True)  # "2024-01-01,2024-01-08,..."
    excluding_dates = Column(Text, nullable=True)  # "2024-01-15,..."
    excluding_recurrence_ids = Column(Text, nullable=True)  # "2,5,7"

    # ── weeklyTemplate ────────────────────────────────────────────────────
    weekly_monday = Column(Boolean, nullable=True)
    weekly_tuesday = Column(Boolean, nullable=True)
    weekly_wednesday = Column(Boolean, nullable=True)
    weekly_thursday = Column(Boolean, nullable=True)
    weekly_friday = Column(Boolean, nullable=True)
    weekly_saturday = Column(Boolean, nullable=True)
    weekly_sunday = Column(Boolean, nullable=True)
    weekly_week_interval = Column(Integer, nullable=True)  # weeks between occurrences

    # ── monthlyTemplate ───────────────────────────────────────────────────
    monthly_day_of_month = Column(Integer, nullable=True)  # 1–31
    monthly_nth_week_code = Column(
        String, nullable=True
    )  # 1st | 2nd | 3rd | 4th | -1st
    monthly_nth_week_display = Column(String, nullable=True)
    monthly_day_of_week_code = Column(
        String, nullable=True
    )  # mon | tue | wed | thu | fri | sat | sun
    monthly_day_of_week_display = Column(String, nullable=True)
    monthly_month_interval = Column(
        Integer, nullable=True
    )  # months between occurrences

    # ── yearlyTemplate ────────────────────────────────────────────────────
    yearly_year_interval = Column(Integer, nullable=True)  # years between occurrences

    appointment = relationship("AppointmentModel", back_populates="recurrence_template")
