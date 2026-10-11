"""Plain (snake_case) builders for CareTeam — field names mirror the input schema."""

from __future__ import annotations

from app.fhir.datatypes import fhir_enum, plain_identifier


def _iso(v):
    return v.isoformat() if v is not None else None


def plain_care_team_identifier(i) -> dict:
    return {"id": i.id, **plain_identifier(i)}


def plain_care_team_cc(c) -> dict:
    """CodeableConcept list row (category / participant.role / reasonCode)."""
    return {
        "id": c.id,
        "coding_system": c.coding_system,
        "coding_code": c.coding_code,
        "coding_display": c.coding_display,
        "text": c.text,
    }


def plain_care_team_reference(r) -> dict:
    """Reference list row (reasonReference / managingOrganization)."""
    return {
        "id": r.id,
        "reference_type": fhir_enum(r.reference_type),
        "reference_id": r.reference_id,
        "reference_display": r.reference_display,
    }


def plain_care_team_participant(p) -> dict:
    return {
        "id": p.id,
        "role": [plain_care_team_cc(r) for r in (p.roles or [])],
        "member_type": fhir_enum(p.member_type),
        "member_id": p.member_id,
        "member_display": p.member_display,
        "on_behalf_of_type": fhir_enum(p.on_behalf_of_type),
        "on_behalf_of_id": p.on_behalf_of_id,
        "on_behalf_of_display": p.on_behalf_of_display,
        "period_start": _iso(p.period_start),
        "period_end": _iso(p.period_end),
    }


def plain_care_team_telecom(t) -> dict:
    return {
        "id": t.id,
        "system": t.system,
        "value": t.value,
        "use": t.use,
        "rank": t.rank,
        "period_start": _iso(t.period_start),
        "period_end": _iso(t.period_end),
    }


def plain_care_team_note(n) -> dict:
    return {
        "id": n.id,
        "text": n.text,
        "time": _iso(n.time),
        "author_string": n.author_string,
        "author_reference_type": n.author_reference_type,
        "author_reference_id": n.author_reference_id,
        "author_reference_display": n.author_reference_display,
    }


def to_plain_care_team(ct) -> dict:
    return {
        "id": ct.care_team_id,
        "status": fhir_enum(ct.status),
        "name": ct.name,
        "subject_type": fhir_enum(ct.subject_type),
        "subject_id": ct.subject_id,
        "subject_display": ct.subject_display,
        "encounter_type": fhir_enum(ct.encounter_type),
        "encounter_id": ct.encounter_id,
        "encounter_display": ct.encounter_display,
        "period_start": _iso(ct.period_start),
        "period_end": _iso(ct.period_end),
        "identifier": [plain_care_team_identifier(i) for i in (ct.identifiers or [])],
        "category": [plain_care_team_cc(c) for c in (ct.categories or [])],
        "participant": [plain_care_team_participant(p) for p in (ct.participants or [])],
        "reason_code": [plain_care_team_cc(c) for c in (ct.reason_codes or [])],
        "reason_reference": [plain_care_team_reference(r) for r in (ct.reason_references or [])],
        "managing_organization": [plain_care_team_reference(r) for r in (ct.managing_organizations or [])],
        "telecom": [plain_care_team_telecom(t) for t in (ct.telecoms or [])],
        "note": [plain_care_team_note(n) for n in (ct.notes or [])],
        "user_id": ct.user_id,
        "org_id": ct.org_id,
        "created_at": _iso(ct.created_at),
        "updated_at": _iso(ct.updated_at),
        "created_by": ct.created_by,
        "updated_by": ct.updated_by,
    }
