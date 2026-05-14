from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.appointment.enums import (
    AppointmentParticipantRequired,
    AppointmentParticipantStatus,
    AppointmentStatus,
)


class AppointmentIdentifierInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    use: Optional[str] = None
    type_system: Optional[str] = None
    type_code: Optional[str] = None
    type_display: Optional[str] = None
    type_text: Optional[str] = None
    system: Optional[str] = None
    value: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    assigner: Optional[str] = None


class AppointmentServiceCategoryInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class AppointmentServiceTypeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class AppointmentSpecialtyInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class AppointmentReasonCodeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class AppointmentReasonReferenceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: str = Field(
        ...,
        description="FHIR reference to the reason resource, e.g. 'Condition/12345' or 'Procedure/67890'.",
    )
    reference_display: Optional[str] = None


class AppointmentSupportingInformationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: str = Field(
        ...,
        description="FHIR reference to any supporting resource, e.g. 'DocumentReference/456'.",
    )
    reference_display: Optional[str] = None


class AppointmentSlotInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    slot_id: int = Field(..., description="Public slot_id.")
    slot_display: Optional[str] = None


class AppointmentBasedOnInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    service_request_id: int = Field(..., description="Public service_request_id.")
    service_request_display: Optional[str] = None


class AppointmentParticipantTypeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class AppointmentParticipantInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    actor: Optional[str] = Field(
        None,
        description="FHIR reference using the public resource ID, e.g. 'Practitioner/30001' or 'Patient/10001'.",
    )
    actor_display: Optional[str] = None
    types: Optional[List[AppointmentParticipantTypeInput]] = Field(
        None,
        description="Participant role code(s), e.g. [{coding_code: 'ATND', coding_display: 'attender'}].",
    )
    required: Optional[AppointmentParticipantRequired] = None
    status: AppointmentParticipantStatus = Field(
        AppointmentParticipantStatus.needs_action,
        description="Participation acceptance status.",
    )
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class AppointmentRequestedPeriodInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


# ── Recurrence template (operational, not FHIR R4 standard) ──────────────────


class RecurrenceWeeklyTemplateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    monday: Optional[bool] = None
    tuesday: Optional[bool] = None
    wednesday: Optional[bool] = None
    thursday: Optional[bool] = None
    friday: Optional[bool] = None
    saturday: Optional[bool] = None
    sunday: Optional[bool] = None
    week_interval: Optional[int] = Field(None, ge=1, description="Weeks between occurrences.")


class RecurrenceMonthlyTemplateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    day_of_month: Optional[int] = Field(None, ge=1, le=31)
    nth_week_code: Optional[str] = Field(None, description="e.g. '1' (1st week) or '-1' (last week).")
    nth_week_display: Optional[str] = None
    day_of_week_code: Optional[str] = Field(None, description="mon | tue | wed | thu | fri | sat | sun")
    day_of_week_display: Optional[str] = None
    month_interval: int = Field(..., ge=1, description="Months between occurrences.")


class RecurrenceYearlyTemplateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    year_interval: int = Field(..., ge=1, description="Years between occurrences.")


class RecurrenceTemplateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    recurrence_type_code: str = Field(..., description="daily | weekly | monthly | yearly", examples=["weekly"])
    recurrence_type_display: Optional[str] = None
    recurrence_type_system: Optional[str] = None
    timezone_code: Optional[str] = Field(None, description="IANA timezone, e.g. 'America/New_York'.")
    timezone_display: Optional[str] = None
    last_occurrence_date: Optional[date] = Field(None, description="Date after which no more occurrences.")
    occurrence_count: Optional[int] = Field(None, ge=1, description="Total number of occurrences.")
    occurrence_dates: Optional[List[date]] = Field(None, description="Explicit list of occurrence dates.")
    excluding_dates: Optional[List[date]] = Field(None, description="Dates within the series to skip.")
    excluding_recurrence_ids: Optional[List[int]] = Field(None, description="Ordinal occurrence positions to skip.")
    weekly_template: Optional[RecurrenceWeeklyTemplateInput] = None
    monthly_template: Optional[RecurrenceMonthlyTemplateInput] = None
    yearly_template: Optional[RecurrenceYearlyTemplateInput] = None


