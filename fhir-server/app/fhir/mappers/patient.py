from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.patient.patient import PatientModel


def _split(value: str | None) -> list[str]:
    """Split a comma-separated string back into a list, stripping whitespace."""
    if not value:
        return []
    return [s.strip() for s in value.split(",") if s.strip()]


def _fhir_human_name(n) -> dict:
    entry: dict = {}
    if n.use:
        entry["use"] = n.use
    if n.text:
        entry["text"] = n.text
    if n.family:
        entry["family"] = n.family
    given = _split(n.given)
    if given:
        entry["given"] = given
    prefix = _split(n.prefix)
    if prefix:
        entry["prefix"] = prefix
    suffix = _split(n.suffix)
    if suffix:
        entry["suffix"] = suffix
    if n.period_start or n.period_end:
        entry["period"] = {k: v for k, v in {
            "start": n.period_start.isoformat() if n.period_start else None,
            "end": n.period_end.isoformat() if n.period_end else None,
        }.items() if v}
    return entry


def _fhir_address(a) -> dict:
    entry: dict = {}
    if a.use:
        entry["use"] = a.use
    if a.type:
        entry["type"] = a.type
    if a.text:
        entry["text"] = a.text
    lines = _split(a.line)
    if lines:
        entry["line"] = lines
    if a.city:
        entry["city"] = a.city
    if a.district:
        entry["district"] = a.district
    if a.state:
        entry["state"] = a.state
    if a.postal_code:
        entry["postalCode"] = a.postal_code
    if a.country:
        entry["country"] = a.country
    if a.period_start or a.period_end:
        entry["period"] = {k: v for k, v in {
            "start": a.period_start.isoformat() if a.period_start else None,
            "end": a.period_end.isoformat() if a.period_end else None,
        }.items() if v}
    return entry


def _fhir_telecom(t) -> dict:
    entry: dict = {}
    if t.system:
        entry["system"] = t.system
    if t.value:
        entry["value"] = t.value
    if t.use:
        entry["use"] = t.use
    if t.rank is not None:
        entry["rank"] = t.rank
    if t.period_start or t.period_end:
        entry["period"] = {k: v for k, v in {
            "start": t.period_start.isoformat() if t.period_start else None,
            "end": t.period_end.isoformat() if t.period_end else None,
        }.items() if v}
    return entry


