from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.encounter.encounter import EncounterModel


def to_fhir_encounter(encounter: "EncounterModel") -> dict:
    """Convert EncounterModel (with relationships loaded) to a FHIR R4 Encounter dict."""
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
            if i.type_system or i.type_code or i.type_display or i.type_text:
                type_coding = {k: v for k, v in {
                    "system": i.type_system, "code": i.type_code, "display": i.type_display,
                }.items() if v}
                entry["type"] = {k: v for k, v in {
                    "coding": [type_coding] if type_coding else None,
                    "text": i.type_text,
                }.items() if v}
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

    # statusHistory
    if encounter.status_history:
        result["statusHistory"] = [
            {k: v for k, v in {
                "status": sh.status,
                "period": {k2: v2 for k2, v2 in {
                    "start": sh.period_start.isoformat() if sh.period_start else None,
                    "end": sh.period_end.isoformat() if sh.period_end else None,
                }.items() if v2} or None,
            }.items() if v}
            for sh in encounter.status_history
        ]

    # class (1..1 Coding)
    if encounter.class_code or encounter.class_system:
        result["class"] = {k: v for k, v in {
            "system": encounter.class_system,
            "version": encounter.class_version,
            "code": encounter.class_code,
            "display": encounter.class_display,
        }.items() if v}

    # classHistory
    if encounter.class_history:
        result["classHistory"] = []
        for ch in encounter.class_history:
            entry = {}
            cls = {k: v for k, v in {
                "system": ch.class_system,
                "version": ch.class_version,
                "code": ch.class_code,
                "display": ch.class_display,
            }.items() if v}
            if cls:
                entry["class"] = cls
            if ch.period_start or ch.period_end:
                entry["period"] = {k: v for k, v in {
                    "start": ch.period_start.isoformat() if ch.period_start else None,
                    "end": ch.period_end.isoformat() if ch.period_end else None,
                }.items() if v}
            if entry:
                result["classHistory"].append(entry)

    # type
    if encounter.types:
        type_list = []
        for t in encounter.types:
            entry = {}
            coding = {k: v for k, v in {
                "system": t.coding_system, "code": t.coding_code, "display": t.coding_display,
            }.items() if v}
            if coding:
                entry["coding"] = [coding]
            if t.text:
                entry["text"] = t.text
            if entry:
                type_list.append(entry)
        if type_list:
            result["type"] = type_list

    # serviceType
    if encounter.service_type_code or encounter.service_type_system or encounter.service_type_text:
        coding = {k: v for k, v in {
            "system": encounter.service_type_system,
            "code": encounter.service_type_code,
            "display": encounter.service_type_display,
        }.items() if v}
        st: dict = {}
        if coding:
            st["coding"] = [coding]
        if encounter.service_type_text:
            st["text"] = encounter.service_type_text
        if st:
            result["serviceType"] = st

    # priority
    if encounter.priority_code or encounter.priority_system or encounter.priority_text:
        coding = {k: v for k, v in {
            "system": encounter.priority_system,
            "code": encounter.priority_code,
            "display": encounter.priority_display,
        }.items() if v}
        pr: dict = {}
        if coding:
            pr["coding"] = [coding]
        if encounter.priority_text:
            pr["text"] = encounter.priority_text
        if pr:
            result["priority"] = pr

    # subject
    if encounter.subject_type and encounter.subject_id:
        subject: dict = {"reference": f"{encounter.subject_type.value}/{encounter.subject_id}"}
        if encounter.subject_display:
            subject["display"] = encounter.subject_display
        result["subject"] = subject

    # episodeOfCare
    if encounter.episode_of_cares:
        result["episodeOfCare"] = [
            {k: v for k, v in {
                "reference": f"EpisodeOfCare/{e.episode_of_care_id}" if e.episode_of_care_id else None,
                "display": e.display,
            }.items() if v}
            for e in encounter.episode_of_cares
        ]

    # basedOn
    if encounter.based_ons:
        based_on_list = []
        for b in encounter.based_ons:
            if b.reference_type and b.reference_id:
                entry = {"reference": f"{b.reference_type.value}/{b.reference_id}"}
                if b.reference_display:
                    entry["display"] = b.reference_display
                based_on_list.append(entry)
        if based_on_list:
            result["basedOn"] = based_on_list

    # participant
    if encounter.participants:
        participant_list = []
        for p in encounter.participants:
            entry = {}
            if p.types:
                type_cc_list = []
                for pt in p.types:
                    cc: dict = {}
                    coding = {k: v for k, v in {
                        "system": pt.coding_system,
                        "code": pt.coding_code,
                        "display": pt.coding_display,
                    }.items() if v}
                    if coding:
                        cc["coding"] = [coding]
                    if pt.text:
                        cc["text"] = pt.text
                    if cc:
                        type_cc_list.append(cc)
                if type_cc_list:
                    entry["type"] = type_cc_list
            if p.individual_type and p.individual_id:
                ind: dict = {"reference": f"{p.individual_type.value}/{p.individual_id}"}
                if p.individual_display:
                    ind["display"] = p.individual_display
                entry["individual"] = ind
            if p.period_start or p.period_end:
                entry["period"] = {k: v for k, v in {
                    "start": p.period_start.isoformat() if p.period_start else None,
                    "end": p.period_end.isoformat() if p.period_end else None,
                }.items() if v}
            if entry:
                participant_list.append(entry)
        if participant_list:
            result["participant"] = participant_list

    # appointment
    if encounter.appointment_refs:
        result["appointment"] = [
            {k: v for k, v in {
                "reference": f"Appointment/{a.appointment_id}" if a.appointment_id else None,
                "display": a.appointment_display,
            }.items() if v}
            for a in encounter.appointment_refs
        ]

    # period
    if encounter.period_start or encounter.period_end:
        result["period"] = {k: v for k, v in {
            "start": encounter.period_start.isoformat() if encounter.period_start else None,
            "end": encounter.period_end.isoformat() if encounter.period_end else None,
        }.items() if v}

    # length (Duration)
    if encounter.length_value is not None or encounter.length_code:
        result["length"] = {k: v for k, v in {
            "value": encounter.length_value,
            "comparator": encounter.length_comparator,
            "unit": encounter.length_unit,
            "system": encounter.length_system,
            "code": encounter.length_code,
        }.items() if v is not None}

    # reasonCode
    if encounter.reason_codes:
        reason_list = []
        for r in encounter.reason_codes:
            entry = {}
            coding = {k: v for k, v in {
                "system": r.coding_system, "code": r.coding_code, "display": r.coding_display,
            }.items() if v}
            if coding:
                entry["coding"] = [coding]
            if r.text:
                entry["text"] = r.text
            if entry:
                reason_list.append(entry)
        if reason_list:
            result["reasonCode"] = reason_list

    # reasonReference
    if encounter.reason_references:
        rr_list = []
        for rr in encounter.reason_references:
            if rr.reference_type and rr.reference_id:
                entry = {"reference": f"{rr.reference_type}/{rr.reference_id}"}
                if rr.reference_display:
                    entry["display"] = rr.reference_display
                rr_list.append(entry)
        if rr_list:
            result["reasonReference"] = rr_list

    # diagnosis
    if encounter.diagnoses:
        diag_list = []
        for d in encounter.diagnoses:
            entry = {}
            if d.condition_type and d.condition_id:
                cond: dict = {"reference": f"{d.condition_type.value}/{d.condition_id}"}
                if d.condition_display:
                    cond["display"] = d.condition_display
                entry["condition"] = cond
            if d.use_system or d.use_code or d.use_text:
                use_coding = {k: v for k, v in {
                    "system": d.use_system, "code": d.use_code, "display": d.use_display,
                }.items() if v}
                use_cc: dict = {}
                if use_coding:
                    use_cc["coding"] = [use_coding]
                if d.use_text:
                    use_cc["text"] = d.use_text
                if use_cc:
                    entry["use"] = use_cc
            if d.rank is not None:
                entry["rank"] = d.rank
            if entry:
                diag_list.append(entry)
        if diag_list:
            result["diagnosis"] = diag_list

    # account
    if encounter.accounts:
        result["account"] = [
            {k: v for k, v in {
                "reference": f"Account/{a.account_id}" if a.account_id else None,
                "display": a.account_display,
            }.items() if v}
            for a in encounter.accounts
        ]

    # hospitalization
    hosp = _build_fhir_hospitalization(encounter)
    if hosp:
        result["hospitalization"] = hosp

    # location
    if encounter.locations:
        loc_list = []
        for loc in encounter.locations:
            entry = {}
            if loc.location_id:
                lref: dict = {"reference": f"Location/{loc.location_id}"}
                if loc.location_display:
                    lref["display"] = loc.location_display
                entry["location"] = lref
            if loc.status:
                entry["status"] = loc.status.value if hasattr(loc.status, "value") else loc.status
            if loc.physical_type_system or loc.physical_type_code or loc.physical_type_text:
                pt_coding = {k: v for k, v in {
                    "system": loc.physical_type_system,
                    "code": loc.physical_type_code,
                    "display": loc.physical_type_display,
                }.items() if v}
                pt_cc: dict = {}
                if pt_coding:
                    pt_cc["coding"] = [pt_coding]
                if loc.physical_type_text:
                    pt_cc["text"] = loc.physical_type_text
                if pt_cc:
                    entry["physicalType"] = pt_cc
            if loc.period_start or loc.period_end:
                entry["period"] = {k: v for k, v in {
                    "start": loc.period_start.isoformat() if loc.period_start else None,
                    "end": loc.period_end.isoformat() if loc.period_end else None,
                }.items() if v}
            if entry:
                loc_list.append(entry)
        if loc_list:
            result["location"] = loc_list

    # serviceProvider
    if encounter.service_provider_id:
        sp: dict = {"reference": f"Organization/{encounter.service_provider_id}"}
        if encounter.service_provider_display:
            sp["display"] = encounter.service_provider_display
        result["serviceProvider"] = sp

    # partOf
    if encounter.part_of_id:
        result["partOf"] = {"reference": f"Encounter/{encounter.part_of_id}"}

    return {k: v for k, v in result.items() if v is not None}


