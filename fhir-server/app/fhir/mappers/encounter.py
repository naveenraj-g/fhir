from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.encounter.encounter import EncounterModel


def _cc(coding_system, coding_code, coding_display, text=None) -> dict | None:
    """Build a CodeableConcept dict from flat columns; returns None if all empty."""
    coding = {k: v for k, v in {
        "system": coding_system, "code": coding_code, "display": coding_display,
    }.items() if v}
    cc: dict = {}
    if coding:
        cc["coding"] = [coding]
    if text:
        cc["text"] = text
    return cc or None


def _period(start, end) -> dict | None:
    p = {k: v for k, v in {
        "start": start.isoformat() if start else None,
        "end": end.isoformat() if end else None,
    }.items() if v}
    return p or None


def to_fhir_encounter(encounter: "EncounterModel") -> dict:
    """Convert EncounterModel (with relationships loaded) to a FHIR R5 Encounter dict."""
    result: dict = {
        "resourceType": "Encounter",
        "id": str(encounter.encounter_id),
        "status": encounter.status.value if encounter.status else None,
    }

    # identifier
    if encounter.identifiers:
        id_list = []
        for i in encounter.identifiers:
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
            period = _period(i.period_start, i.period_end)
            if period:
                entry["period"] = period
            if i.assigner:
                entry["assigner"] = {"display": i.assigner}
            if entry:
                id_list.append(entry)
        if id_list:
            result["identifier"] = id_list

    # statusHistory (R4 backward-compat)
    if encounter.status_history:
        result["statusHistory"] = [
            {k: v for k, v in {
                "status": sh.status,
                "period": _period(sh.period_start, sh.period_end),
            }.items() if v}
            for sh in encounter.status_history
        ]

    # class[] (0..* CodeableConcept) — R5
    if encounter.classes:
        class_list = []
        for c in encounter.classes:
            cc = _cc(c.coding_system, c.coding_code, c.coding_display, c.text)
            if cc:
                class_list.append(cc)
        if class_list:
            result["class"] = class_list

    # classHistory (R4 backward-compat)
    if encounter.class_history:
        ch_list = []
        for ch in encounter.class_history:
            entry = {}
            cls = {k: v for k, v in {
                "system": ch.class_system, "version": ch.class_version,
                "code": ch.class_code, "display": ch.class_display,
            }.items() if v}
            if cls:
                entry["class"] = cls
            period = _period(ch.period_start, ch.period_end)
            if period:
                entry["period"] = period
            if entry:
                ch_list.append(entry)
        if ch_list:
            result["classHistory"] = ch_list

    # businessStatus[]
    if encounter.business_statuses:
        bs_list = []
        for bs in encounter.business_statuses:
            entry = {}
            code_cc = _cc(bs.code_system, bs.code_code, bs.code_display, bs.code_text)
            if code_cc:
                entry["code"] = code_cc
            type_coding = {k: v for k, v in {
                "system": bs.type_system, "code": bs.type_code, "display": bs.type_display,
            }.items() if v}
            if type_coding:
                entry["type"] = type_coding
            if bs.effective_date:
                entry["effectiveDate"] = bs.effective_date.isoformat()
            if entry:
                bs_list.append(entry)
        if bs_list:
            result["businessStatus"] = bs_list

    # type[]
    if encounter.types:
        type_list = []
        for t in encounter.types:
            cc = _cc(t.coding_system, t.coding_code, t.coding_display, t.text)
            if cc:
                type_list.append(cc)
        if type_list:
            result["type"] = type_list

    # serviceType[] (0..* CodeableReference)
    if encounter.service_types:
        st_list = []
        for st in encounter.service_types:
            entry = {}
            concept = _cc(st.coding_system, st.coding_code, st.coding_display, st.text)
            if concept:
                entry["concept"] = concept
            if st.reference_type and st.reference_id:
                ref: dict = {"reference": f"{st.reference_type.value}/{st.reference_id}"}
                if st.reference_display:
                    ref["display"] = st.reference_display
                entry["reference"] = ref
            if entry:
                st_list.append(entry)
        if st_list:
            result["serviceType"] = st_list

    # priority
    priority_cc = _cc(encounter.priority_system, encounter.priority_code,
                      encounter.priority_display, encounter.priority_text)
    if priority_cc:
        result["priority"] = priority_cc

    # subject
    if encounter.subject_type and encounter.subject_id:
        subj: dict = {"reference": f"{encounter.subject_type.value}/{encounter.subject_id}"}
        if encounter.subject_display:
            subj["display"] = encounter.subject_display
        result["subject"] = subj

    # subjectStatus (R5 new)
    subject_status_cc = _cc(encounter.subject_status_system, encounter.subject_status_code,
                            encounter.subject_status_display, encounter.subject_status_text)
    if subject_status_cc:
        result["subjectStatus"] = subject_status_cc

    # episodeOfCare
    if encounter.episode_of_cares:
        eoc_list = []
        for e in encounter.episode_of_cares:
            if e.reference_type and e.reference_id:
                entry: dict = {"reference": f"{e.reference_type.value}/{e.reference_id}"}
                if e.reference_display:
                    entry["display"] = e.reference_display
                eoc_list.append(entry)
        if eoc_list:
            result["episodeOfCare"] = eoc_list

    # basedOn
    if encounter.based_ons:
        bo_list = []
        for b in encounter.based_ons:
            if b.reference_type and b.reference_id:
                entry = {"reference": f"{b.reference_type.value}/{b.reference_id}"}
                if b.reference_display:
                    entry["display"] = b.reference_display
                bo_list.append(entry)
        if bo_list:
            result["basedOn"] = bo_list

    # careTeam (R5 new)
    if encounter.care_teams:
        ct_list = []
        for ct in encounter.care_teams:
            if ct.reference_type and ct.reference_id:
                ct_entry: dict = {"reference": f"{ct.reference_type.value}/{ct.reference_id}"}
                if ct.reference_display:
                    ct_entry["display"] = ct.reference_display
                ct_list.append(ct_entry)
        if ct_list:
            result["careTeam"] = ct_list

    # participant (actor, not individual)
    if encounter.participants:
        participant_list = []
        for p in encounter.participants:
            entry = {}
            if p.types:
                type_cc_list = [cc for pt in p.types
                                if (cc := _cc(pt.coding_system, pt.coding_code, pt.coding_display, pt.text))]
                if type_cc_list:
                    entry["type"] = type_cc_list
            if p.reference_type and p.reference_id:
                actor: dict = {"reference": f"{p.reference_type.value}/{p.reference_id}"}
                if p.reference_display:
                    actor["display"] = p.reference_display
                entry["actor"] = actor
            period = _period(p.period_start, p.period_end)
            if period:
                entry["period"] = period
            if entry:
                participant_list.append(entry)
        if participant_list:
            result["participant"] = participant_list

    # appointment
    if encounter.appointment_refs:
        appt_list = []
        for a in encounter.appointment_refs:
            if a.reference_type and a.reference_id:
                appt_entry: dict = {"reference": f"{a.reference_type.value}/{a.reference_id}"}
                if a.reference_display:
                    appt_entry["display"] = a.reference_display
                appt_list.append(appt_entry)
        if appt_list:
            result["appointment"] = appt_list

    # virtualService (R5 new)
    if encounter.virtual_services:
        vs_list = []
        for vs in encounter.virtual_services:
            entry = {}
            channel = {k: v for k, v in {
                "system": vs.channel_type_system,
                "code": vs.channel_type_code,
                "display": vs.channel_type_display,
            }.items() if v}
            if channel:
                entry["channelType"] = channel
            if vs.address_url:
                entry["addressUrl"] = vs.address_url
            if vs.additional_info:
                entry["additionalInfo"] = [u.strip() for u in vs.additional_info.split(",") if u.strip()]
            if vs.max_participants is not None:
                entry["maxParticipants"] = vs.max_participants
            if vs.session_key:
                entry["sessionKey"] = vs.session_key
            if entry:
                vs_list.append(entry)
        if vs_list:
            result["virtualService"] = vs_list

    # actualPeriod (R5 renamed from period)
    period = _period(encounter.actual_period_start, encounter.actual_period_end)
    if period:
        result["actualPeriod"] = period

    # plannedStartDate / plannedEndDate (R5 new)
    if encounter.planned_start_date:
        result["plannedStartDate"] = encounter.planned_start_date.isoformat()
    if encounter.planned_end_date:
        result["plannedEndDate"] = encounter.planned_end_date.isoformat()

    # length (Duration)
    if encounter.length_value is not None or encounter.length_code:
        result["length"] = {k: v for k, v in {
            "value": encounter.length_value,
            "comparator": encounter.length_comparator,
            "unit": encounter.length_unit,
            "system": encounter.length_system,
            "code": encounter.length_code,
        }.items() if v is not None}

    # reason[] (R5 BackboneElement)
    if encounter.reasons:
        reason_list = []
        for r in encounter.reasons:
            entry = {}
            if r.uses:
                use_list = [cc for ru in r.uses
                            if (cc := _cc(ru.coding_system, ru.coding_code, ru.coding_display, ru.text))]
                if use_list:
                    entry["use"] = use_list
            if r.values:
                val_list = []
                for rv in r.values:
                    val_entry = {}
                    concept = _cc(rv.coding_system, rv.coding_code, rv.coding_display, rv.text)
                    if concept:
                        val_entry["concept"] = concept
                    if rv.reference_type and rv.reference_id:
                        ref: dict = {"reference": f"{rv.reference_type.value}/{rv.reference_id}"}
                        if rv.reference_display:
                            ref["display"] = rv.reference_display
                        val_entry["reference"] = ref
                    if val_entry:
                        val_list.append(val_entry)
                if val_list:
                    entry["value"] = val_list
            if entry:
                reason_list.append(entry)
        if reason_list:
            result["reason"] = reason_list

    # diagnosis[]
    if encounter.diagnoses:
        diag_list = []
        for d in encounter.diagnoses:
            entry = {}
            if d.conditions:
                cond_list = []
                for dc in d.conditions:
                    cond_entry = {}
                    concept = _cc(dc.coding_system, dc.coding_code, dc.coding_display, dc.text)
                    if concept:
                        cond_entry["concept"] = concept
                    if dc.reference_type and dc.reference_id:
                        ref: dict = {"reference": f"{dc.reference_type.value}/{dc.reference_id}"}
                        if dc.reference_display:
                            ref["display"] = dc.reference_display
                        cond_entry["reference"] = ref
                    if cond_entry:
                        cond_list.append(cond_entry)
                if cond_list:
                    entry["condition"] = cond_list
            if d.uses:
                use_list = [cc for du in d.uses
                            if (cc := _cc(du.coding_system, du.coding_code, du.coding_display, du.text))]
                if use_list:
                    entry["use"] = use_list
            if entry:
                diag_list.append(entry)
        if diag_list:
            result["diagnosis"] = diag_list

    # account
    if encounter.accounts:
        acct_list = []
        for a in encounter.accounts:
            if a.reference_type and a.reference_id:
                acct_entry: dict = {"reference": f"{a.reference_type.value}/{a.reference_id}"}
                if a.reference_display:
                    acct_entry["display"] = a.reference_display
                acct_list.append(acct_entry)
        if acct_list:
            result["account"] = acct_list

    # admission (R5 renamed from hospitalization)
    admission = _build_fhir_admission(encounter)
    if admission:
        result["admission"] = admission

    # dietPreference / specialArrangement / specialCourtesy (top-level in R5)
    if encounter.diet_preferences:
        result["dietPreference"] = [
            cc for dp in encounter.diet_preferences
            if (cc := _cc(dp.coding_system, dp.coding_code, dp.coding_display, dp.text))
        ]
    if encounter.special_arrangements:
        result["specialArrangement"] = [
            cc for sa in encounter.special_arrangements
            if (cc := _cc(sa.coding_system, sa.coding_code, sa.coding_display, sa.text))
        ]
    if encounter.special_courtesies:
        result["specialCourtesy"] = [
            cc for sc in encounter.special_courtesies
            if (cc := _cc(sc.coding_system, sc.coding_code, sc.coding_display, sc.text))
        ]

    # location
    if encounter.locations:
        loc_list = []
        for loc in encounter.locations:
            entry = {}
            if loc.reference_type and loc.reference_id:
                lref: dict = {"reference": f"{loc.reference_type.value}/{loc.reference_id}"}
                if loc.reference_display:
                    lref["display"] = loc.reference_display
                entry["location"] = lref
            if loc.status:
                entry["status"] = loc.status.value if hasattr(loc.status, "value") else loc.status
            form_cc = _cc(loc.form_system, loc.form_code, loc.form_display, loc.form_text)
            if form_cc:
                entry["form"] = form_cc
            period = _period(loc.period_start, loc.period_end)
            if period:
                entry["period"] = period
            if entry:
                loc_list.append(entry)
        if loc_list:
            result["location"] = loc_list

    # serviceProvider
    if encounter.service_provider_type and encounter.service_provider_id:
        sp: dict = {"reference": f"{encounter.service_provider_type.value}/{encounter.service_provider_id}"}
        if encounter.service_provider_display:
            sp["display"] = encounter.service_provider_display
        result["serviceProvider"] = sp

    # partOf
    if encounter.part_of_id:
        result["partOf"] = {"reference": f"Encounter/{encounter.part_of_id}"}

    return {k: v for k, v in result.items() if v is not None}


