"""Plain (snake_case) builders for Flag — field names mirror the input schema."""

from __future__ import annotations

from app.fhir.datatypes import fhir_enum, plain_identifier


def _iso(v):
    return v.isoformat() if v is not None else None


def plain_flag_identifier(i) -> dict:
    return {"id": i.id, **plain_identifier(i)}


def plain_flag_category(c) -> dict:
    return {
        "id": c.id,
        "coding_system": c.coding_system,
        "coding_code": c.coding_code,
        "coding_display": c.coding_display,
        "text": c.text,
    }


def to_plain_flag(flag) -> dict:
    return {
        "id": flag.flag_id,
        "status": fhir_enum(flag.status),
        "code_system": flag.code_system,
        "code_code": flag.code_code,
        "code_display": flag.code_display,
        "code_text": flag.code_text,
        "subject_type": fhir_enum(flag.subject_type),
        "subject_id": flag.subject_id,
        "subject_display": flag.subject_display,
        "period_start": _iso(flag.period_start),
        "period_end": _iso(flag.period_end),
        "encounter_type": fhir_enum(flag.encounter_type),
        "encounter_id": flag.encounter_id,
        "encounter_display": flag.encounter_display,
        "author_type": fhir_enum(flag.author_type),
        "author_id": flag.author_id,
        "author_display": flag.author_display,
        "identifier": [plain_flag_identifier(i) for i in (flag.identifiers or [])],
        "category": [plain_flag_category(c) for c in (flag.categories or [])],
        "user_id": flag.user_id,
        "org_id": flag.org_id,
        "created_at": _iso(flag.created_at),
        "updated_at": _iso(flag.updated_at),
        "created_by": flag.created_by,
        "updated_by": flag.updated_by,
    }