def _build_fhir_hospitalization(encounter: "EncounterModel") -> dict:
    hosp: dict = {}

    if encounter.hosp_pre_admission_identifier_value:
        pre_id: dict = {"value": encounter.hosp_pre_admission_identifier_value}
        if encounter.hosp_pre_admission_identifier_system:
            pre_id["system"] = encounter.hosp_pre_admission_identifier_system
        hosp["preAdmissionIdentifier"] = pre_id

    if encounter.hosp_origin_id:
        orig: dict = {
            "reference": f"{encounter.hosp_origin_type}/{encounter.hosp_origin_id}" if encounter.hosp_origin_type else f"Location/{encounter.hosp_origin_id}"
        }
        if encounter.hosp_origin_display:
            orig["display"] = encounter.hosp_origin_display
        hosp["origin"] = orig

    for field_prefix, fhir_key in [
        ("hosp_admit_source", "admitSource"),
        ("hosp_re_admission", "reAdmission"),
        ("hosp_discharge_disposition", "dischargeDisposition"),
    ]:
        sys_val = getattr(encounter, f"{field_prefix}_system", None)
        code_val = getattr(encounter, f"{field_prefix}_code", None)
        display_val = getattr(encounter, f"{field_prefix}_display", None)
        text_val = getattr(encounter, f"{field_prefix}_text", None)
        if sys_val or code_val or text_val:
            coding = {k: v for k, v in {
                "system": sys_val, "code": code_val, "display": display_val,
            }.items() if v}
            cc: dict = {}
            if coding:
                cc["coding"] = [coding]
            if text_val:
                cc["text"] = text_val
            if cc:
                hosp[fhir_key] = cc

    if encounter.hosp_diet_preferences:
        hosp["dietPreference"] = [
            _codeable_concept_from_row(dp)
            for dp in encounter.hosp_diet_preferences
        ]

    if encounter.hosp_special_arrangements:
        hosp["specialArrangement"] = [
            _codeable_concept_from_row(sa)
            for sa in encounter.hosp_special_arrangements
        ]

    if encounter.hosp_special_courtesies:
        hosp["specialCourtesy"] = [
            _codeable_concept_from_row(sc)
            for sc in encounter.hosp_special_courtesies
        ]

    if encounter.hosp_destination_id:
        dest: dict = {
            "reference": f"{encounter.hosp_destination_type}/{encounter.hosp_destination_id}" if encounter.hosp_destination_type else f"Location/{encounter.hosp_destination_id}"
        }
        if encounter.hosp_destination_display:
            dest["display"] = encounter.hosp_destination_display
        hosp["destination"] = dest

    return hosp


