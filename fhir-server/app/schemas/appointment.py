from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.appointment.enums import (
    AppointmentStatus,
    AppointmentParticipantStatus,
    AppointmentParticipantRequired,
)


# ── Recurrence template input schemas ─────────────────────────────────────


class RecurrenceWeeklyTemplateInput(BaseModel):
    """Days of the week on which the appointment recurs."""

    model_config = ConfigDict(extra="forbid")
    monday: Optional[bool] = None
    tuesday: Optional[bool] = None
    wednesday: Optional[bool] = None
    thursday: Optional[bool] = None
    friday: Optional[bool] = None
    saturday: Optional[bool] = None
    sunday: Optional[bool] = None
    week_interval: Optional[int] = Field(None, ge=1, description="Weeks between occurrences (default 1).")


class RecurrenceMonthlyTemplateInput(BaseModel):
    """Monthly recurrence — either a fixed day-of-month or an nth weekday."""

    model_config = ConfigDict(extra="forbid")
    day_of_month: Optional[int] = Field(None, ge=1, le=31, description="Fixed day of the month (e.g. 15).")
    nth_week_code: Optional[str] = Field(None, description="Nth week ordinal code, e.g. '1' (1st), '-1' (last).")
    nth_week_display: Optional[str] = None
    day_of_week_code: Optional[str] = Field(None, description="Day of week code: mon | tue | wed | thu | fri | sat | sun.")
    day_of_week_display: Optional[str] = None
    month_interval: int = Field(..., ge=1, description="Months between occurrences.")


class RecurrenceYearlyTemplateInput(BaseModel):
    """Yearly recurrence."""

    model_config = ConfigDict(extra="forbid")
    year_interval: int = Field(..., ge=1, description="Years between occurrences.")


class RecurrenceTemplateInput(BaseModel):
    """
    Defines the recurrence pattern for a series of appointments.
    Exactly one of weekly_template, monthly_template, or yearly_template
    should be provided to match recurrence_type_code.
    """

    model_config = ConfigDict(extra="forbid")
    recurrence_type_code: str = Field(
        ...,
        description="Frequency of recurrence: daily | weekly | monthly | yearly.",
        examples=["weekly"],
    )
    recurrence_type_display: Optional[str] = None
    recurrence_type_system: Optional[str] = None
    timezone_code: Optional[str] = Field(None, description="IANA timezone, e.g. 'America/New_York'.")
    timezone_display: Optional[str] = None
    last_occurrence_date: Optional[date] = Field(None, description="Date after which no more occurrences.")
    occurrence_count: Optional[int] = Field(None, ge=1, description="Total number of occurrences.")
    occurrence_dates: Optional[List[date]] = Field(None, description="Explicit list of occurrence dates.")
    excluding_dates: Optional[List[date]] = Field(None, description="Dates within the series to skip.")
    excluding_recurrence_ids: Optional[List[int]] = Field(None, description="Recurrence IDs (ordinal positions) to skip.")
    weekly_template: Optional[RecurrenceWeeklyTemplateInput] = None
    monthly_template: Optional[RecurrenceMonthlyTemplateInput] = None
    yearly_template: Optional[RecurrenceYearlyTemplateInput] = None


# ── Sub-resource input schemas ─────────────────────────────────────────────


class AppointmentParticipantInput(BaseModel):
    """A participant involved in the appointment."""

    model_config = ConfigDict(extra="forbid")
    actor: Optional[str] = Field(
        None,
        description="FHIR reference using the public resource ID, e.g. 'Practitioner/30001' or 'Patient/10001'.",
        examples=["Practitioner/30001"],
    )
    actor_display: Optional[str] = Field(None, description="Display name for the actor, e.g. 'Dr. Smith'.")
    type_code: Optional[str] = Field(None, description="Participant role code, e.g. 'ATND'.")
    type_display: Optional[str] = Field(None, description="Human-readable role label, e.g. 'attender'.")
    type_text: Optional[str] = Field(None, description="Free-text role description.")
    required: Optional[AppointmentParticipantRequired] = None
    status: AppointmentParticipantStatus = Field(
        AppointmentParticipantStatus.NEEDS_ACTION,
        description="Participation acceptance status.",
    )
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class AppointmentReasonInput(BaseModel):
    """A coded reason / chief complaint for the appointment."""

    model_config = ConfigDict(extra="forbid")
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


# ── Appointment create / patch ─────────────────────────────────────────────


