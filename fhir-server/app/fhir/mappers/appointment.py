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

    # cancellationReason (R5 double-'l')
    cancelation_cc = _cc(
        appointment.cancelation_reason_system,
        appointment.cancelation_reason_code,
        appointment.cancelation_reason_display,
        appointment.cancelation_reason_text,
    )
    if cancelation_cc:
        result["cancellationReason"] = cancelation_cc

    if appointment.cancellation_date:
        result["cancellationDate"] = appointment.cancellation_date.isoformat()

    # class
    if appointment.classes:
        result["class"] = [
            cc for cls in appointment.classes
            if (cc := _cc(cls.coding_system, cls.coding_code, cls.coding_display, cls.text))
        ]

    # serviceCategory
    if appointment.service_categories:
        result["serviceCategory"] = [
            cc for sc in appointment.service_categories
            if (cc := _cc(sc.coding_system, sc.coding_code, sc.coding_display, sc.text))
        ]

    # serviceType (CodeableReference)
    if appointment.service_types:
        st_list = []
        for st in appointment.service_types:
            entry = {}
            concept = _cc(st.coding_system, st.coding_code, st.coding_display, st.text)
            if concept:
                entry["concept"] = concept
            if st.reference_type and st.reference_id:
                ref = {"reference": f"{st.reference_type.value}/{st.reference_id}"}
                if st.reference_display:
                    ref["display"] = st.reference_display
                entry["reference"] = ref
            if entry:
                st_list.append(entry)
        if st_list:
            result["serviceType"] = st_list

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

    # reason (0..*) CodeableReference — R5
    if appointment.reasons:
        reason_list = []
        for r in appointment.reasons:
            entry = {}
            concept = _cc(r.coding_system, r.coding_code, r.coding_display, r.text)
            if concept:
                entry["concept"] = concept
            if r.reference_type and r.reference_id:
                ref = {"reference": f"{r.reference_type.value}/{r.reference_id}"}
                if r.reference_display:
                    ref["display"] = r.reference_display
                entry["reference"] = ref
            if entry:
                reason_list.append(entry)
        if reason_list:
            result["reason"] = reason_list

    # priority (0..1 CodeableConcept) — R5
    priority_cc = _cc(
        appointment.priority_system,
        appointment.priority_code,
        appointment.priority_display,
        appointment.priority_text,
    )
    if priority_cc:
        result["priority"] = priority_cc

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

    if appointment.description:
        result["description"] = appointment.description

    # replaces (0..*) — R5 new
    if appointment.replaces_list:
        result["replaces"] = [
            {k: v for k, v in {
                "reference": f"{r.reference_type.value}/{r.reference_id}" if r.reference_type and r.reference_id else None,
                "display": r.reference_display,
            }.items() if v}
            for r in appointment.replaces_list
        ]

    # virtualService (0..*) — R5 new
    if appointment.virtual_services:
        vs_list = []
        for vs in appointment.virtual_services:
            entry = {}
            if vs.channel_type_code or vs.channel_type_system or vs.channel_type_display:
                coding = {k: v for k, v in {
                    "system": vs.channel_type_system,
                    "code": vs.channel_type_code,
                    "display": vs.channel_type_display,
                }.items() if v}
                if coding:
                    entry["channelType"] = coding
            if vs.address_url:
                entry["addressUrl"] = vs.address_url
            if vs.additional_info:
                entry["additionalInfo"] = [u for u in vs.additional_info.split(",") if u]
            if vs.max_participants is not None:
                entry["maxParticipants"] = vs.max_participants
            if vs.session_key:
                entry["sessionKey"] = vs.session_key
            if entry:
                vs_list.append(entry)
        if vs_list:
            result["virtualService"] = vs_list

    # previousAppointment (0..1) — R5 new
    if appointment.previous_appointment_id:
        prev: dict = {"reference": f"Appointment/{appointment.previous_appointment_id}"}
        if appointment.previous_appointment_display:
            prev["display"] = appointment.previous_appointment_display
        result["previousAppointment"] = prev

    # originatingAppointment (0..1) — R5 new
    if appointment.originating_appointment_id:
        orig: dict = {"reference": f"Appointment/{appointment.originating_appointment_id}"}
        if appointment.originating_appointment_display:
            orig["display"] = appointment.originating_appointment_display
        result["originatingAppointment"] = orig

    # slot
    if appointment.slots:
        result["slot"] = [
            {k: v for k, v in {
                "reference": f"{s.reference_type.value}/{s.reference_id}" if s.reference_type and s.reference_id else None,
                "display": s.reference_display,
            }.items() if v}
            for s in appointment.slots
        ]

    # account (0..*) — R5 new
    if appointment.accounts:
        result["account"] = [
            {k: v for k, v in {
                "reference": f"{a.reference_type.value}/{a.reference_id}" if a.reference_type and a.reference_id else None,
                "display": a.reference_display,
            }.items() if v}
            for a in appointment.accounts
        ]

    # basedOn
    if appointment.based_ons:
        result["basedOn"] = [
            {k: v for k, v in {
                "reference": f"{b.reference_type.value}/{b.reference_id}" if b.reference_type and b.reference_id else None,
                "display": b.reference_display,
            }.items() if v}
            for b in appointment.based_ons
        ]

    if appointment.created:
        result["created"] = appointment.created.isoformat()

    # note (0..*) Annotation — R5
    if appointment.notes:
        note_list = []
        for n in appointment.notes:
            entry = {"text": n.text}
            if n.author_string:
                entry["authorString"] = n.author_string
            elif n.author_reference_type and n.author_reference_id:
                ref = {"reference": f"{n.author_reference_type}/{n.author_reference_id}"}
                if n.author_reference_display:
                    ref["display"] = n.author_reference_display
                entry["authorReference"] = ref
            if n.time:
                entry["time"] = n.time.isoformat()
            note_list.append(entry)
        if note_list:
            result["note"] = note_list

    # patientInstruction (0..*) CodeableReference — R5
    if appointment.patient_instructions:
        pi_list = []
        for pi in appointment.patient_instructions:
            entry = {}
            concept = _cc(pi.coding_system, pi.coding_code, pi.coding_display, pi.text)
            if concept:
                entry["concept"] = concept
            if pi.reference_type and pi.reference_id:
                ref = {"reference": f"{pi.reference_type.value}/{pi.reference_id}"}
                if pi.reference_display:
                    ref["display"] = pi.reference_display
                entry["reference"] = ref
            if entry:
                pi_list.append(entry)
        if pi_list:
            result["patientInstruction"] = pi_list

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

        if p.reference_type and p.reference_id:
            actor: dict = {
                "reference": f"{p.reference_type.value}/{p.reference_id}"
            }
            if p.reference_display:
                actor["display"] = p.reference_display
            entry["actor"] = actor

        if p.required is not None:
            entry["required"] = p.required

        if p.period_start or p.period_end:
            entry["period"] = {k: v for k, v in {
                "start": p.period_start.isoformat() if p.period_start else None,
                "end": p.period_end.isoformat() if p.period_end else None,
            }.items() if v}

        participant_list.append(entry)
    result["participant"] = participant_list

    if appointment.recurrence_id is not None:
        result["recurrenceId"] = appointment.recurrence_id
    if appointment.occurrence_changed is not None:
        result["occurrenceChanged"] = appointment.occurrence_changed

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
        "cancellation_date": appointment.cancellation_date.isoformat() if appointment.cancellation_date else None,
        "appointment_type_system": appointment.appointment_type_system,
        "appointment_type_code": appointment.appointment_type_code,
        "appointment_type_display": appointment.appointment_type_display,
        "appointment_type_text": appointment.appointment_type_text,
        "priority_system": appointment.priority_system,
        "priority_code": appointment.priority_code,
        "priority_display": appointment.priority_display,
        "priority_text": appointment.priority_text,
        "subject_type": appointment.subject_type.value if appointment.subject_type else None,
        "subject_id": appointment.subject_id,
        "subject_display": appointment.subject_display,
        "encounter_id": (
            appointment.encounter.encounter_id
            if appointment.encounter and appointment.encounter.encounter_id
            else None
        ),
        "previous_appointment_id": appointment.previous_appointment_id,
        "previous_appointment_display": appointment.previous_appointment_display,
        "originating_appointment_id": appointment.originating_appointment_id,
        "originating_appointment_display": appointment.originating_appointment_display,
        "start": appointment.start.isoformat() if appointment.start else None,
        "end": appointment.end.isoformat() if appointment.end else None,
        "minutes_duration": appointment.minutes_duration,
        "created": appointment.created.isoformat() if appointment.created else None,
        "description": appointment.description,
        "recurrence_id": appointment.recurrence_id,
        "occurrence_changed": appointment.occurrence_changed,
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

    if appointment.classes:
        result["class_"] = [
            {"coding_system": cls.coding_system, "coding_code": cls.coding_code,
             "coding_display": cls.coding_display, "text": cls.text}
            for cls in appointment.classes
        ]

    if appointment.service_categories:
        result["service_category"] = [
            {"coding_system": sc.coding_system, "coding_code": sc.coding_code,
             "coding_display": sc.coding_display, "text": sc.text}
            for sc in appointment.service_categories
        ]

    if appointment.service_types:
        result["service_type"] = [
            {
                "coding_system": st.coding_system,
                "coding_code": st.coding_code,
                "coding_display": st.coding_display,
                "text": st.text,
                "reference_type": st.reference_type.value if st.reference_type else None,
                "reference_id": st.reference_id,
                "reference_display": st.reference_display,
            }
            for st in appointment.service_types
        ]

    if appointment.specialties:
        result["specialty"] = [
            {"coding_system": sp.coding_system, "coding_code": sp.coding_code,
             "coding_display": sp.coding_display, "text": sp.text}
            for sp in appointment.specialties
        ]

    if appointment.reasons:
        result["reason"] = [
            {
                "coding_system": r.coding_system,
                "coding_code": r.coding_code,
                "coding_display": r.coding_display,
                "text": r.text,
                "reference_type": r.reference_type.value if r.reference_type else None,
                "reference_id": r.reference_id,
                "reference_display": r.reference_display,
            }
            for r in appointment.reasons
        ]

    if appointment.supporting_informations:
        result["supporting_information"] = [
            {"reference_type": si.reference_type, "reference_id": si.reference_id,
             "reference_display": si.reference_display}
            for si in appointment.supporting_informations
        ]

    if appointment.slots:
        result["slot"] = [
            {
                "reference_type": s.reference_type.value if s.reference_type else None,
                "reference_id": s.reference_id,
                "reference_display": s.reference_display,
            }
            for s in appointment.slots
        ]

    if appointment.based_ons:
        result["based_on"] = [
            {
                "reference_type": b.reference_type.value if b.reference_type else None,
                "reference_id": b.reference_id,
                "reference_display": b.reference_display,
            }
            for b in appointment.based_ons
        ]

    if appointment.replaces_list:
        result["replaces"] = [
            {
                "reference_type": r.reference_type.value if r.reference_type else None,
                "reference_id": r.reference_id,
                "reference_display": r.reference_display,
            }
            for r in appointment.replaces_list
        ]

    if appointment.virtual_services:
        result["virtual_service"] = [
            {
                "channel_type_system": vs.channel_type_system,
                "channel_type_code": vs.channel_type_code,
                "channel_type_display": vs.channel_type_display,
                "address_url": vs.address_url,
                "additional_info": [u for u in vs.additional_info.split(",") if u] if vs.additional_info else None,
                "max_participants": vs.max_participants,
                "session_key": vs.session_key,
            }
            for vs in appointment.virtual_services
        ]

    if appointment.accounts:
        result["account"] = [
            {
                "reference_type": a.reference_type.value if a.reference_type else None,
                "reference_id": a.reference_id,
                "reference_display": a.reference_display,
            }
            for a in appointment.accounts
        ]

    if appointment.notes:
        result["note"] = [
            {
                "author_string": n.author_string,
                "author_reference_type": n.author_reference_type,
                "author_reference_id": n.author_reference_id,
                "author_reference_display": n.author_reference_display,
                "time": n.time.isoformat() if n.time else None,
                "text": n.text,
            }
            for n in appointment.notes
        ]

    if appointment.patient_instructions:
        result["patient_instruction"] = [
            {
                "coding_system": pi.coding_system,
                "coding_code": pi.coding_code,
                "coding_display": pi.coding_display,
                "text": pi.text,
                "reference_type": pi.reference_type.value if pi.reference_type else None,
                "reference_id": pi.reference_id,
                "reference_display": pi.reference_display,
            }
            for pi in appointment.patient_instructions
        ]

    if appointment.participants:
        result["participant"] = []
        for p in appointment.participants:
            entry = {
                "reference_type": p.reference_type.value if p.reference_type else None,
                "reference_id": p.reference_id,
                "reference_display": p.reference_display,
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
