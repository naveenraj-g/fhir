"""Plain (snake_case) builders for RiskAssessment — field names mirror the input schema."""

from __future__ import annotations

from app.fhir.datatypes import fhir_enum, plain_identifier


def _iso(v):
    return v.isoformat() if v is not None else None


def plain_risk_identifier(i) -> dict:
    return {"id": i.id, **plain_identifier(i)}


def plain_risk_reason_code(r) -> dict:
    return {
        "id": r.id,
        "coding_system": r.coding_system,
        "coding_code": r.coding_code,
        "coding_display": r.coding_display,
        "text": r.text,
    }


def plain_risk_reference(r) -> dict:
    """reasonReference / basis child row."""
    return {
        "id": r.id,
        "reference_type": fhir_enum(r.reference_type),
        "reference_id": r.reference_id,
        "reference_display": r.reference_display,
    }


def plain_risk_prediction(p) -> dict:
    return {
        "id": p.id,
        "outcome_system": p.outcome_system,
        "outcome_code": p.outcome_code,
        "outcome_display": p.outcome_display,
        "outcome_text": p.outcome_text,
        "probability_decimal": p.probability_decimal,
        "probability_range_low_value": p.probability_range_low_value,
        "probability_range_low_unit": p.probability_range_low_unit,
        "probability_range_low_system": p.probability_range_low_system,
        "probability_range_low_code": p.probability_range_low_code,
        "probability_range_high_value": p.probability_range_high_value,
        "probability_range_high_unit": p.probability_range_high_unit,
        "probability_range_high_system": p.probability_range_high_system,
        "probability_range_high_code": p.probability_range_high_code,
        "qualitative_risk_system": p.qualitative_risk_system,
        "qualitative_risk_code": p.qualitative_risk_code,
        "qualitative_risk_display": p.qualitative_risk_display,
        "qualitative_risk_text": p.qualitative_risk_text,
        "relative_risk": p.relative_risk,
        "when_period_start": _iso(p.when_period_start),
        "when_period_end": _iso(p.when_period_end),
        "when_range_low_value": p.when_range_low_value,
        "when_range_low_unit": p.when_range_low_unit,
        "when_range_low_system": p.when_range_low_system,
        "when_range_low_code": p.when_range_low_code,
        "when_range_high_value": p.when_range_high_value,
        "when_range_high_unit": p.when_range_high_unit,
        "when_range_high_system": p.when_range_high_system,
        "when_range_high_code": p.when_range_high_code,
        "rationale": p.rationale,
    }


def plain_risk_note(n) -> dict:
    return {
        "id": n.id,
        "text": n.text,
        "time": _iso(n.time),
        "author_string": n.author_string,
        "author_reference_type": fhir_enum(n.author_reference_type),
        "author_reference_id": n.author_reference_id,
        "author_reference_display": n.author_reference_display,
    }


def to_plain_risk_assessment(ra) -> dict:
    return {
        "id": ra.risk_assessment_id,
        "status": fhir_enum(ra.status),
        "method_system": ra.method_system,
        "method_code": ra.method_code,
        "method_display": ra.method_display,
        "method_text": ra.method_text,
        "code_system": ra.code_system,
        "code_code": ra.code_code,
        "code_display": ra.code_display,
        "code_text": ra.code_text,
        "based_on_type": ra.based_on_type,
        "based_on_id": ra.based_on_id,
        "based_on_display": ra.based_on_display,
        "parent_type": ra.parent_type,
        "parent_id": ra.parent_id,
        "parent_display": ra.parent_display,
        "subject_type": fhir_enum(ra.subject_type),
        "subject_id": ra.subject_id,
        "subject_display": ra.subject_display,
        "encounter_type": fhir_enum(ra.encounter_type),
        "encounter_id": ra.encounter_id,
        "encounter_display": ra.encounter_display,
        "occurrence_datetime": _iso(ra.occurrence_datetime),
        "occurrence_period_start": _iso(ra.occurrence_period_start),
        "occurrence_period_end": _iso(ra.occurrence_period_end),
        "condition_type": fhir_enum(ra.condition_type),
        "condition_id": ra.condition_id,
        "condition_display": ra.condition_display,
        "performer_type": fhir_enum(ra.performer_type),
        "performer_id": ra.performer_id,
        "performer_display": ra.performer_display,
        "mitigation": ra.mitigation,
        "identifier": [plain_risk_identifier(i) for i in (ra.identifiers or [])],
        "reason_code": [plain_risk_reason_code(r) for r in (ra.reason_codes or [])],
        "reason_reference": [plain_risk_reference(r) for r in (ra.reason_references or [])],
        "basis": [plain_risk_reference(b) for b in (ra.basis or [])],
        "prediction": [plain_risk_prediction(p) for p in (ra.predictions or [])],
        "note": [plain_risk_note(n) for n in (ra.notes or [])],
        "user_id": ra.user_id,
        "org_id": ra.org_id,
        "created_at": _iso(ra.created_at),
        "updated_at": _iso(ra.updated_at),
        "created_by": ra.created_by,
        "updated_by": ra.updated_by,
    }
