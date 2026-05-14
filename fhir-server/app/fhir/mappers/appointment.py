from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.appointment.appointment import AppointmentModel


def to_fhir_appointment(appointment: "AppointmentModel") -> dict:
    """
    Convert AppointmentModel (with relationships loaded) to a FHIR R4 Appointment dict.

    Rules:
      - Uses appointment_id (public) as the FHIR logical id — never the internal PK.
      - priority is an unsignedInt in FHIR R4 (not an object).
      - subject and participant actor are reconstructed from stored type enum + public ID.
      - None / empty values are stripped from the output.
    """
    result: dict = {
        "resourceType": "Appointment",
        "id": str(appointment.appointment_id),
        "status": appointment.status,
    }

    # subject
    if appointment.subject_type and appointment.subject_id:
        subject: dict = {
            "reference": f"{appointment.subject_type.value}/{appointment.subject_id}"
        }
        if appointment.subject_display:
            subject["display"] = appointment.subject_display
        result["subject"] = subject

    # encounter (loaded via relationship → use public encounter_id)
    if appointment.encounter and appointment.encounter.encounter_id:
        result["encounter"] = {
            "reference": f"Encounter/{appointment.encounter.encounter_id}"
        }

    if appointment.start:
        result["start"] = appointment.start.isoformat()
    if appointment.end:
        result["end"] = appointment.end.isoformat()
    if appointment.minutes_duration is not None:
        result["minutesDuration"] = appointment.minutes_duration
    if appointment.created:
        result["created"] = appointment.created.isoformat()
    if appointment.description:
        result["description"] = appointment.description
    if appointment.patient_instruction:
        result["patientInstruction"] = appointment.patient_instruction
    if appointment.comment:
        result["comment"] = appointment.comment
    if appointment.priority_value is not None:
        result["priority"] = appointment.priority_value  # R4: unsignedInt

    # cancellation
    if appointment.cancellation_reason:
        result["cancellationReason"] = {"text": appointment.cancellation_reason}
    if appointment.cancellation_date:
        result["cancellationDate"] = appointment.cancellation_date.isoformat()

    # Coded concept fields
    if appointment.service_category_code:
        coding = {k: v for k, v in {
            "code": appointment.service_category_code,
            "display": appointment.service_category_display,
        }.items() if v}
        result["serviceCategory"] = [{"coding": [coding]}]

    if appointment.service_type_code:
        coding = {k: v for k, v in {
            "code": appointment.service_type_code,
            "display": appointment.service_type_display,
        }.items() if v}
        result["serviceType"] = [{"coding": [coding]}]

    if appointment.specialty_code:
        coding = {k: v for k, v in {
            "code": appointment.specialty_code,
            "display": appointment.specialty_display,
        }.items() if v}
        result["specialty"] = [{"coding": [coding]}]

    if appointment.appointment_type_code:
        coding = {k: v for k, v in {
            "code": appointment.appointment_type_code,
            "display": appointment.appointment_type_display,
        }.items() if v}
        result["appointmentType"] = {"coding": [coding]}

    # reasonCode (FHIR R4)
    if appointment.reason_codes:
        reason_list = []
        for r in appointment.reason_codes:
            entry: dict = {}
            coding = {k: v for k, v in {
                "system": r.coding_system,
                "code": r.coding_code,
                "display": r.coding_display,
            }.items() if v}
            if coding:
                entry["coding"] = [coding]
            if r.text:
                entry["text"] = r.text
            if entry:
                reason_list.append(entry)
        if reason_list:
            result["reasonCode"] = reason_list

    # participant (required by FHIR spec)
    participant_list = []
    for p in appointment.participants:
        entry: dict = {"status": p.status}

        if p.actor_reference_type and p.actor_reference_id:
            actor: dict = {
                "reference": f"{p.actor_reference_type.value}/{p.actor_reference_id}"
            }
            if p.actor_display:
                actor["display"] = p.actor_display
            entry["actor"] = actor

        if p.type_code or p.type_text:
            type_entry: dict = {}
            if p.type_code:
                type_entry["coding"] = [{k: v for k, v in {
                    "code": p.type_code,
                    "display": p.type_display,
                }.items() if v}]
            if p.type_text:
                type_entry["text"] = p.type_text
            entry["type"] = [type_entry]

        if p.required:
            entry["required"] = p.required

        if p.period_start or p.period_end:
            period: dict = {}
            if p.period_start:
                period["start"] = p.period_start.isoformat()
            if p.period_end:
                period["end"] = p.period_end.isoformat()
            entry["period"] = period

        participant_list.append(entry)

    result["participant"] = participant_list

    # recurrenceId / occurrenceChanged (on the instance, not the template)
    if appointment.recurrence_id is not None:
        result["recurrenceId"] = appointment.recurrence_id
    if appointment.occurrence_changed is not None:
        result["occurrenceChanged"] = appointment.occurrence_changed

    # recurrenceTemplate
    rt = appointment.recurrence_template
    if rt:
        rt_data: dict = {
            "recurrenceType": {
                "coding": [{k: v for k, v in {
                    "system": rt.recurrence_type_system,
                    "code": rt.recurrence_type_code,
                    "display": rt.recurrence_type_display,
                }.items() if v}]
            }
        }

        if rt.timezone_code:
            rt_data["timezone"] = {"coding": [{k: v for k, v in {
                "code": rt.timezone_code,
                "display": rt.timezone_display,
            }.items() if v}]}

        if rt.last_occurrence_date:
            rt_data["lastOccurrenceDate"] = rt.last_occurrence_date.isoformat()
        if rt.occurrence_count is not None:
            rt_data["occurrenceCount"] = rt.occurrence_count
        if rt.occurrence_dates:
            rt_data["occurrenceDates"] = [d for d in rt.occurrence_dates.split(",") if d]
        if rt.excluding_dates:
            rt_data["excludingDate"] = [d for d in rt.excluding_dates.split(",") if d]
        if rt.excluding_recurrence_ids:
            rt_data["excludingRecurrenceId"] = [
                int(i) for i in rt.excluding_recurrence_ids.split(",") if i
            ]

        weekly_fields = {
            "monday": rt.weekly_monday,
            "tuesday": rt.weekly_tuesday,
            "wednesday": rt.weekly_wednesday,
            "thursday": rt.weekly_thursday,
            "friday": rt.weekly_friday,
            "saturday": rt.weekly_saturday,
            "sunday": rt.weekly_sunday,
        }
        weekly = {k: v for k, v in weekly_fields.items() if v is not None}
        if rt.weekly_week_interval is not None:
            weekly["weekInterval"] = rt.weekly_week_interval
        if weekly:
            rt_data["weeklyTemplate"] = weekly

        if rt.monthly_month_interval is not None:
            monthly: dict = {"monthInterval": rt.monthly_month_interval}
            if rt.monthly_day_of_month is not None:
                monthly["dayOfMonth"] = rt.monthly_day_of_month
            if rt.monthly_nth_week_code:
                monthly["nthWeekOfMonth"] = {k: v for k, v in {
                    "code": rt.monthly_nth_week_code,
                    "display": rt.monthly_nth_week_display,
                }.items() if v}
            if rt.monthly_day_of_week_code:
                monthly["dayOfWeek"] = {k: v for k, v in {
                    "code": rt.monthly_day_of_week_code,
                    "display": rt.monthly_day_of_week_display,
                }.items() if v}
            rt_data["monthlyTemplate"] = monthly

        if rt.yearly_year_interval is not None:
            rt_data["yearlyTemplate"] = {"yearInterval": rt.yearly_year_interval}

        result["recurrenceTemplate"] = rt_data

    return {k: v for k, v in result.items() if v is not None}


