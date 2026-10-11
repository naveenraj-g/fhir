"""FHIR R4 (camelCase) builders for CareTeam."""

from __future__ import annotations

from app.fhir.datatypes import fhir_enum, fhir_identifier, fhir_telecom


def _cc(system, code, display, text) -> dict | None:
    coding = {k: v for k, v in {"system": system, "code": code, "display": display}.items() if v}
    entry: dict = {}
    if coding:
        entry["coding"] = [coding]
    if text:
        entry["text"] = text
    return entry or None


def _ref(ref_type, ref_id, display) -> dict | None:
    entry: dict = {}
    if ref_type is not None and ref_id is not None:
        entry["reference"] = f"{fhir_enum(ref_type)}/{ref_id}"
    if display:
        entry["display"] = display
    return entry or None


def _period(start, end) -> dict | None:
    out = {k: v.isoformat() for k, v in (("start", start), ("end", end)) if v}
    return out or None


def fhir_care_team_cc(c) -> dict:
    """CodeableConcept list row (category / participant.role / reasonCode)."""
    return _cc(c.coding_system, c.coding_code, c.coding_display, c.text) or {}


def fhir_care_team_reference(r) -> dict:
    """Reference list row (reasonReference / managingOrganization)."""
    return _ref(r.reference_type, r.reference_id, r.reference_display) or {}


def fhir_care_team_participant(p) -> dict:
    entry: dict = {}
    roles = [fhir_care_team_cc(r) for r in (p.roles or [])]
    if roles:
        entry["role"] = roles
    member = _ref(p.member_type, p.member_id, p.member_display)
    if member:
        entry["member"] = member
    behalf = _ref(p.on_behalf_of_type, p.on_behalf_of_id, p.on_behalf_of_display)
    if behalf:
        entry["onBehalfOf"] = behalf
    period = _period(p.period_start, p.period_end)
    if period:
        entry["period"] = period
    return entry


def fhir_care_team_note(n) -> dict:
    entry: dict = {"text": n.text}
    if n.time:
        entry["time"] = n.time.isoformat()
    if n.author_string:
        entry["authorString"] = n.author_string
    else:
        ref = _ref(n.author_reference_type, n.author_reference_id, n.author_reference_display)
        if ref:
            entry["authorReference"] = ref
    return entry


def to_fhir_care_team(ct) -> dict:
    result: dict = {
        "resourceType": "CareTeam",
        "id": str(ct.care_team_id),
        "status": fhir_enum(ct.status),
        "name": ct.name,
        "subject": _ref(ct.subject_type, ct.subject_id, ct.subject_display),
        "encounter": _ref(ct.encounter_type, ct.encounter_id, ct.encounter_display),
        "period": _period(ct.period_start, ct.period_end),
        "identifier": [fhir_identifier(i) for i in (ct.identifiers or [])],
        "category": [fhir_care_team_cc(c) for c in (ct.categories or [])],
        "participant": [fhir_care_team_participant(p) for p in (ct.participants or [])],
        "reasonCode": [fhir_care_team_cc(c) for c in (ct.reason_codes or [])],
        "reasonReference": [fhir_care_team_reference(r) for r in (ct.reason_references or [])],
        "managingOrganization": [fhir_care_team_reference(r) for r in (ct.managing_organizations or [])],
        "telecom": [fhir_telecom(t) for t in (ct.telecoms or [])],
        "note": [fhir_care_team_note(n) for n in (ct.notes or [])],
    }
    return {k: v for k, v in result.items() if v is not None and v != [] and v != {}}
