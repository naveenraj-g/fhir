from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.encounter.encounter import EncounterModel


def to_plain_encounter(encounter: "EncounterModel") -> dict:
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

    if encounter.length_value is not None or encounter.length_code:
        result["length"] = {
            "value": encounter.length_value,
            "comparator": encounter.length_comparator,
            "unit": encounter.length_unit,
            "system": encounter.length_system,
            "code": encounter.length_code,
        }

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