def to_plain_appointment(appointment: "AppointmentModel") -> dict:
    """
    Return the appointment as a flat snake_case JSON object — no FHIR conventions.
    Uses public appointment_id as `id`.
    """
    result: dict = {
        "id": appointment.appointment_id,
        "user_id": appointment.user_id,
        "org_id": appointment.org_id,
        "status": appointment.status.value if appointment.status else None,
        "subject_type": appointment.subject_type.value if appointment.subject_type else None,
        "subject_id": appointment.subject_id,
        "subject_display": appointment.subject_display,
        "encounter_id": (
            appointment.encounter.encounter_id
            if appointment.encounter and appointment.encounter.encounter_id
            else None
        ),
        "start": appointment.start.isoformat() if appointment.start else None,
        "end": appointment.end.isoformat() if appointment.end else None,
        "minutes_duration": appointment.minutes_duration,
        "created": appointment.created.isoformat() if appointment.created else None,
        "description": appointment.description,
        "comment": appointment.comment,
        "patient_instruction": appointment.patient_instruction,
        "priority": appointment.priority_value,
        "cancellation_reason": appointment.cancellation_reason,
        "cancellation_date": appointment.cancellation_date.isoformat() if appointment.cancellation_date else None,
        "service_category_code": appointment.service_category_code,
        "service_category_display": appointment.service_category_display,
        "service_type_code": appointment.service_type_code,
        "service_type_display": appointment.service_type_display,
        "specialty_code": appointment.specialty_code,
        "specialty_display": appointment.specialty_display,
        "appointment_type_code": appointment.appointment_type_code,
        "appointment_type_display": appointment.appointment_type_display,
        "recurrence_id": appointment.recurrence_id,
        "occurrence_changed": appointment.occurrence_changed,
    }

    if appointment.reason_codes:
        result["reason_code"] = [
            {
                "coding_system": r.coding_system,
                "coding_code": r.coding_code,
                "coding_display": r.coding_display,
                "text": r.text,
            }
            for r in appointment.reason_codes
        ]

    if appointment.participants:
        result["participant"] = [
            {
                "actor_type": p.actor_reference_type.value if p.actor_reference_type else None,
                "actor_id": p.actor_reference_id,
                "actor_display": p.actor_display,
                "type_code": p.type_code,
                "type_display": p.type_display,
                "type_text": p.type_text,
                "required": p.required,
                "status": p.status,
                "period_start": p.period_start.isoformat() if p.period_start else None,
                "period_end": p.period_end.isoformat() if p.period_end else None,
            }
            for p in appointment.participants
        ]

    rt = appointment.recurrence_template
    if rt:
        rt_plain: dict = {
            "recurrence_type_code": rt.recurrence_type_code,
            "recurrence_type_display": rt.recurrence_type_display,
            "recurrence_type_system": rt.recurrence_type_system,
            "timezone_code": rt.timezone_code,
            "timezone_display": rt.timezone_display,
            "last_occurrence_date": rt.last_occurrence_date.isoformat() if rt.last_occurrence_date else None,
            "occurrence_count": rt.occurrence_count,
            "occurrence_dates": [d for d in rt.occurrence_dates.split(",") if d] if rt.occurrence_dates else None,
            "excluding_dates": [d for d in rt.excluding_dates.split(",") if d] if rt.excluding_dates else None,
            "excluding_recurrence_ids": (
                [int(i) for i in rt.excluding_recurrence_ids.split(",") if i]
                if rt.excluding_recurrence_ids else None
            ),
        }

        weekly_fields = {k: v for k, v in {
            "monday": rt.weekly_monday,
            "tuesday": rt.weekly_tuesday,
            "wednesday": rt.weekly_wednesday,
            "thursday": rt.weekly_thursday,
            "friday": rt.weekly_friday,
            "saturday": rt.weekly_saturday,
            "sunday": rt.weekly_sunday,
            "week_interval": rt.weekly_week_interval,
        }.items() if v is not None}
        rt_plain["weekly_template"] = weekly_fields if weekly_fields else None

        monthly_fields = {k: v for k, v in {
            "day_of_month": rt.monthly_day_of_month,
            "nth_week_code": rt.monthly_nth_week_code,
            "nth_week_display": rt.monthly_nth_week_display,
            "day_of_week_code": rt.monthly_day_of_week_code,
            "day_of_week_display": rt.monthly_day_of_week_display,
            "month_interval": rt.monthly_month_interval,
        }.items() if v is not None}
        rt_plain["monthly_template"] = monthly_fields if monthly_fields else None

        rt_plain["yearly_template"] = (
            {"year_interval": rt.yearly_year_interval}
            if rt.yearly_year_interval is not None else None
        )

        result["recurrence_template"] = {k: v for k, v in rt_plain.items() if v is not None}

    return {k: v for k, v in result.items() if v is not None}