class AppointmentCreateSchema(BaseModel):
    """
    Payload for creating an Appointment.

    An Appointment is a booking of a healthcare event for a patient and/or
    practitioner(s) at a specific date and time. At least one participant is required.
    References use public IDs (e.g. Patient/10001, Practitioner/30001).
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "status": "booked",
                "subject": "Patient/10001",
                "subject_display": "John Doe",
                "encounter_id": 20001,
                "start": "2026-06-01T09:00:00Z",
                "end": "2026-06-01T09:30:00Z",
                "minutes_duration": 30,
                "description": "Follow-up visit for hypertension management",
                "comment": "Patient prefers morning appointments",
                "patient_instruction": "Please arrive 10 minutes early.",
                "priority_value": 5,
                "service_category_code": "gp",
                "service_category_display": "General Practice",
                "service_type_code": "11429006",
                "service_type_display": "Consultation",
                "specialty_code": "394814009",
                "specialty_display": "General practice",
                "appointment_type_code": "FOLLOWUP",
                "appointment_type_display": "A follow up visit from a previous appointment",
                "reason_codes": [
                    {
                        "coding_system": "http://snomed.info/sct",
                        "coding_code": "274640006",
                        "coding_display": "Fever with chills",
                        "text": "Fever with chills",
                    }
                ],
                "participant": [
                    {
                        "actor": "Patient/10001",
                        "actor_display": "Jane Doe",
                        "required": "required",
                        "status": "accepted",
                    },
                    {
                        "actor": "Practitioner/30001",
                        "actor_display": "Dr. Smith",
                        "type_code": "ATND",
                        "type_display": "attender",
                        "required": "required",
                        "status": "accepted",
                    },
                ],
            }
        },
    )

    user_id: Optional[str] = None
    org_id: Optional[str] = None
    status: AppointmentStatus
    subject: Optional[str] = Field(
        None,
        description="Patient reference using the public patient_id, e.g. 'Patient/10001'.",
    )
    subject_display: Optional[str] = Field(
        None, description="Human-readable display name for the subject, e.g. 'John Doe'."
    )
    encounter_id: Optional[int] = Field(
        None, description="Public encounter_id this appointment belongs to (e.g. 20001)."
    )
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    minutes_duration: Optional[int] = Field(None, ge=1, description="Expected duration in minutes.")
    created: Optional[datetime] = Field(None, description="Date this appointment was initially created.")
    description: Optional[str] = None
    comment: Optional[str] = None
    patient_instruction: Optional[str] = None
    priority_value: Optional[int] = Field(None, ge=0, description="Priority (0 = not prioritized, higher = more urgent).")
    service_category_code: Optional[str] = None
    service_category_display: Optional[str] = None
    service_type_code: Optional[str] = None
    service_type_display: Optional[str] = None
    specialty_code: Optional[str] = None
    specialty_display: Optional[str] = None
    appointment_type_code: Optional[str] = None
    appointment_type_display: Optional[str] = None
    cancellation_reason: Optional[str] = Field(
        None, description="Reason for cancellation (e.g. 'Patient request')."
    )
    cancellation_date: Optional[datetime] = Field(
        None, description="Date/time the appointment was cancelled."
    )
    reason_codes: Optional[List[AppointmentReasonInput]] = None
    participant: List[AppointmentParticipantInput] = Field(..., min_length=1)
    # Recurrence
    recurrence_id: Optional[int] = Field(
        None, ge=1, description="For a recurring instance: which occurrence in the series this is."
    )
    occurrence_changed: Optional[bool] = Field(
        None, description="True if this instance was changed from the recurrence template."
    )
    recurrence_template: Optional[RecurrenceTemplateInput] = None


class AppointmentPatchSchema(BaseModel):
    """
    Partial update for an Appointment.

    Allows updating scheduling and lifecycle fields. Structural data
    (participants, service fields) cannot be changed after creation.
    """

    model_config = ConfigDict(extra="forbid")

    status: Optional[AppointmentStatus] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    minutes_duration: Optional[int] = Field(None, ge=1)
    description: Optional[str] = None
    comment: Optional[str] = None
    patient_instruction: Optional[str] = None
    priority_value: Optional[int] = Field(None, ge=0)
    cancellation_reason: Optional[str] = None
    cancellation_date: Optional[datetime] = None


# ── FHIR response fragments (read-only) ───────────────────────────────────


class FHIRCoding(BaseModel):
    system: Optional[str] = None
    code: Optional[str] = None
    display: Optional[str] = None


class FHIRCodeableConcept(BaseModel):
    coding: Optional[List[FHIRCoding]] = None
    text: Optional[str] = None


class FHIRReference(BaseModel):
    reference: Optional[str] = None
    display: Optional[str] = None


class FHIRPeriod(BaseModel):
    start: Optional[datetime] = None
    end: Optional[datetime] = None


class FHIRAppointmentParticipant(BaseModel):
    type: Optional[List[FHIRCodeableConcept]] = None
    actor: Optional[FHIRReference] = None
    required: Optional[str] = None
    status: str
    period: Optional[FHIRPeriod] = None


class FHIRWeeklyTemplate(BaseModel):
    monday: Optional[bool] = None
    tuesday: Optional[bool] = None
    wednesday: Optional[bool] = None
    thursday: Optional[bool] = None
    friday: Optional[bool] = None
    saturday: Optional[bool] = None
    sunday: Optional[bool] = None
    weekInterval: Optional[int] = None


class FHIRMonthlyTemplate(BaseModel):
    dayOfMonth: Optional[int] = None
    nthWeekOfMonth: Optional[FHIRCoding] = None
    dayOfWeek: Optional[FHIRCoding] = None
    monthInterval: int


class FHIRYearlyTemplate(BaseModel):
    yearInterval: int


class FHIRRecurrenceTemplate(BaseModel):
    timezone: Optional[FHIRCodeableConcept] = None
    recurrenceType: FHIRCodeableConcept
    lastOccurrenceDate: Optional[date] = None
    occurrenceCount: Optional[int] = None
    occurrenceDates: Optional[List[date]] = None
    excludingDate: Optional[List[date]] = None
    excludingRecurrenceId: Optional[List[int]] = None
    weeklyTemplate: Optional[FHIRWeeklyTemplate] = None
    monthlyTemplate: Optional[FHIRMonthlyTemplate] = None
    yearlyTemplate: Optional[FHIRYearlyTemplate] = None


# ── Plain response sub-schemas ─────────────────────────────────────────────


class AppointmentReasonCodeSchema(BaseModel):
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class AppointmentParticipantSchema(BaseModel):
    actor_type: Optional[str] = None
    actor_id: Optional[int] = None
    actor_display: Optional[str] = None
    type_code: Optional[str] = None
    type_display: Optional[str] = None
    type_text: Optional[str] = None
    required: Optional[str] = None
    status: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class AppointmentWeeklyTemplateSchema(BaseModel):
    monday: Optional[bool] = None
    tuesday: Optional[bool] = None
    wednesday: Optional[bool] = None
    thursday: Optional[bool] = None
    friday: Optional[bool] = None
    saturday: Optional[bool] = None
    sunday: Optional[bool] = None
    week_interval: Optional[int] = None


class AppointmentMonthlyTemplateSchema(BaseModel):
    day_of_month: Optional[int] = None
    nth_week_code: Optional[str] = None
    nth_week_display: Optional[str] = None
    day_of_week_code: Optional[str] = None
    day_of_week_display: Optional[str] = None
    month_interval: Optional[int] = None


class AppointmentYearlyTemplateSchema(BaseModel):
    year_interval: int


class AppointmentRecurrenceTemplateSchema(BaseModel):
    recurrence_type_code: Optional[str] = None
    recurrence_type_display: Optional[str] = None
    recurrence_type_system: Optional[str] = None
    timezone_code: Optional[str] = None
    timezone_display: Optional[str] = None
    last_occurrence_date: Optional[date] = None
    occurrence_count: Optional[int] = None
    occurrence_dates: Optional[List[str]] = None
    excluding_dates: Optional[List[str]] = None
    excluding_recurrence_ids: Optional[List[int]] = None
    weekly_template: Optional[AppointmentWeeklyTemplateSchema] = None
    monthly_template: Optional[AppointmentMonthlyTemplateSchema] = None
    yearly_template: Optional[AppointmentYearlyTemplateSchema] = None


# ── Response schema ────────────────────────────────────────────────────────


class AppointmentResponseSchema(BaseModel):
    """
    Plain snake_case Appointment resource returned by all read/write endpoints.

    - `id` is the PUBLIC appointment_id (e.g. 40001) — never the internal PK.
    - References are split into _type and _id fields (no FHIR reference strings).
    """

    model_config = ConfigDict(populate_by_name=True)

    id: int
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    status: str
    subject_type: Optional[str] = None
    subject_id: Optional[int] = None
    subject_display: Optional[str] = None
    encounter_id: Optional[int] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    minutes_duration: Optional[int] = None
    created: Optional[datetime] = None
    description: Optional[str] = None
    comment: Optional[str] = None
    patient_instruction: Optional[str] = None
    priority: Optional[int] = None
    cancellation_reason: Optional[str] = None
    cancellation_date: Optional[datetime] = None
    service_category_code: Optional[str] = None
    service_category_display: Optional[str] = None
    service_type_code: Optional[str] = None
    service_type_display: Optional[str] = None
    specialty_code: Optional[str] = None
    specialty_display: Optional[str] = None
    appointment_type_code: Optional[str] = None
    appointment_type_display: Optional[str] = None
    reason_code: Optional[List[AppointmentReasonCodeSchema]] = None
    participant: Optional[List[AppointmentParticipantSchema]] = None
    recurrence_id: Optional[int] = None
    occurrence_changed: Optional[bool] = None
    recurrence_template: Optional[AppointmentRecurrenceTemplateSchema] = None
