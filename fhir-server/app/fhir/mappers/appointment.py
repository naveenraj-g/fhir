from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.appointment.appointment import AppointmentModel


def _cc(system, code, display, text) -> dict | None:
    """Build a CodeableConcept dict; return None if all fields are empty."""
    coding = {k: v for k, v in {"system": system, "code": code, "display": display}.items() if v}
    result: dict = {}
    if coding:
        result["coding"] = [coding]
    if text:
        result["text"] = text
    return result if result else None


def to_fhir_appointment(appointment: "AppointmentModel") -> dict:
    result: dict = {
        "resourceType": "Appointment",
        "id": str(appointment.appointment_id),
        "status": appointment.status.value if hasattr(appointment.status, "value") else appointment.status,
    }

    # identifier
    if appointment.identifiers:
        id_list = []
        for i in appointment.identifiers:
            entry: dict = {}
            if i.use:
                entry["use"] = i.use
            type_cc = _cc(i.type_system, i.type_code, i.type_display, i.type_text)
            if type_cc:
                entry["type"] = type_cc
            if i.system:
                entry["system"] = i.system
            if i.value:
                entry["value"] = i.value
            if i.period_start or i.period_end:
                entry["period"] = {k: v for k, v in {
                    "start": i.period_start.isoformat() if i.period_start else None,
                    "end": i.period_end.isoformat() if i.period_end else None,
                }.items() if v}
            if i.assigner:
                entry["assigner"] = {"display": i.assigner}
            if entry:
                id_list.append(entry)
        if id_list:
            result["identifier"] = id_list

    # cancelationReason (R4: single 'l')
    cancelation_cc = _cc(
        appointment.cancelation_reason_system,
        appointment.cancelation_reason_code,
        appointment.cancelation_reason_display,
        appointment.cancelation_reason_text,
    )
    if cancelation_cc:
        result["cancelationReason"] = cancelation_cc

    # serviceCategory
    if appointment.service_categories:
        result["serviceCategory"] = [
            cc for sc in appointment.service_categories
            if (cc := _cc(sc.coding_system, sc.coding_code, sc.coding_display, sc.text))
        ]

    # serviceType
    if appointment.service_types:
        result["serviceType"] = [
            cc for st in appointment.service_types
            if (cc := _cc(st.coding_system, st.coding_code, st.coding_display, st.text))
        ]

    # specialty
    if appointment.specialties:
        result["specialty"] = [
            cc for sp in appointment.specialties
            if (cc := _cc(sp.coding_system, sp.coding_code, sp.coding_display, sp.text))
        ]

    # appointmentType
    appt_type_cc = _cc(
        appointment.appointment_type_system,
        appointment.appointment_type_code,
        appointment.appointment_type_display,
        appointment.appointment_type_text,
    )
    if appt_type_cc:
        result["appointmentType"] = appt_type_cc

    # reasonCode
    if appointment.reason_codes:
        result["reasonCode"] = [
            cc for rc in appointment.reason_codes
            if (cc := _cc(rc.coding_system, rc.coding_code, rc.coding_display, rc.text))
        ]

    # reasonReference
    if appointment.reason_references:
        refs = []
        for rr in appointment.reason_references:
            if rr.reference_type and rr.reference_id:
                ref: dict = {"reference": f"{rr.reference_type}/{rr.reference_id}"}
                if rr.reference_display:
                    ref["display"] = rr.reference_display
                refs.append(ref)
        if refs:
            result["reasonReference"] = refs

    # supportingInformation
    if appointment.supporting_informations:
        refs = []
        for si in appointment.supporting_informations:
            if si.reference_type and si.reference_id:
                ref = {"reference": f"{si.reference_type}/{si.reference_id}"}
                if si.reference_display:
                    ref["display"] = si.reference_display
                refs.append(ref)
        if refs:
            result["supportingInformation"] = refs

    if appointment.priority_value is not None:
        result["priority"] = appointment.priority_value

    if appointment.description:
        result["description"] = appointment.description

    # slot
    if appointment.slots:
        result["slot"] = [
            {k: v for k, v in {
                "reference": f"Slot/{s.slot_id}" if s.slot_id else None,
                "display": s.slot_display,
            }.items() if v}
            for s in appointment.slots
        ]

    # basedOn
    if appointment.based_ons:
        result["basedOn"] = [
            {k: v for k, v in {
                "reference": f"ServiceRequest/{b.service_request_id}" if b.service_request_id else None,
                "display": b.service_request_display,
            }.items() if v}
            for b in appointment.based_ons
        ]

    if appointment.created:
        result["created"] = appointment.created.isoformat()
    if appointment.comment:
        result["comment"] = appointment.comment
    if appointment.patient_instruction:
        result["patientInstruction"] = appointment.patient_instruction

    # subject
    if appointment.subject_type and appointment.subject_id:
        subj: dict = {"reference": f"{appointment.subject_type.value}/{appointment.subject_id}"}
        if appointment.subject_display:
            subj["display"] = appointment.subject_display
        result["subject"] = subj

    # encounter
    if appointment.encounter and appointment.encounter.encounter_id:
        result["encounter"] = {"reference": f"Encounter/{appointment.encounter.encounter_id}"}

    if appointment.start:
        result["start"] = appointment.start.isoformat()
    if appointment.end:
        result["end"] = appointment.end.isoformat()
    if appointment.minutes_duration is not None:
        result["minutesDuration"] = appointment.minutes_duration

    # requestedPeriod
    if appointment.requested_periods:
        periods = []
        for rp in appointment.requested_periods:
            period = {k: v for k, v in {
                "start": rp.period_start.isoformat() if rp.period_start else None,
                "end": rp.period_end.isoformat() if rp.period_end else None,
            }.items() if v}
            if period:
                periods.append(period)
        if periods:
            result["requestedPeriod"] = periods

    # participant (1..*)
    participant_list = []
    for p in appointment.participants:
        entry: dict = {"status": p.status}

        if p.types:
            type_list = []
            for t in p.types:
                cc = _cc(t.coding_system, t.coding_code, t.coding_display, t.text)
                if cc:
                    type_list.append(cc)
            if type_list:
                entry["type"] = type_list

        if p.actor_type and p.actor_id:
            actor: dict = {
                "reference": f"{p.actor_type.value}/{p.actor_id}"
            }
            if p.actor_display:
                actor["display"] = p.actor_display
            entry["actor"] = actor

        if p.required:
            entry["required"] = p.required

        if p.period_start or p.period_end:
            entry["period"] = {k: v for k, v in {
                "start": p.period_start.isoformat() if p.period_start else None,
                "end": p.period_end.isoformat() if p.period_end else None,
            }.items() if v}

        participant_list.append(entry)
    result["participant"] = participant_list

    # recurrenceTemplate (operational extension)
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
            rt_data["excludingRecurrenceId"] = [int(i) for i in rt.excluding_recurrence_ids.split(",") if i]

        weekly = {k: v for k, v in {
            "monday": rt.weekly_monday, "tuesday": rt.weekly_tuesday,
            "wednesday": rt.weekly_wednesday, "thursday": rt.weekly_thursday,
            "friday": rt.weekly_friday, "saturday": rt.weekly_saturday,
            "sunday": rt.weekly_sunday,
        }.items() if v is not None}
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
                    "code": rt.monthly_nth_week_code, "display": rt.monthly_nth_week_display,
                }.items() if v}
            if rt.monthly_day_of_week_code:
                monthly["dayOfWeek"] = {k: v for k, v in {
                    "code": rt.monthly_day_of_week_code, "display": rt.monthly_day_of_week_display,
                }.items() if v}
            rt_data["monthlyTemplate"] = monthly

        if rt.yearly_year_interval is not None:
            rt_data["yearlyTemplate"] = {"yearInterval": rt.yearly_year_interval}

        result["recurrenceTemplate"] = rt_data

    return {k: v for k, v in result.items() if v is not None}