# ── Create / Patch ────────────────────────────────────────────────────────────


class AppointmentCreateSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "user_id": "user-uuid-123",
                "org_id": "org-uuid-456",
                "status": "booked",
                "subject": "Patient/10001",
                "subject_display": "John Doe",
                "encounter_id": 20001,
                "start": "2026-06-01T09:00:00Z",
                "end": "2026-06-01T09:30:00Z",
                "minutes_duration": 30,
                "description": "Follow-up visit for hypertension management",
                "service_type": [{"coding_code": "57", "coding_display": "Immunisation"}],
                "specialty": [{"coding_code": "394814009", "coding_display": "General practice"}],
                "reason_code": [{"coding_code": "274640006", "coding_display": "Fever"}],
                "participant": [
                    {
                        "actor": "Patient/10001",
                        "actor_display": "John Doe",
                        "required": "required",
                        "status": "accepted",
                    },
                    {
                        "actor": "Practitioner/30001",
                        "actor_display": "Dr. Smith",
                        "types": [{"coding_code": "ATND", "coding_display": "attender"}],
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

    # cancelationReason (0..1 CodeableConcept) — R4 single-'l' spelling
    cancelation_reason_system: Optional[str] = None
    cancelation_reason_code: Optional[str] = None
    cancelation_reason_display: Optional[str] = None
    cancelation_reason_text: Optional[str] = None

    # appointmentType (0..1 CodeableConcept)
    appointment_type_system: Optional[str] = None
    appointment_type_code: Optional[str] = None
    appointment_type_display: Optional[str] = None
    appointment_type_text: Optional[str] = None

    # subject (0..1 Reference(Patient|Group))
    subject: Optional[str] = Field(None, description="'Patient/10001' or 'Group/200'")
    subject_display: Optional[str] = None

    # encounter (operational FK, not FHIR R4 standard)
    encounter_id: Optional[int] = Field(None, description="Public encounter_id.")

    # scheduling
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    minutes_duration: Optional[int] = Field(None, ge=1)
    created: Optional[datetime] = Field(None, description="When this appointment was initially created.")

    # descriptive
    description: Optional[str] = None
    comment: Optional[str] = None
    patient_instruction: Optional[str] = None
    priority_value: Optional[int] = Field(None, ge=0, description="0 = not prioritised; higher = more urgent.")

    # sub-resources (arrays)
    identifier: Optional[List[AppointmentIdentifierInput]] = None
    service_category: Optional[List[AppointmentServiceCategoryInput]] = None
    service_type: Optional[List[AppointmentServiceTypeInput]] = None
    specialty: Optional[List[AppointmentSpecialtyInput]] = None
    reason_code: Optional[List[AppointmentReasonCodeInput]] = None
    reason_reference: Optional[List[AppointmentReasonReferenceInput]] = None
    supporting_information: Optional[List[AppointmentSupportingInformationInput]] = None
    slot: Optional[List[AppointmentSlotInput]] = None
    based_on: Optional[List[AppointmentBasedOnInput]] = None
    participant: List[AppointmentParticipantInput] = Field(..., min_length=1)
    requested_period: Optional[List[AppointmentRequestedPeriodInput]] = None
    recurrence_template: Optional[RecurrenceTemplateInput] = None


class AppointmentPatchSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Optional[AppointmentStatus] = None
    cancelation_reason_system: Optional[str] = None
    cancelation_reason_code: Optional[str] = None
    cancelation_reason_display: Optional[str] = None
    cancelation_reason_text: Optional[str] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    minutes_duration: Optional[int] = Field(None, ge=1)
    description: Optional[str] = None
    comment: Optional[str] = None
    patient_instruction: Optional[str] = None
    priority_value: Optional[int] = Field(None, ge=0)
