from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.fhir.common import (
    FHIRBundle,
    FHIRCoding,
    FHIRCodeableConcept,
    FHIRReference,
    FHIRPeriod,
    PlainReasonCode,
)


class FHIRAppointmentParticipantType(BaseModel):
    coding: Optional[List[FHIRCoding]] = None
    text: Optional[str] = None


class FHIRAppointmentParticipant(BaseModel):
    type: Optional[List[FHIRAppointmentParticipantType]] = None
    actor: Optional[FHIRReference] = None
    required: Optional[str] = Field(None, description="required | optional | information-only")
    status: str = Field(..., description="accepted | declined | tentative | needs-action")
    period: Optional[FHIRPeriod] = None


class FHIRAppointmentReasonCode(BaseModel):
    coding: Optional[List[FHIRCoding]] = None
    text: Optional[str] = None


class FHIRRecurrenceWeeklyTemplate(BaseModel):
    monday: Optional[bool] = None
    tuesday: Optional[bool] = None
    wednesday: Optional[bool] = None
    thursday: Optional[bool] = None
    friday: Optional[bool] = None
    saturday: Optional[bool] = None
    sunday: Optional[bool] = None
    weekInterval: Optional[int] = None


class FHIRRecurrenceMonthlyTemplate(BaseModel):
    dayOfMonth: Optional[int] = None
    nthWeekOfMonth: Optional[Dict[str, str]] = None
    dayOfWeek: Optional[Dict[str, str]] = None
    monthInterval: Optional[int] = None


class FHIRRecurrenceTemplate(BaseModel):
    recurrenceType: Optional[FHIRCodeableConcept] = None
    timezone: Optional[FHIRCodeableConcept] = None
    lastOccurrenceDate: Optional[str] = None
    occurrenceCount: Optional[int] = None
    occurrenceDates: Optional[List[str]] = None
    excludingDate: Optional[List[str]] = None
    excludingRecurrenceId: Optional[List[int]] = None
    weeklyTemplate: Optional[FHIRRecurrenceWeeklyTemplate] = None
    monthlyTemplate: Optional[FHIRRecurrenceMonthlyTemplate] = None
    yearlyTemplate: Optional[Dict[str, int]] = None


class FHIRAppointmentSchema(BaseModel):
    resourceType: str = Field("Appointment", description="Always 'Appointment'.")
    id: str = Field(..., description="Public appointment_id as a string.")
    status: str = Field(..., description="proposed | pending | booked | arrived | fulfilled | cancelled | noshow | etc.")
    subject: Optional[FHIRReference] = None
    encounter: Optional[FHIRReference] = None
    start: Optional[str] = None
    end: Optional[str] = None
    minutesDuration: Optional[int] = None
    created: Optional[str] = None
    description: Optional[str] = None
    patientInstruction: Optional[str] = None
    comment: Optional[str] = None
    priority: Optional[int] = Field(None, description="Unsigned integer — 0 = not prioritized.")
    cancellationReason: Optional[Dict[str, str]] = None
    cancellationDate: Optional[str] = None
    serviceCategory: Optional[List[FHIRCodeableConcept]] = None
    serviceType: Optional[List[FHIRCodeableConcept]] = None
    specialty: Optional[List[FHIRCodeableConcept]] = None
    appointmentType: Optional[FHIRCodeableConcept] = None
    reasonCode: Optional[List[FHIRAppointmentReasonCode]] = None
    participant: List[FHIRAppointmentParticipant] = Field(..., description="At least one participant is required.")
    recurrenceId: Optional[int] = None
    occurrenceChanged: Optional[bool] = None
    recurrenceTemplate: Optional[FHIRRecurrenceTemplate] = None


class FHIRAppointmentBundleEntry(BaseModel):
    resource: FHIRAppointmentSchema


class FHIRAppointmentBundle(FHIRBundle):
    entry: Optional[List[FHIRAppointmentBundleEntry]] = None


# ── Plain (snake_case) sub-types ──────────────────────────────────────────────