def _build_fhir_admission(encounter: "EncounterModel") -> dict:
    admission: dict = {}

    if encounter.admission_pre_admission_identifier_value:
        pre_id: dict = {"value": encounter.admission_pre_admission_identifier_value}
        if encounter.admission_pre_admission_identifier_system:
            pre_id["system"] = encounter.admission_pre_admission_identifier_system
        admission["preAdmissionIdentifier"] = pre_id

    if encounter.admission_origin_id:
        ref_str = (
            f"{encounter.admission_origin_type}/{encounter.admission_origin_id}"
            if encounter.admission_origin_type
            else f"Location/{encounter.admission_origin_id}"
        )
        orig: dict = {"reference": ref_str}
        if encounter.admission_origin_display:
            orig["display"] = encounter.admission_origin_display
        admission["origin"] = orig

    for prefix, fhir_key in [
        ("admission_admit_source", "admitSource"),
        ("admission_re_admission", "reAdmission"),
        ("admission_discharge_disposition", "dischargeDisposition"),
    ]:
        cc = _cc(
            getattr(encounter, f"{prefix}_system", None),
            getattr(encounter, f"{prefix}_code", None),
            getattr(encounter, f"{prefix}_display", None),
            getattr(encounter, f"{prefix}_text", None),
        )
        if cc:
            admission[fhir_key] = cc

    if encounter.admission_destination_id:
        ref_str = (
            f"{encounter.admission_destination_type}/{encounter.admission_destination_id}"
            if encounter.admission_destination_type
            else f"Location/{encounter.admission_destination_id}"
        )
        dest: dict = {"reference": ref_str}
        if encounter.admission_destination_display:
            dest["display"] = encounter.admission_destination_display
        admission["destination"] = dest

    return admission