def to_plain_appointment(appointment: "AppointmentModel") -> dict:
    result: dict = {
        "id": appointment.appointment_id,
        "user_id": appointment.user_id,
        "org_id": appointment.org_id,
        "status": appointment.status.value if hasattr(appointment.status, "value") else appointment.status,
        "cancelation_reason_system": appointment.cancelation_reason_system,
        "cancelation_reason_code": appointment.cancelation_reason_code,
        "cancelation_reason_display": appointment.cancelation_reason_display,
        "cancelation_reason_text": appointment.cancelation_reason_text,
        "appointment_type_system": appointment.appointment_type_system,
        "appointment_type_code": appointment.appointment_type_code,
        "appointment_type_display": appointment.appointment_type_display,
        "appointment_type_text": appointment.appointment_type_text,
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
        "priority_value": appointment.priority_value,
        "created_at": appointment.created_at.isoformat() if appointment.created_at else None,
        "updated_at": appointment.updated_at.isoformat() if appointment.updated_at else None,
        "created_by": appointment.created_by,
        "updated_by": appointment.updated_by,
    }

    if appointment.identifiers:
        result["identifier"] = [
            {
                "use": i.use,
                "type_system": i.type_system,
                "type_code": i.type_code,
                "type_display": i.type_display,
                "type_text": i.type_text,
                "system": i.system,
                "value": i.value,
                "period_start": i.period_start.isoformat() if i.period_start else None,
                "period_end": i.period_end.isoformat() if i.period_end else None,
                "assigner": i.assigner,
            }
            for i in appointment.identifiers
        ]

    if appointment.service_categories:
        result["service_category"] = [
            {"coding_system": sc.coding_system, "coding_code": sc.coding_code,
             "coding_display": sc.coding_display, "text": sc.text}
            for sc in appointment.service_categories
        ]

    if appointment.service_types:
        result["service_type"] = [
            {"coding_system": st.coding_system, "coding_code": st.coding_code,
             "coding_display": st.coding_display, "text": st.text}
            for st in appointment.service_types
        ]

    if appointment.specialties:
        result["specialty"] = [
            {"coding_system": sp.coding_system, "coding_code": sp.coding_code,
             "coding_display": sp.coding_display, "text": sp.text}
            for sp in appointment.specialties
        ]

    if appointment.reason_codes:
        result["reason_code"] = [
            {"coding_system": rc.coding_system, "coding_code": rc.coding_code,
             "coding_display": rc.coding_display, "text": rc.text}
            for rc in appointment.reason_codes
        ]

    if appointment.reason_references:
        result["reason_reference"] = [
            {"reference_type": rr.reference_type, "reference_id": rr.reference_id,
             "reference_display": rr.reference_display}
            for rr in appointment.reason_references
        ]

    if appointment.supporting_informations:
        result["supporting_information"] = [
            {"reference_type": si.reference_type, "reference_id": si.reference_id,
             "reference_display": si.reference_display}
            for si in appointment.supporting_informations
        ]

    if appointment.slots:
        result["slot"] = [
            {"slot_id": s.slot_id, "slot_display": s.slot_display}
            for s in appointment.slots
        ]

    if appointment.based_ons:
        result["based_on"] = [
            {"service_request_id": b.service_request_id, "service_request_display": b.service_request_display}
            for b in appointment.based_ons
        ]

    if appointment.participants:
        result["participant"] = []
        for p in appointment.participants:
            entry = {
                "actor_type": p.actor_type.value if p.actor_type else None,
                "actor_id": p.actor_id,
                "actor_display": p.actor_display,
                "required": p.required,
                "status": p.status,
                "period_start": p.period_start.isoformat() if p.period_start else None,
                "period_end": p.period_end.isoformat() if p.period_end else None,
            }
            if p.types:
                entry["types"] = [
                    {"coding_system": t.coding_system, "coding_code": t.coding_code,
                     "coding_display": t.coding_display, "text": t.text}
                    for t in p.types
                ]
            result["participant"].append(entry)

    if appointment.requested_periods:
        result["requested_period"] = [
            {
                "period_start": rp.period_start.isoformat() if rp.period_start else None,
                "period_end": rp.period_end.isoformat() if rp.period_end else None,
            }
            for rp in appointment.requested_periods
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

        weekly = {k: v for k, v in {
            "monday": rt.weekly_monday, "tuesday": rt.weekly_tuesday,
            "wednesday": rt.weekly_wednesday, "thursday": rt.weekly_thursday,
            "friday": rt.weekly_friday, "saturday": rt.weekly_saturday,
            "sunday": rt.weekly_sunday, "week_interval": rt.weekly_week_interval,
        }.items() if v is not None}
        rt_plain["weekly_template"] = weekly if weekly else None

        monthly = {k: v for k, v in {
            "day_of_month": rt.monthly_day_of_month,
            "nth_week_code": rt.monthly_nth_week_code,
            "nth_week_display": rt.monthly_nth_week_display,
            "day_of_week_code": rt.monthly_day_of_week_code,
            "day_of_week_display": rt.monthly_day_of_week_display,
            "month_interval": rt.monthly_month_interval,
        }.items() if v is not None}
        rt_plain["monthly_template"] = monthly if monthly else None

        rt_plain["yearly_template"] = (
            {"year_interval": rt.yearly_year_interval} if rt.yearly_year_interval is not None else None
        )

        result["recurrence_template"] = {k: v for k, v in rt_plain.items() if v is not None}

    return {k: v for k, v in result.items() if v is not None}