def _codeable_concept_from_row(row) -> dict:
    coding = {k: v for k, v in {
        "system": row.coding_system,
        "code": row.coding_code,
        "display": row.coding_display,
    }.items() if v}
    cc: dict = {}
    if coding:
        cc["coding"] = [coding]
    if row.text:
        cc["text"] = row.text
    return cc


def to_plain_encounter(encounter: "EncounterModel") -> dict:
    """Return the encounter as a flat snake_case JSON object."""
    result: dict = {
        "id": encounter.encounter_id,
        "user_id": encounter.user_id,
        "org_id": encounter.org_id,
        "status": encounter.status.value if encounter.status else None,
        "class_system": encounter.class_system,
        "class_version": encounter.class_version,
        "class_code": encounter.class_code,
        "class_display": encounter.class_display,
        "service_type_system": encounter.service_type_system,
        "service_type_code": encounter.service_type_code,
        "service_type_display": encounter.service_type_display,
        "service_type_text": encounter.service_type_text,
        "priority_system": encounter.priority_system,
        "priority_code": encounter.priority_code,
        "priority_display": encounter.priority_display,
        "priority_text": encounter.priority_text,
        "subject_type": encounter.subject_type.value if encounter.subject_type else None,
        "subject_id": encounter.subject_id,
        "subject_display": encounter.subject_display,
        "period_start": encounter.period_start.isoformat() if encounter.period_start else None,
        "period_end": encounter.period_end.isoformat() if encounter.period_end else None,
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

    if encounter.identifiers:
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
                "class_system": ch.class_system,
                "class_version": ch.class_version,
                "class_code": ch.class_code,
                "class_display": ch.class_display,
                "period_start": ch.period_start.isoformat() if ch.period_start else None,
                "period_end": ch.period_end.isoformat() if ch.period_end else None,
            }
            for ch in encounter.class_history
        ]

    if encounter.types:
        result["type"] = [
            {
                "coding_system": t.coding_system,
                "coding_code": t.coding_code,
                "coding_display": t.coding_display,
                "text": t.text,
            }
            for t in encounter.types
        ]

    if encounter.episode_of_cares:
        result["episode_of_care"] = [
            {"episode_of_care_id": e.episode_of_care_id, "display": e.display}
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

    if encounter.participants:
        result["participant"] = [
            {
                "type": [
                    {
                        "coding_system": pt.coding_system,
                        "coding_code": pt.coding_code,
                        "coding_display": pt.coding_display,
                        "text": pt.text,
                    }
                    for pt in p.types
                ] if p.types else None,
                "individual_type": p.individual_type.value if p.individual_type else None,
                "individual_id": p.individual_id,
                "individual_display": p.individual_display,
                "period_start": p.period_start.isoformat() if p.period_start else None,
                "period_end": p.period_end.isoformat() if p.period_end else None,
            }
            for p in encounter.participants
        ]

    if encounter.appointment_refs:
        result["appointment"] = [
            {"appointment_id": a.appointment_id, "display": a.appointment_display}
            for a in encounter.appointment_refs
        ]

    if encounter.reason_codes:
        result["reason_code"] = [
            {
                "coding_system": r.coding_system,
                "coding_code": r.coding_code,
                "coding_display": r.coding_display,
                "text": r.text,
            }
            for r in encounter.reason_codes
        ]

    if encounter.reason_references:
        result["reason_reference"] = [
            {
                "reference_type": rr.reference_type,
                "reference_id": rr.reference_id,
                "reference_display": rr.reference_display,
            }
            for rr in encounter.reason_references
        ]

    if encounter.diagnoses:
        result["diagnosis"] = [
            {
                "condition_type": d.condition_type.value if d.condition_type else None,
                "condition_id": d.condition_id,
                "condition_display": d.condition_display,
                "use_system": d.use_system,
                "use_code": d.use_code,
                "use_display": d.use_display,
                "use_text": d.use_text,
                "rank": d.rank,
            }
            for d in encounter.diagnoses
        ]

    if encounter.accounts:
        result["account"] = [
            {"account_id": a.account_id, "display": a.account_display}
            for a in encounter.accounts
        ]

    hosp_plain = _build_plain_hospitalization(encounter)
    if hosp_plain:
        result["hospitalization"] = hosp_plain

    if encounter.locations:
        result["location"] = [
            {
                "location_id": loc.location_id,
                "location_display": loc.location_display,
                "status": loc.status.value if loc.status else None,
                "physical_type_system": loc.physical_type_system,
                "physical_type_code": loc.physical_type_code,
                "physical_type_display": loc.physical_type_display,
                "physical_type_text": loc.physical_type_text,
                "period_start": loc.period_start.isoformat() if loc.period_start else None,
                "period_end": loc.period_end.isoformat() if loc.period_end else None,
            }
            for loc in encounter.locations
        ]

    return {k: v for k, v in result.items() if v is not None}


def _build_plain_hospitalization(encounter: "EncounterModel") -> dict:
    fields = [
        "hosp_pre_admission_identifier_system", "hosp_pre_admission_identifier_value",
        "hosp_origin_type", "hosp_origin_id", "hosp_origin_display",
        "hosp_admit_source_system", "hosp_admit_source_code", "hosp_admit_source_display", "hosp_admit_source_text",
        "hosp_re_admission_system", "hosp_re_admission_code", "hosp_re_admission_display", "hosp_re_admission_text",
        "hosp_destination_type", "hosp_destination_id", "hosp_destination_display",
        "hosp_discharge_disposition_system", "hosp_discharge_disposition_code",
        "hosp_discharge_disposition_display", "hosp_discharge_disposition_text",
    ]
    has_any = any(getattr(encounter, f, None) for f in fields)
    has_children = bool(
        encounter.hosp_diet_preferences
        or encounter.hosp_special_arrangements
        or encounter.hosp_special_courtesies
    )
    if not has_any and not has_children:
        return {}

    hosp: dict = {
        "pre_admission_identifier_system": encounter.hosp_pre_admission_identifier_system,
        "pre_admission_identifier_value": encounter.hosp_pre_admission_identifier_value,
        "origin_type": encounter.hosp_origin_type,
        "origin_id": encounter.hosp_origin_id,
        "origin_display": encounter.hosp_origin_display,
        "admit_source_system": encounter.hosp_admit_source_system,
        "admit_source_code": encounter.hosp_admit_source_code,
        "admit_source_display": encounter.hosp_admit_source_display,
        "admit_source_text": encounter.hosp_admit_source_text,
        "re_admission_system": encounter.hosp_re_admission_system,
        "re_admission_code": encounter.hosp_re_admission_code,
        "re_admission_display": encounter.hosp_re_admission_display,
        "re_admission_text": encounter.hosp_re_admission_text,
        "destination_type": encounter.hosp_destination_type,
        "destination_id": encounter.hosp_destination_id,
        "destination_display": encounter.hosp_destination_display,
        "discharge_disposition_system": encounter.hosp_discharge_disposition_system,
        "discharge_disposition_code": encounter.hosp_discharge_disposition_code,
        "discharge_disposition_display": encounter.hosp_discharge_disposition_display,
        "discharge_disposition_text": encounter.hosp_discharge_disposition_text,
    }

    if encounter.hosp_diet_preferences:
        hosp["diet_preference"] = [
            {"coding_system": dp.coding_system, "coding_code": dp.coding_code,
             "coding_display": dp.coding_display, "text": dp.text}
            for dp in encounter.hosp_diet_preferences
        ]
    if encounter.hosp_special_arrangements:
        hosp["special_arrangement"] = [
            {"coding_system": sa.coding_system, "coding_code": sa.coding_code,
             "coding_display": sa.coding_display, "text": sa.text}
            for sa in encounter.hosp_special_arrangements
        ]
    if encounter.hosp_special_courtesies:
        hosp["special_courtesy"] = [
            {"coding_system": sc.coding_system, "coding_code": sc.coding_code,
             "coding_display": sc.coding_display, "text": sc.text}
            for sc in encounter.hosp_special_courtesies
        ]

    return {k: v for k, v in hosp.items() if v is not None}
