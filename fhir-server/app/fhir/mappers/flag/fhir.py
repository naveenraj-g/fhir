"""FHIR R4 (camelCase) builders for Flag."""

from __future__ import annotations

from app.fhir.datatypes import fhir_enum, fhir_identifier


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


def fhir_flag_identifier(i) -> dict:
    return fhir_identifier(i)


def fhir_flag_category(c) -> dict:
    return _cc(c.coding_system, c.coding_code, c.coding_display, c.text) or {}


def to_fhir_flag(flag) -> dict:
    result: dict = {
        "resourceType": "Flag",
        "id": str(flag.flag_id),
        "status": fhir_enum(flag.status),
    }
    if flag.identifiers:
        result["identifier"] = [fhir_flag_identifier(i) for i in flag.identifiers]
    if flag.categories:
        result["category"] = [fhir_flag_category(c) for c in flag.categories]

    code = _cc(flag.code_system, flag.code_code, flag.code_display, flag.code_text)
    if code:
        result["code"] = code
    subject = _ref(flag.subject_type, flag.subject_id, flag.subject_display)
    if subject:
        result["subject"] = subject
    if flag.period_start or flag.period_end:
        result["period"] = {k: v for k, v in {
            "start": flag.period_start.isoformat() if flag.period_start else None,
            "end": flag.period_end.isoformat() if flag.period_end else None,
        }.items() if v}
    if flag.encounter_id is not None:
        enc = {"reference": f"Encounter/{flag.encounter_id}"}
        if flag.encounter_display:
            enc["display"] = flag.encounter_display
        result["encounter"] = enc
    author = _ref(flag.author_type, flag.author_id, flag.author_display)
    if author:
        result["author"] = author
    return result