def to_fhir_patient(patient: "PatientModel") -> dict:
    result: dict = {
        "resourceType": "Patient",
        "id": str(patient.patient_id),
        "active": patient.active,
        "gender": patient.gender.value if patient.gender else None,
        "birthDate": patient.birth_date.isoformat() if patient.birth_date else None,
        "deceasedBoolean": patient.deceased_boolean,
        "deceasedDateTime": patient.deceased_datetime.isoformat() if patient.deceased_datetime else None,
    }

    # maritalStatus
    if patient.marital_status_code or patient.marital_status_text:
        cc: dict = {}
        if patient.marital_status_system or patient.marital_status_code:
            cc["coding"] = [{k: v for k, v in {
                "system": patient.marital_status_system,
                "code": patient.marital_status_code,
                "display": patient.marital_status_display,
            }.items() if v}]
        if patient.marital_status_text:
            cc["text"] = patient.marital_status_text
        result["maritalStatus"] = cc

    # multipleBirth[x]
    if patient.multiple_birth_integer is not None:
        result["multipleBirthInteger"] = patient.multiple_birth_integer
    elif patient.multiple_birth_boolean is not None:
        result["multipleBirthBoolean"] = patient.multiple_birth_boolean

    # managingOrganization
    if patient.managing_organization_id:
        result["managingOrganization"] = {k: v for k, v in {
            "reference": f"Organization/{patient.managing_organization_id}",
            "display": patient.managing_organization_display,
        }.items() if v}

    # name
    if patient.names:
        result["name"] = [_fhir_human_name(n) for n in patient.names]

    # identifier
    if patient.identifiers:
        entries = []
        for i in patient.identifiers:
            entry: dict = {}
            if i.use:
                entry["use"] = i.use
            if i.type_system or i.type_code:
                entry["type"] = {"coding": [{k: v for k, v in {
                    "system": i.type_system,
                    "code": i.type_code,
                    "display": i.type_display,
                }.items() if v}]}
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
            entries.append(entry)
        result["identifier"] = entries

    # telecom
    if patient.telecoms:
        result["telecom"] = [_fhir_telecom(t) for t in patient.telecoms]

    # address
    if patient.addresses:
        result["address"] = [_fhir_address(a) for a in patient.addresses]

    # photo
    if patient.photos:
        result["photo"] = [{k: v for k, v in {
            "contentType": p.content_type,
            "language": p.language,
            "data": p.data,
            "url": p.url,
            "size": p.size,
            "hash": p.hash,
            "title": p.title,
            "creation": p.creation.isoformat() if p.creation else None,
        }.items() if v is not None} for p in patient.photos]

    # contact
    if patient.contacts:
        contacts = []
        for c in patient.contacts:
            ce: dict = {}
            if c.relationships:
                ce["relationship"] = [{k: v for k, v in {
                    "coding": [{k2: v2 for k2, v2 in {
                        "system": r.coding_system,
                        "code": r.coding_code,
                        "display": r.coding_display,
                    }.items() if v2}],
                    "text": r.text,
                }.items() if v} for r in c.relationships]
            name_entry: dict = {}
            if c.name_use:
                name_entry["use"] = c.name_use
            if c.name_text:
                name_entry["text"] = c.name_text
            if c.name_family:
                name_entry["family"] = c.name_family
            given = _split(c.name_given)
            if given:
                name_entry["given"] = given
            prefix = _split(c.name_prefix)
            if prefix:
                name_entry["prefix"] = prefix
            suffix = _split(c.name_suffix)
            if suffix:
                name_entry["suffix"] = suffix
            if name_entry:
                ce["name"] = name_entry
            if c.telecoms:
                ce["telecom"] = [_fhir_telecom(t) for t in c.telecoms]
            addr_entry: dict = {}
            if c.address_use:
                addr_entry["use"] = c.address_use
            if c.address_type:
                addr_entry["type"] = c.address_type
            if c.address_text:
                addr_entry["text"] = c.address_text
            addr_lines = _split(c.address_line)
            if addr_lines:
                addr_entry["line"] = addr_lines
            if c.address_city:
                addr_entry["city"] = c.address_city
            if c.address_district:
                addr_entry["district"] = c.address_district
            if c.address_state:
                addr_entry["state"] = c.address_state
            if c.address_postal_code:
                addr_entry["postalCode"] = c.address_postal_code
            if c.address_country:
                addr_entry["country"] = c.address_country
            if c.address_period_start or c.address_period_end:
                addr_entry["period"] = {k: v for k, v in {
                    "start": c.address_period_start.isoformat() if c.address_period_start else None,
                    "end": c.address_period_end.isoformat() if c.address_period_end else None,
                }.items() if v}
            if addr_entry:
                ce["address"] = addr_entry
            if c.gender:
                ce["gender"] = c.gender
            if c.organization_id:
                ce["organization"] = {k: v for k, v in {
                    "reference": f"Organization/{c.organization_id}",
                    "display": c.organization_display,
                }.items() if v}
            if c.period_start or c.period_end:
                ce["period"] = {k: v for k, v in {
                    "start": c.period_start.isoformat() if c.period_start else None,
                    "end": c.period_end.isoformat() if c.period_end else None,
                }.items() if v}
            contacts.append(ce)
        result["contact"] = contacts

    # communication
    if patient.communications:
        result["communication"] = [{k: v for k, v in {
            "language": {k2: v2 for k2, v2 in {
                "coding": [{k3: v3 for k3, v3 in {
                    "system": cm.language_system,
                    "code": cm.language_code,
                    "display": cm.language_display,
                }.items() if v3}],
                "text": cm.language_text,
            }.items() if v2},
            "preferred": cm.preferred,
        }.items() if v is not None} for cm in patient.communications]

    # generalPractitioner
    if patient.general_practitioners:
        result["generalPractitioner"] = [{k: v for k, v in {
            "reference": f"{gp.reference_type.value}/{gp.reference_id}" if gp.reference_type and gp.reference_id else None,
            "display": gp.reference_display,
        }.items() if v} for gp in patient.general_practitioners]

    # link
    if patient.links:
        result["link"] = [{k: v for k, v in {
            "other": {k2: v2 for k2, v2 in {
                "reference": f"{lk.other_type.value}/{lk.other_id}" if lk.other_type and lk.other_id else None,
                "display": lk.other_display,
            }.items() if v2},
            "type": lk.type.value if lk.type else None,
        }.items() if v} for lk in patient.links]

    return {k: v for k, v in result.items() if v is not None}


