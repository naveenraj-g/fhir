"""FHIR R4 (camelCase) builders for ActivityDefinition."""

from __future__ import annotations

from app.fhir.datatypes import fhir_enum, fhir_identifier
from app.fhir.mappers.plan_definition.codec import camel, unpack
from app.fhir.mappers.plan_definition.fhir import (
    _cc,
    _cc_row,
    _iso,
    _n,
    _prune,
    _ref,
    _timing,
    fhir_pd_contact,
    fhir_pd_related_artifact,
    fhir_pd_use_context,
)


def fhir_ad_participant(p) -> dict:
    return _prune({"type": fhir_enum(p.type), "role": _cc(p, "role")})


def fhir_ad_reference_row(r) -> dict:
    """Reference list row -> {reference, display}."""
    out: dict = {}
    if r.reference_type is not None and r.reference_id is not None:
        out["reference"] = f"{fhir_enum(r.reference_type)}/{r.reference_id}"
    if r.reference_display:
        out["display"] = r.reference_display
    return out


def fhir_ad_dynamic_value(d) -> dict:
    return _prune({"path": d.path, "expression": _n(d, "expression", "expression")})


def fhir_ad_dose_and_rate(r) -> dict:
    return _prune({
        "type": _cc(r, "type"),
        "doseRange": _n(r, "dose_range", "range"),
        "doseQuantity": _n(r, "dose_quantity", "simple_quantity"),
        "rateRatio": _n(r, "rate_ratio", "ratio"),
        "rateRange": _n(r, "rate_range", "range"),
        "rateQuantity": _n(r, "rate_quantity", "simple_quantity"),
    })


def fhir_ad_dosage(d) -> dict:
    return _prune({
        "sequence": d.sequence,
        "text": d.text,
        "additionalInstruction": [_cc_row(a) for a in (d.additional_instructions or [])],
        "patientInstruction": d.patient_instruction,
        "timing": _timing(d, "timing"),
        "asNeededBoolean": d.as_needed_boolean,
        "asNeededCodeableConcept": _cc(d, "as_needed"),
        "site": _cc(d, "site"),
        "route": _cc(d, "route"),
        "method": _cc(d, "method"),
        "doseAndRate": [fhir_ad_dose_and_rate(r) for r in (d.dose_and_rates or [])],
        "maxDosePerPeriod": _n(d, "max_dose_per_period", "ratio"),
        "maxDosePerAdministration": _n(d, "max_dose_per_administration", "simple_quantity"),
        "maxDosePerLifetime": _n(d, "max_dose_per_lifetime", "simple_quantity"),
    })


def to_fhir_activity_definition(ad) -> dict:
    contacts = lambda kind: [fhir_pd_contact(c) for c in (ad.contacts or []) if fhir_enum(c.kind) == kind]  # noqa: E731
    result = {
        "resourceType": "ActivityDefinition",
        "id": str(ad.activity_definition_id),
        "url": ad.url,
        "identifier": [fhir_identifier(i) for i in (ad.identifiers or [])],
        "version": ad.version,
        "name": ad.name,
        "title": ad.title,
        "subtitle": ad.subtitle,
        "status": fhir_enum(ad.status),
        "experimental": ad.experimental,
        "subjectCodeableConcept": _cc(ad, "subject_cc"),
        "subjectReference": _ref(ad, "subject_reference"),
        "date": _iso(ad.date),
        "publisher": ad.publisher,
        "contact": contacts("contact"),
        "description": ad.description,
        "useContext": [fhir_pd_use_context(u) for u in (ad.use_contexts or [])],
        "jurisdiction": [_cc_row(j) for j in (ad.jurisdictions or [])],
        "purpose": ad.purpose,
        "usage": ad.usage,
        "copyright": ad.copyright,
        "approvalDate": _iso(ad.approval_date),
        "lastReviewDate": _iso(ad.last_review_date),
        "effectivePeriod": camel(unpack("effective_period", "period", ad)),
        "topic": [_cc_row(t) for t in (ad.topics or [])],
        "author": contacts("author"),
        "editor": contacts("editor"),
        "reviewer": contacts("reviewer"),
        "endorser": contacts("endorser"),
        "relatedArtifact": [fhir_pd_related_artifact(r) for r in (ad.related_artifacts or [])],
        "library": [lib.canonical for lib in (ad.libraries or [])],
        "kind": fhir_enum(ad.kind),
        "profile": ad.profile,
        "code": _cc(ad, "code"),
        "intent": fhir_enum(ad.intent),
        "priority": fhir_enum(ad.priority),
        "doNotPerform": ad.do_not_perform,
        "timingTiming": _timing(ad, "timing_timing"),
        "timingDateTime": _iso(ad.timing_datetime),
        "timingAge": _n(ad, "timing_age", "quantity"),
        "timingPeriod": _n(ad, "timing_period", "period"),
        "timingRange": _n(ad, "timing_range", "range"),
        "timingDuration": _n(ad, "timing_duration", "quantity"),
        "location": _ref(ad, "location"),
        "participant": [fhir_ad_participant(p) for p in (ad.participants or [])],
        "productReference": _ref(ad, "product_reference"),
        "productCodeableConcept": _cc(ad, "product_cc"),
        "quantity": _n(ad, "quantity", "simple_quantity"),
        "dosage": [fhir_ad_dosage(d) for d in (ad.dosages or [])],
        "bodySite": [_cc_row(b) for b in (ad.body_sites or [])],
        "specimenRequirement": [fhir_ad_reference_row(r) for r in (ad.specimen_requirements or [])],
        "observationRequirement": [fhir_ad_reference_row(r) for r in (ad.observation_requirements or [])],
        "observationResultRequirement": [fhir_ad_reference_row(r) for r in (ad.observation_result_requirements or [])],
        "transform": ad.transform,
        "dynamicValue": [fhir_ad_dynamic_value(d) for d in (ad.dynamic_values or [])],
    }
    return _prune(result)
