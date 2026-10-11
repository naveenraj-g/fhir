"""FHIR R4 (camelCase) builders for RiskAssessment."""

from __future__ import annotations

from app.fhir.datatypes import fhir_enum, fhir_identifier


def _strip(d: dict) -> dict:
    """Drop None values (keeps 0 / False)."""
    return {k: v for k, v in d.items() if v is not None}


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


def _quantity(value, unit, system, code) -> dict | None:
    return _strip({"value": value, "unit": unit, "system": system, "code": code}) or None


def _range(low: dict | None, high: dict | None) -> dict | None:
    entry = {}
    if low:
        entry["low"] = low
    if high:
        entry["high"] = high
    return entry or None


def fhir_risk_identifier(i) -> dict:
    return fhir_identifier(i)


def fhir_risk_reason_code(r) -> dict:
    return _cc(r.coding_system, r.coding_code, r.coding_display, r.text) or {}


def fhir_risk_reference(r) -> dict:
    """reasonReference / basis child row -> Reference."""
    return _ref(r.reference_type, r.reference_id, r.reference_display) or {}


def fhir_risk_prediction(p) -> dict:
    entry: dict = {}
    outcome = _cc(p.outcome_system, p.outcome_code, p.outcome_display, p.outcome_text)
    if outcome:
        entry["outcome"] = outcome
    if p.probability_decimal is not None:
        entry["probabilityDecimal"] = p.probability_decimal
    else:
        rng = _range(
            _quantity(p.probability_range_low_value, p.probability_range_low_unit,
                      p.probability_range_low_system, p.probability_range_low_code),
            _quantity(p.probability_range_high_value, p.probability_range_high_unit,
                      p.probability_range_high_system, p.probability_range_high_code),
        )
        if rng:
            entry["probabilityRange"] = rng
    qualitative = _cc(p.qualitative_risk_system, p.qualitative_risk_code, p.qualitative_risk_display, p.qualitative_risk_text)
    if qualitative:
        entry["qualitativeRisk"] = qualitative
    if p.relative_risk is not None:
        entry["relativeRisk"] = p.relative_risk
    if p.when_period_start or p.when_period_end:
        entry["whenPeriod"] = _strip({
            "start": p.when_period_start.isoformat() if p.when_period_start else None,
            "end": p.when_period_end.isoformat() if p.when_period_end else None,
        })
    else:
        rng = _range(
            _quantity(p.when_range_low_value, p.when_range_low_unit, p.when_range_low_system, p.when_range_low_code),
            _quantity(p.when_range_high_value, p.when_range_high_unit, p.when_range_high_system, p.when_range_high_code),
        )
        if rng:
            entry["whenRange"] = rng
    if p.rationale:
        entry["rationale"] = p.rationale
    return entry


def fhir_risk_note(n) -> dict:
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


def to_fhir_risk_assessment(ra) -> dict:
    result: dict = {
        "resourceType": "RiskAssessment",
        "id": str(ra.risk_assessment_id),
        "status": fhir_enum(ra.status),
        "mitigation": ra.mitigation,
    }
    if ra.identifiers:
        result["identifier"] = [fhir_risk_identifier(i) for i in ra.identifiers]

    for key, value in (
        ("basedOn", _ref(ra.based_on_type, ra.based_on_id, ra.based_on_display)),
        ("parent", _ref(ra.parent_type, ra.parent_id, ra.parent_display)),
        ("method", _cc(ra.method_system, ra.method_code, ra.method_display, ra.method_text)),
        ("code", _cc(ra.code_system, ra.code_code, ra.code_display, ra.code_text)),
        ("subject", _ref(ra.subject_type, ra.subject_id, ra.subject_display)),
        ("condition", _ref(ra.condition_type, ra.condition_id, ra.condition_display)),
        ("performer", _ref(ra.performer_type, ra.performer_id, ra.performer_display)),
    ):
        if value:
            result[key] = value

    if ra.encounter_id is not None:
        enc = {"reference": f"Encounter/{ra.encounter_id}"}
        if ra.encounter_display:
            enc["display"] = ra.encounter_display
        result["encounter"] = enc

    if ra.occurrence_datetime:
        result["occurrenceDateTime"] = ra.occurrence_datetime.isoformat()
    elif ra.occurrence_period_start or ra.occurrence_period_end:
        result["occurrencePeriod"] = _strip({
            "start": ra.occurrence_period_start.isoformat() if ra.occurrence_period_start else None,
            "end": ra.occurrence_period_end.isoformat() if ra.occurrence_period_end else None,
        })

    if ra.reason_codes:
        result["reasonCode"] = [fhir_risk_reason_code(r) for r in ra.reason_codes]
    if ra.reason_references:
        result["reasonReference"] = [fhir_risk_reference(r) for r in ra.reason_references]
    if ra.basis:
        result["basis"] = [fhir_risk_reference(b) for b in ra.basis]
    if ra.predictions:
        result["prediction"] = [fhir_risk_prediction(p) for p in ra.predictions]
    if ra.notes:
        result["note"] = [fhir_risk_note(n) for n in ra.notes]

    return {k: v for k, v in result.items() if v is not None}