def to_plain_patient(patient: "PatientModel") -> dict:
    result: dict = {
        "id": patient.patient_id,
        "user_id": patient.user_id,
        "org_id": patient.org_id,
        "active": patient.active,
        "gender": patient.gender.value if patient.gender else None,
        "birth_date": patient.birth_date.isoformat() if patient.birth_date else None,
        "deceased_boolean": patient.deceased_boolean,
        "deceased_datetime": patient.deceased_datetime.isoformat() if patient.deceased_datetime else None,
        "marital_status_system": patient.marital_status_system,
        "marital_status_code": patient.marital_status_code,
        "marital_status_display": patient.marital_status_display,
        "marital_status_text": patient.marital_status_text,
        "multiple_birth_boolean": patient.multiple_birth_boolean,
        "multiple_birth_integer": patient.multiple_birth_integer,
        "managing_organization_id": patient.managing_organization_id,
        "managing_organization_display": patient.managing_organization_display,
    }

    if patient.names:
        result["name"] = [{
            "use": n.use,
            "text": n.text,
            "family": n.family,
            "given": _split(n.given),
            "prefix": _split(n.prefix),
            "suffix": _split(n.suffix),
            "period_start": n.period_start.isoformat() if n.period_start else None,
            "period_end": n.period_end.isoformat() if n.period_end else None,
        } for n in patient.names]

    if patient.identifiers:
        result["identifier"] = [{
            "use": i.use,
            "type_system": i.type_system,
            "type_code": i.type_code,
            "type_display": i.type_display,
            "system": i.system,
            "value": i.value,
            "period_start": i.period_start.isoformat() if i.period_start else None,
            "period_end": i.period_end.isoformat() if i.period_end else None,
            "assigner": i.assigner,
        } for i in patient.identifiers]

    if patient.telecoms:
        result["telecom"] = [{
            "system": t.system,
            "value": t.value,
            "use": t.use,
            "rank": t.rank,
            "period_start": t.period_start.isoformat() if t.period_start else None,
            "period_end": t.period_end.isoformat() if t.period_end else None,
        } for t in patient.telecoms]

    if patient.addresses:
        result["address"] = [{
            "use": a.use,
            "type": a.type,
            "text": a.text,
            "line": _split(a.line),
            "city": a.city,
            "district": a.district,
            "state": a.state,
            "postal_code": a.postal_code,
            "country": a.country,
            "period_start": a.period_start.isoformat() if a.period_start else None,
            "period_end": a.period_end.isoformat() if a.period_end else None,
        } for a in patient.addresses]

    if patient.photos:
        result["photo"] = [{
            "content_type": p.content_type,
            "language": p.language,
            "data": p.data,
            "url": p.url,
            "size": p.size,
            "hash": p.hash,
            "title": p.title,
            "creation": p.creation.isoformat() if p.creation else None,
        } for p in patient.photos]

    if patient.contacts:
        result["contact"] = [{
            "relationship": [{"coding_system": r.coding_system, "coding_code": r.coding_code,
                               "coding_display": r.coding_display, "text": r.text}
                              for r in c.relationships] if c.relationships else None,
            "name_use": c.name_use,
            "name_text": c.name_text,
            "name_family": c.name_family,
            "name_given": _split(c.name_given),
            "name_prefix": _split(c.name_prefix),
            "name_suffix": _split(c.name_suffix),
            "telecom": [{"system": t.system, "value": t.value, "use": t.use, "rank": t.rank,
                          "period_start": t.period_start.isoformat() if t.period_start else None,
                          "period_end": t.period_end.isoformat() if t.period_end else None}
                         for t in c.telecoms] if c.telecoms else None,
            "address_use": c.address_use,
            "address_type": c.address_type,
            "address_text": c.address_text,
            "address_line": _split(c.address_line),
            "address_city": c.address_city,
            "address_district": c.address_district,
            "address_state": c.address_state,
            "address_postal_code": c.address_postal_code,
            "address_country": c.address_country,
            "address_period_start": c.address_period_start.isoformat() if c.address_period_start else None,
            "address_period_end": c.address_period_end.isoformat() if c.address_period_end else None,
            "gender": c.gender,
            "organization_id": c.organization_id,
            "organization_display": c.organization_display,
            "period_start": c.period_start.isoformat() if c.period_start else None,
            "period_end": c.period_end.isoformat() if c.period_end else None,
        } for c in patient.contacts]

    if patient.communications:
        result["communication"] = [{
            "language_system": cm.language_system,
            "language_code": cm.language_code,
            "language_display": cm.language_display,
            "language_text": cm.language_text,
            "preferred": cm.preferred,
        } for cm in patient.communications]

    if patient.general_practitioners:
        result["general_practitioner"] = [{
            "reference_type": gp.reference_type.value if gp.reference_type else None,
            "reference_id": gp.reference_id,
            "reference_display": gp.reference_display,
        } for gp in patient.general_practitioners]

    if patient.links:
        result["link"] = [{
            "other_type": lk.other_type.value if lk.other_type else None,
            "other_id": lk.other_id,
            "other_display": lk.other_display,
            "type": lk.type.value if lk.type else None,
        } for lk in patient.links]

    return {k: v for k, v in result.items() if v is not None}
