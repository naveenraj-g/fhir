from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.patient import PatientModel


def to_fhir_patient(patient: "PatientModel") -> dict:
    """
    Convert internal PatientModel (with relationships loaded) to a
    FHIR R4 Patient resource dict.

    Rules:
      - Uses patient_id (public) as the FHIR logical id — never the internal PK.
      - All sub-resources are mapped from normalised relationship tables.
      - None / empty values are stripped from the output.
    """
    result: dict = {
        "resourceType": "Patient",
        "id": str(patient.patient_id),
        "active": patient.active,
        "gender": patient.gender,
        "birthDate": patient.birth_date.isoformat() if patient.birth_date else None,
        "deceasedBoolean": patient.deceased_boolean,
        "deceasedDateTime": patient.deceased_datetime.isoformat() if patient.deceased_datetime else None,
    }

    # name
    if patient.given_name or patient.family_name:
        result["name"] = [
            {
                "use": "official",
                "family": patient.family_name,
                "given": [patient.given_name] if patient.given_name else [],
            }
        ]

    # identifier
    if patient.identifiers:
        entries = []
        for i in patient.identifiers:
            entry: dict = {}
            if i.use:
                entry["use"] = i.use
            if i.type:
                type_entry: dict = {}
                if i.type.codings:
                    type_entry["coding"] = [
                        {k: v for k, v in {
                            "system": c.system,
                            "version": c.version,
                            "code": c.code,
                            "display": c.display,
                            "userSelected": c.user_selected,
                        }.items() if v is not None}
                        for c in i.type.codings
                    ]
                if i.type.text:
                    type_entry["text"] = i.type.text
                if type_entry:
                    entry["type"] = type_entry
            if i.system:
                entry["system"] = i.system
            if i.value:
                entry["value"] = i.value
            if i.period_start or i.period_end:
                entry["period"] = {k: v for k, v in {
                    "start": i.period_start.isoformat() if i.period_start else None,
                    "end": i.period_end.isoformat() if i.period_end else None,
                }.items() if v is not None}
            if i.assigner:
                entry["assigner"] = {"display": i.assigner}
            entries.append(entry)
        result["identifier"] = entries

    # telecom
    if patient.telecoms:
        result["telecom"] = [
            {k: v for k, v in {"system": t.system, "value": t.value, "use": t.use}.items() if v is not None}
            for t in patient.telecoms
        ]

    # address
    if patient.addresses:
        result["address"] = [
            {k: v for k, v in {
                "line": [a.line] if a.line else [],
                "city": a.city,
                "state": a.state,
                "postalCode": a.postal_code,
                "country": a.country,
            }.items() if v}
            for a in patient.addresses
        ]

    # strip top-level None values
    return {k: v for k, v in result.items() if v is not None}


def to_plain_patient(patient: "PatientModel") -> dict:
    """
    Return the patient as a flat, snake_case JSON object — no FHIR conventions.
    Uses public patient_id as `id`. All sub-resources keep their DB field names.
    """
    result: dict = {
        "id": patient.patient_id,
        "user_id": patient.user_id,
        "org_id": patient.org_id,
        "given_name": patient.given_name,
        "family_name": patient.family_name,
        "gender": patient.gender.value if patient.gender else None,
        "birth_date": patient.birth_date.isoformat() if patient.birth_date else None,
        "active": patient.active,
        "deceased_boolean": patient.deceased_boolean,
        "deceased_datetime": patient.deceased_datetime.isoformat() if patient.deceased_datetime else None,
    }

    if patient.identifiers:
        entries = []
        for i in patient.identifiers:
            entry: dict = {
                "use": i.use,
                "system": i.system,
                "value": i.value,
                "period_start": i.period_start.isoformat() if i.period_start else None,
                "period_end": i.period_end.isoformat() if i.period_end else None,
                "assigner": i.assigner,
            }
            if i.type:
                type_entry: dict = {"text": i.type.text}
                if i.type.codings:
                    type_entry["coding"] = [
                        {
                            "system": c.system,
                            "version": c.version,
                            "code": c.code,
                            "display": c.display,
                            "user_selected": c.user_selected,
                        }
                        for c in i.type.codings
                    ]
                entry["type"] = {k: v for k, v in type_entry.items() if v is not None}
            entries.append({k: v for k, v in entry.items() if v is not None})
        result["identifier"] = entries

    if patient.telecoms:
        result["telecom"] = [
            {"system": t.system, "value": t.value, "use": t.use}
            for t in patient.telecoms
        ]

    if patient.addresses:
        result["address"] = [
            {
                "line": a.line,
                "city": a.city,
                "state": a.state,
                "postal_code": a.postal_code,
                "country": a.country,
            }
            for a in patient.addresses
        ]

    return {k: v for k, v in result.items() if v is not None}
