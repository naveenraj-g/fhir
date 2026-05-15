from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.practitioner import PractitionerModel


def _split(value: str | None) -> list[str]:
    if not value:
        return []
    return [s.strip() for s in value.split(",") if s.strip()]


def to_fhir_practitioner(practitioner: "PractitionerModel") -> dict:
    result: dict = {
        "resourceType": "Practitioner",
        "id": str(practitioner.practitioner_id),
        "active": practitioner.active,
        "gender": practitioner.gender,
        "birthDate": practitioner.birth_date.isoformat() if practitioner.birth_date else None,
        "deceasedBoolean": practitioner.deceased_boolean,
        "deceasedDateTime": practitioner.deceased_datetime.isoformat() if practitioner.deceased_datetime else None,
    }

    # name (0..* HumanName)
    if practitioner.names:
        names = []
        for n in practitioner.names:
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
            names.append(entry)
        result["name"] = names

    # identifier (0..* Identifier)
    if practitioner.identifiers:
        entries = []
        for i in practitioner.identifiers:
            entry = {}
            if i.use:
                entry["use"] = i.use
            if i.type_system or i.type_code or i.type_text:
                type_cc: dict = {}
                if i.type_system or i.type_code:
                    type_cc["coding"] = [{k: v for k, v in {
                        "system": i.type_system,
                        "code": i.type_code,
                        "display": i.type_display,
                    }.items() if v}]
                if i.type_text:
                    type_cc["text"] = i.type_text
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
            entries.append(entry)
        result["identifier"] = entries

    # telecom (0..* ContactPoint)
    if practitioner.telecoms:
        tels = []
        for t in practitioner.telecoms:
            entry = {k: v for k, v in {
                "system": t.system,
                "value": t.value,
                "use": t.use,
                "rank": t.rank,
            }.items() if v is not None}
            if t.period_start or t.period_end:
                entry["period"] = {k: v for k, v in {
                    "start": t.period_start.isoformat() if t.period_start else None,
                    "end": t.period_end.isoformat() if t.period_end else None,
                }.items() if v}
            tels.append(entry)
        result["telecom"] = tels

    # address (0..* Address)
    if practitioner.addresses:
        addresses = []
        for a in practitioner.addresses:
            entry = {}
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
            addresses.append(entry)
        result["address"] = addresses

    # photo (0..* Attachment)
    if practitioner.photos:
        result["photo"] = [{k: v for k, v in {
            "contentType": p.content_type,
            "language": p.language,
            "data": p.data,
            "url": p.url,
            "size": p.size,
            "hash": p.hash,
            "title": p.title,
            "creation": p.creation.isoformat() if p.creation else None,
        }.items() if v is not None} for p in practitioner.photos]

    # qualification (0..* BackboneElement)
    if practitioner.qualifications:
        qualifications = []
        for q in practitioner.qualifications:
            entry = {}
            if q.identifiers:
                ident_list = []
                for qi in q.identifiers:
                    ident_entry = {}
                    if qi.use:
                        ident_entry["use"] = qi.use
                    if qi.type_system or qi.type_code or qi.type_text:
                        type_cc: dict = {}
                        if qi.type_system or qi.type_code:
                            type_cc["coding"] = [{k: v for k, v in {
                                "system": qi.type_system,
                                "code": qi.type_code,
                                "display": qi.type_display,
                            }.items() if v}]
                        if qi.type_text:
                            type_cc["text"] = qi.type_text
                        ident_entry["type"] = type_cc
                    if qi.system:
                        ident_entry["system"] = qi.system
                    if qi.value:
                        ident_entry["value"] = qi.value
                    if qi.period_start or qi.period_end:
                        ident_entry["period"] = {k: v for k, v in {
                            "start": qi.period_start.isoformat() if qi.period_start else None,
                            "end": qi.period_end.isoformat() if qi.period_end else None,
                        }.items() if v}
                    if qi.assigner:
                        ident_entry["assigner"] = {"display": qi.assigner}
                    ident_list.append(ident_entry)
                entry["identifier"] = ident_list
            code_cc: dict = {}
            if q.code_system or q.code_code:
                code_cc["coding"] = [{k: v for k, v in {
                    "system": q.code_system,
                    "code": q.code_code,
                    "display": q.code_display,
                }.items() if v}]
            if q.code_text:
                code_cc["text"] = q.code_text
            if code_cc:
                entry["code"] = code_cc
            if q.status_system or q.status_code or q.status_text:
                status_cc: dict = {}
                if q.status_system or q.status_code:
                    status_cc["coding"] = [{k: v for k, v in {
                        "system": q.status_system,
                        "code": q.status_code,
                        "display": q.status_display,
                    }.items() if v}]
                if q.status_text:
                    status_cc["text"] = q.status_text
                entry["status"] = status_cc
            if q.period_start or q.period_end:
                entry["period"] = {k: v for k, v in {
                    "start": q.period_start.isoformat() if q.period_start else None,
                    "end": q.period_end.isoformat() if q.period_end else None,
                }.items() if v}
            if q.issuer_type and q.issuer_id or q.issuer_display:
                entry["issuer"] = {k: v for k, v in {
                    "reference": f"{q.issuer_type.value}/{q.issuer_id}" if q.issuer_type and q.issuer_id else None,
                    "display": q.issuer_display,
                }.items() if v}
            qualifications.append(entry)
        result["qualification"] = qualifications

    # communication (0..* CodeableConcept)
    if practitioner.communications:
        comms = []
        for c in practitioner.communications:
            coding_entry = {k: v for k, v in {
                "system": c.language_system,
                "code": c.language_code,
                "display": c.language_display,
            }.items() if v}
            language_cc: dict = {}
            if coding_entry:
                language_cc["coding"] = [coding_entry]
            if c.language_text:
                language_cc["text"] = c.language_text
            entry: dict = {}
            if language_cc:
                entry["language"] = language_cc
            if c.preferred is not None:
                entry["preferred"] = c.preferred
            comms.append(entry)
        result["communication"] = comms

    return {k: v for k, v in result.items() if v is not None}