def to_plain_encounter(encounter: "EncounterModel") -> dict:
    """Return the encounter as a flat snake_case JSON object."""
    result: dict = {
        "id": encounter.encounter_id,
        "user_id": encounter.user_id,
        "org_id": encounter.org_id,
        "status": encounter.status.value if encounter.status else None,
        "priority_system": encounter.priority_system,
        "priority_code": encounter.priority_code,
        "priority_display": encounter.priority_display,
        "priority_text": encounter.priority_text,
        "subject_type": encounter.subject_type.value if encounter.subject_type else None,
        "subject_id": encounter.subject_id,
        "subject_display": encounter.subject_display,
        "subject_status_system": encounter.subject_status_system,
        "subject_status_code": encounter.subject_status_code,
        "subject_status_display": encounter.subject_status_display,
        "subject_status_text": encounter.subject_status_text,
        "actual_period_start": encounter.actual_period_start.isoformat() if encounter.actual_period_start else None,
        "actual_period_end": encounter.actual_period_end.isoformat() if encounter.actual_period_end else None,
        "planned_start_date": encounter.planned_start_date.isoformat() if encounter.planned_start_date else None,
        "planned_end_date": encounter.planned_end_date.isoformat() if encounter.planned_end_date else None,
        "service_provider_type": encounter.service_provider_type.value if encounter.service_provider_type else None,
        "service_provider_id": encounter.service_provider_id,
        "service_provider_display": encounter.service_provider_display,
        "part_of_id": encounter.part_of_id,
        "created_at": encounter.created_at.isoformat() if encounter.created_at else None,
        "updated_at": encounter.updated_at.isoformat() if encounter.updated_at else None,
        "created_by": encounter.created_by,
        "updated_by": encounter.updated_by,
    }

    # length
    if encounter.length_value is not None or encounter.length_code:
        result["length"] = {
            "value": encounter.length_value,
            "comparator": encounter.length_comparator,
            "unit": encounter.length_unit,
            "system": encounter.length_system,
            "code": encounter.length_code,
        }

    # admission (flat columns → nested plain object)
    admission_fields = [
        "admission_pre_admission_identifier_system", "admission_pre_admission_identifier_value",
        "admission_origin_type", "admission_origin_id", "admission_origin_display",
        "admission_admit_source_system", "admission_admit_source_code",
        "admission_admit_source_display", "admission_admit_source_text",
        "admission_re_admission_system", "admission_re_admission_code",
        "admission_re_admission_display", "admission_re_admission_text",
        "admission_destination_type", "admission_destination_id", "admission_destination_display",
        "admission_discharge_disposition_system", "admission_discharge_disposition_code",
        "admission_discharge_disposition_display", "admission_discharge_disposition_text",
    ]
    if any(getattr(encounter, f, None) for f in admission_fields):
        result["admission"] = {
            "pre_admission_identifier_system": encounter.admission_pre_admission_identifier_system,
            "pre_admission_identifier_value": encounter.admission_pre_admission_identifier_value,
            "origin_type": encounter.admission_origin_type,
            "origin_id": encounter.admission_origin_id,
            "origin_display": encounter.admission_origin_display,
            "admit_source_system": encounter.admission_admit_source_system,
            "admit_source_code": encounter.admission_admit_source_code,
            "admit_source_display": encounter.admission_admit_source_display,
            "admit_source_text": encounter.admission_admit_source_text,
            "re_admission_system": encounter.admission_re_admission_system,
            "re_admission_code": encounter.admission_re_admission_code,
            "re_admission_display": encounter.admission_re_admission_display,
            "re_admission_text": encounter.admission_re_admission_text,
            "destination_type": encounter.admission_destination_type,
            "destination_id": encounter.admission_destination_id,
            "destination_display": encounter.admission_destination_display,
            "discharge_disposition_system": encounter.admission_discharge_disposition_system,
            "discharge_disposition_code": encounter.admission_discharge_disposition_code,
            "discharge_disposition_display": encounter.admission_discharge_disposition_display,
            "discharge_disposition_text": encounter.admission_discharge_disposition_text,
        }

    if encounter.identifiers:
        result["identifier"] = [
            {
                "use": i.use, "type_system": i.type_system, "type_code": i.type_code,
                "type_display": i.type_display, "type_text": i.type_text,
                "system": i.system, "value": i.value,
                "period_start": i.period_start.isoformat() if i.period_start else None,
                "period_end": i.period_end.isoformat() if i.period_end else None,
                "assigner": i.assigner,
            }
            for i in encounter.identifiers
        ]

    if encounter.status_history:
        result["status_history"] = [
            {
                "status": sh.status,
                "period_start": sh.period_start.isoformat() if sh.period_start else None,
                "period_end": sh.period_end.isoformat() if sh.period_end else None,
            }
            for sh in encounter.status_history
        ]

    if encounter.class_history:
        result["class_history"] = [
            {
                "class_system": ch.class_system, "class_version": ch.class_version,
                "class_code": ch.class_code, "class_display": ch.class_display,
                "period_start": ch.period_start.isoformat() if ch.period_start else None,
                "period_end": ch.period_end.isoformat() if ch.period_end else None,
            }
            for ch in encounter.class_history
        ]

    if encounter.classes:
        result["class"] = [
            {"coding_system": c.coding_system, "coding_code": c.coding_code,
             "coding_display": c.coding_display, "text": c.text}
            for c in encounter.classes
        ]

    if encounter.business_statuses:
        result["business_status"] = [
            {
                "code_system": bs.code_system, "code_code": bs.code_code,
                "code_display": bs.code_display, "code_text": bs.code_text,
                "type_system": bs.type_system, "type_code": bs.type_code,
                "type_display": bs.type_display,
                "effective_date": bs.effective_date.isoformat() if bs.effective_date else None,
            }
            for bs in encounter.business_statuses
        ]

    if encounter.service_types:
        result["service_type"] = [
            {
                "coding_system": st.coding_system, "coding_code": st.coding_code,
                "coding_display": st.coding_display, "text": st.text,
                "reference_type": st.reference_type.value if st.reference_type else None,
                "reference_id": st.reference_id,
                "reference_display": st.reference_display,
            }
            for st in encounter.service_types
        ]

    if encounter.types:
        result["type"] = [
            {"coding_system": t.coding_system, "coding_code": t.coding_code,
             "coding_display": t.coding_display, "text": t.text}
            for t in encounter.types
        ]

    if encounter.episode_of_cares:
        result["episode_of_care"] = [
            {
                "reference_type": e.reference_type.value if e.reference_type else None,
                "reference_id": e.reference_id,
                "reference_display": e.reference_display,
            }
            for e in encounter.episode_of_cares
        ]

    if encounter.based_ons:
        result["based_on"] = [
            {
                "reference_type": b.reference_type.value if b.reference_type else None,
                "reference_id": b.reference_id,
                "reference_display": b.reference_display,
            }
            for b in encounter.based_ons
        ]

    if encounter.care_teams:
        result["care_team"] = [
            {
                "reference_type": ct.reference_type.value if ct.reference_type else None,
                "reference_id": ct.reference_id,
                "reference_display": ct.reference_display,
            }
            for ct in encounter.care_teams
        ]

    if encounter.participants:
        result["participant"] = [
            {
                "type": [
                    {"coding_system": pt.coding_system, "coding_code": pt.coding_code,
                     "coding_display": pt.coding_display, "text": pt.text}
                    for pt in p.types
                ] if p.types else None,
                "reference_type": p.reference_type.value if p.reference_type else None,
                "reference_id": p.reference_id,
                "reference_display": p.reference_display,
                "period_start": p.period_start.isoformat() if p.period_start else None,
                "period_end": p.period_end.isoformat() if p.period_end else None,
            }
            for p in encounter.participants
        ]

    if encounter.appointment_refs:
        result["appointment"] = [
            {
                "reference_type": a.reference_type.value if a.reference_type else None,
                "reference_id": a.reference_id,
                "reference_display": a.reference_display,
            }
            for a in encounter.appointment_refs
        ]

    if encounter.virtual_services:
        result["virtual_service"] = [
            {
                "channel_type_system": vs.channel_type_system,
                "channel_type_code": vs.channel_type_code,
                "channel_type_display": vs.channel_type_display,
                "address_url": vs.address_url,
                "additional_info": vs.additional_info,
                "max_participants": vs.max_participants,
                "session_key": vs.session_key,
            }
            for vs in encounter.virtual_services
        ]

    if encounter.reasons:
        result["reason"] = [
            {
                "use": [
                    {"coding_system": ru.coding_system, "coding_code": ru.coding_code,
                     "coding_display": ru.coding_display, "text": ru.text}
                    for ru in r.uses
                ] if r.uses else None,
                "value": [
                    {
                        "coding_system": rv.coding_system, "coding_code": rv.coding_code,
                        "coding_display": rv.coding_display, "text": rv.text,
                        "reference_type": rv.reference_type.value if rv.reference_type else None,
                        "reference_id": rv.reference_id,
                        "reference_display": rv.reference_display,
                    }
                    for rv in r.values
                ] if r.values else None,
            }
            for r in encounter.reasons
        ]

    if encounter.diagnoses:
        result["diagnosis"] = [
            {
                "condition": [
                    {
                        "coding_system": dc.coding_system, "coding_code": dc.coding_code,
                        "coding_display": dc.coding_display, "text": dc.text,
                        "reference_type": dc.reference_type.value if dc.reference_type else None,
                        "reference_id": dc.reference_id,
                        "reference_display": dc.reference_display,
                    }
                    for dc in d.conditions
                ] if d.conditions else None,
                "use": [
                    {"coding_system": du.coding_system, "coding_code": du.coding_code,
                     "coding_display": du.coding_display, "text": du.text}
                    for du in d.uses
                ] if d.uses else None,
            }
            for d in encounter.diagnoses
        ]

    if encounter.accounts:
        result["account"] = [
            {
                "reference_type": a.reference_type.value if a.reference_type else None,
                "reference_id": a.reference_id,
                "reference_display": a.reference_display,
            }
            for a in encounter.accounts
        ]

    if encounter.diet_preferences:
        result["diet_preference"] = [
            {"coding_system": dp.coding_system, "coding_code": dp.coding_code,
             "coding_display": dp.coding_display, "text": dp.text}
            for dp in encounter.diet_preferences
        ]

    if encounter.special_arrangements:
        result["special_arrangement"] = [
            {"coding_system": sa.coding_system, "coding_code": sa.coding_code,
             "coding_display": sa.coding_display, "text": sa.text}
            for sa in encounter.special_arrangements
        ]

    if encounter.special_courtesies:
        result["special_courtesy"] = [
            {"coding_system": sc.coding_system, "coding_code": sc.coding_code,
             "coding_display": sc.coding_display, "text": sc.text}
            for sc in encounter.special_courtesies
        ]

    if encounter.locations:
        result["location"] = [
            {
                "reference_type": loc.reference_type.value if loc.reference_type else None,
                "reference_id": loc.reference_id,
                "reference_display": loc.reference_display,
                "status": loc.status.value if loc.status else None,
                "form_system": loc.form_system,
                "form_code": loc.form_code,
                "form_display": loc.form_display,
                "form_text": loc.form_text,
                "period_start": loc.period_start.isoformat() if loc.period_start else None,
                "period_end": loc.period_end.isoformat() if loc.period_end else None,
            }
            for loc in encounter.locations
        ]

    return {k: v for k, v in result.items() if v is not None}