class PlainAppointmentParticipant(BaseModel):
    actor_type: Optional[str] = Field(None, description="e.g. 'Practitioner' | 'Patient'")
    actor_id: Optional[int] = None
    actor_display: Optional[str] = None
    type_code: Optional[str] = None
    type_display: Optional[str] = None
    type_text: Optional[str] = None
    required: Optional[str] = Field(None, description="required | optional | information-only")
    status: Optional[str] = Field(None, description="accepted | declined | tentative | needs-action")
    period_start: Optional[str] = Field(None, description="ISO 8601 datetime string.")
    period_end: Optional[str] = Field(None, description="ISO 8601 datetime string.")


class PlainWeeklyTemplate(BaseModel):
    monday: Optional[bool] = None
    tuesday: Optional[bool] = None
    wednesday: Optional[bool] = None
    thursday: Optional[bool] = None
    friday: Optional[bool] = None
    saturday: Optional[bool] = None
    sunday: Optional[bool] = None
    week_interval: Optional[int] = None


class PlainMonthlyTemplate(BaseModel):
    day_of_month: Optional[int] = None
    nth_week_code: Optional[str] = None
    nth_week_display: Optional[str] = None
    day_of_week_code: Optional[str] = None
    day_of_week_display: Optional[str] = None
    month_interval: Optional[int] = None


class PlainYearlyTemplate(BaseModel):
    year_interval: Optional[int] = None


class PlainRecurrenceTemplate(BaseModel):
    recurrence_type_code: Optional[str] = None
    recurrence_type_display: Optional[str] = None
    recurrence_type_system: Optional[str] = None
    timezone_code: Optional[str] = None
    timezone_display: Optional[str] = None
    last_occurrence_date: Optional[str] = Field(None, description="ISO 8601 date string.")
    occurrence_count: Optional[int] = None
    occurrence_dates: Optional[List[str]] = None
    excluding_dates: Optional[List[str]] = None
    excluding_recurrence_ids: Optional[List[int]] = None
    weekly_template: Optional[PlainWeeklyTemplate] = None
    monthly_template: Optional[PlainMonthlyTemplate] = None
    yearly_template: Optional[PlainYearlyTemplate] = None


# ── Plain Appointment response ────────────────────────────────────────────────


class PlainAppointmentResponse(BaseModel):
    id: int = Field(..., description="Public appointment_id.")
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    status: Optional[str] = Field(None, description="proposed | pending | booked | arrived | fulfilled | cancelled | noshow | etc.")
    subject_type: Optional[str] = Field(None, description="e.g. 'Patient'")
    subject_id: Optional[int] = None
    subject_display: Optional[str] = None
    encounter_id: Optional[int] = Field(None, description="Public encounter_id of the linked Encounter.")
    start: Optional[str] = Field(None, description="ISO 8601 datetime string.")
    end: Optional[str] = Field(None, description="ISO 8601 datetime string.")
    minutes_duration: Optional[int] = None
    created: Optional[str] = Field(None, description="ISO 8601 datetime string.")
    description: Optional[str] = None
    comment: Optional[str] = None
    patient_instruction: Optional[str] = None
    priority: Optional[int] = Field(None, description="Unsigned integer — 0 = not prioritized.")
    cancellation_reason: Optional[str] = None
    cancellation_date: Optional[str] = Field(None, description="ISO 8601 date string.")
    service_category_code: Optional[str] = None
    service_category_display: Optional[str] = None
    service_type_code: Optional[str] = None
    service_type_display: Optional[str] = None
    specialty_code: Optional[str] = None
    specialty_display: Optional[str] = None
    appointment_type_code: Optional[str] = None
    appointment_type_display: Optional[str] = None
    recurrence_id: Optional[int] = None
    occurrence_changed: Optional[bool] = None
    reason_code: Optional[List[PlainReasonCode]] = None
    participant: Optional[List[PlainAppointmentParticipant]] = None
    recurrence_template: Optional[PlainRecurrenceTemplate] = None


# ── Paginated response ────────────────────────────────────────────────────────


class PaginatedAppointmentResponse(BaseModel):
    total: int = Field(..., description="Total number of matching appointments.")
    limit: int = Field(..., description="Page size requested.")
    offset: int = Field(..., description="Number of records skipped.")
    data: List[PlainAppointmentResponse] = Field(..., description="Array of plain-JSON Appointment objects.")