def to_plain_practitioner(practitioner: "PractitionerModel") -> dict:
    result: dict = {
        "id": practitioner.practitioner_id,
        "user_id": practitioner.user_id,
        "org_id": practitioner.org_id,
        "active": practitioner.active,
        "gender": practitioner.gender,
        "birth_date": practitioner.birth_date.isoformat() if practitioner.birth_date else None,
        "deceased_boolean": practitioner.deceased_boolean,
        "deceased_datetime": practitioner.deceased_datetime.isoformat() if practitioner.deceased_datetime else None,
        "created_at": practitioner.created_at.isoformat() if practitioner.created_at else None,
        "updated_at": practitioner.updated_at.isoformat() if practitioner.updated_at else None,
        "created_by": practitioner.created_by,
        "updated_by": practitioner.updated_by,
    }

    if practitioner.names:
        result["name"] = [{
            "use": n.use,
            "text": n.text,
            "family": n.family,
            "given": _split(n.given),
            "prefix": _split(n.prefix),
            "suffix": _split(n.suffix),
            "period_start": n.period_start.isoformat() if n.period_start else None,
            "period_end": n.period_end.isoformat() if n.period_end else None,
        } for n in practitioner.names]

    if practitioner.identifiers:
        result["identifier"] = [{
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
        } for i in practitioner.identifiers]

    if practitioner.telecoms:
        result["telecom"] = [{
            "system": t.system,
            "value": t.value,
            "use": t.use,
            "rank": t.rank,
            "period_start": t.period_start.isoformat() if t.period_start else None,
            "period_end": t.period_end.isoformat() if t.period_end else None,
        } for t in practitioner.telecoms]

    if practitioner.addresses:
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
        } for a in practitioner.addresses]

    if practitioner.photos:
        result["photo"] = [{
            "content_type": p.content_type,
            "language": p.language,
            "data": p.data,
            "url": p.url,
            "size": p.size,
            "hash": p.hash,
            "title": p.title,
            "creation": p.creation.isoformat() if p.creation else None,
        } for p in practitioner.photos]

    if practitioner.qualifications:
        result["qualification"] = [{
            "identifier": [{
                "use": qi.use,
                "type_system": qi.type_system,
                "type_code": qi.type_code,
                "type_display": qi.type_display,
                "type_text": qi.type_text,
                "system": qi.system,
                "value": qi.value,
                "period_start": qi.period_start.isoformat() if qi.period_start else None,
                "period_end": qi.period_end.isoformat() if qi.period_end else None,
                "assigner": qi.assigner,
            } for qi in q.identifiers] if q.identifiers else None,
            "code_system": q.code_system,
            "code_code": q.code_code,
            "code_display": q.code_display,
            "code_text": q.code_text,
            "status_system": q.status_system,
            "status_code": q.status_code,
            "status_display": q.status_display,
            "status_text": q.status_text,
            "period_start": q.period_start.isoformat() if q.period_start else None,
            "period_end": q.period_end.isoformat() if q.period_end else None,
            "issuer_type": q.issuer_type.value if q.issuer_type else None,
            "issuer_id": q.issuer_id,
            "issuer_display": q.issuer_display,
        } for q in practitioner.qualifications]

    if practitioner.communications:
        result["communication"] = [{
            "language_system": c.language_system,
            "language_code": c.language_code,
            "language_display": c.language_display,
            "language_text": c.language_text,
            "preferred": c.preferred,
        } for c in practitioner.communications]

    return {k: v for k, v in result.items() if v is not None}
