"""Plain (snake_case) builders for ActivityDefinition — field names mirror the input schema."""

from __future__ import annotations

from app.fhir.datatypes import fhir_enum, plain_identifier
from app.fhir.mappers.plan_definition.codec import unpack
from app.fhir.mappers.plan_definition.plain import (
    _cc_flat,
    _iso,
    _ref_flat,
    plain_pd_cc_row,
    plain_pd_contact,
    plain_pd_related_artifact,
    plain_pd_use_context,
)


def plain_ad_participant(p) -> dict:
    return {"id": p.id, "type": fhir_enum(p.type), **_cc_flat(p, "role")}


def plain_ad_reference_row(r) -> dict:
    """Reference list row (specimenRequirement / observationRequirement / observationResultRequirement)."""
    return {
        "id": r.id,
        "reference_type": fhir_enum(r.reference_type),
        "reference_id": r.reference_id,
        "reference_display": r.reference_display,
    }


def plain_ad_dynamic_value(d) -> dict:
    return {"id": d.id, "path": d.path, "expression": unpack("expression", "expression", d)}


def plain_ad_dose_and_rate(r) -> dict:
    return {
        "id": r.id,
        **_cc_flat(r, "type"),
        "dose_range": unpack("dose_range", "range", r),
        "dose_quantity": unpack("dose_quantity", "simple_quantity", r),
        "rate_ratio": unpack("rate_ratio", "ratio", r),
        "rate_range": unpack("rate_range", "range", r),
        "rate_quantity": unpack("rate_quantity", "simple_quantity", r),
    }


def plain_ad_dosage(d) -> dict:
    return {
        "id": d.id,
        "sequence": d.sequence,
        "text": d.text,
        "additional_instruction": [plain_pd_cc_row(a) for a in (d.additional_instructions or [])],
        "patient_instruction": d.patient_instruction,
        "timing": unpack("timing", "timing", d),
        "as_needed_boolean": d.as_needed_boolean,
        **_cc_flat(d, "as_needed"),
        **_cc_flat(d, "site"),
        **_cc_flat(d, "route"),
        **_cc_flat(d, "method"),
        "dose_and_rate": [plain_ad_dose_and_rate(r) for r in (d.dose_and_rates or [])],
        "max_dose_per_period": unpack("max_dose_per_period", "ratio", d),
        "max_dose_per_administration": unpack("max_dose_per_administration", "simple_quantity", d),
        "max_dose_per_lifetime": unpack("max_dose_per_lifetime", "simple_quantity", d),
    }


def to_plain_activity_definition(ad) -> dict:
    contacts = lambda kind: [plain_pd_contact(c) for c in (ad.contacts or []) if fhir_enum(c.kind) == kind]  # noqa: E731
    return {
        "id": ad.activity_definition_id,
        "url": ad.url,
        "version": ad.version,
        "name": ad.name,
        "title": ad.title,
        "subtitle": ad.subtitle,
        "status": fhir_enum(ad.status),
        "experimental": ad.experimental,
        "date": _iso(ad.date),
        "publisher": ad.publisher,
        "description": ad.description,
        "purpose": ad.purpose,
        "usage": ad.usage,
        "copyright": ad.copyright,
        "approval_date": _iso(ad.approval_date),
        "last_review_date": _iso(ad.last_review_date),
        "effective_period_start": _iso(ad.effective_period_start),
        "effective_period_end": _iso(ad.effective_period_end),
        **_cc_flat(ad, "subject_cc"),
        **_ref_flat(ad, "subject_reference"),
        "kind": fhir_enum(ad.kind),
        "profile": ad.profile,
        **_cc_flat(ad, "code"),
        "intent": fhir_enum(ad.intent),
        "priority": fhir_enum(ad.priority),
        "do_not_perform": ad.do_not_perform,
        "timing_datetime": _iso(ad.timing_datetime),
        "timing_age": unpack("timing_age", "quantity", ad),
        "timing_period": unpack("timing_period", "period", ad),
        "timing_range": unpack("timing_range", "range", ad),
        "timing_duration": unpack("timing_duration", "quantity", ad),
        "timing_timing": unpack("timing_timing", "timing", ad),
        **_ref_flat(ad, "location"),
        **_ref_flat(ad, "product_reference"),
        **_cc_flat(ad, "product_cc"),
        "quantity": unpack("quantity", "simple_quantity", ad),
        "transform": ad.transform,
        "identifier": [{"id": i.id, **plain_identifier(i)} for i in (ad.identifiers or [])],
        "contact": contacts("contact"),
        "author": contacts("author"),
        "editor": contacts("editor"),
        "reviewer": contacts("reviewer"),
        "endorser": contacts("endorser"),
        "use_context": [plain_pd_use_context(u) for u in (ad.use_contexts or [])],
        "jurisdiction": [plain_pd_cc_row(j) for j in (ad.jurisdictions or [])],
        "topic": [plain_pd_cc_row(t) for t in (ad.topics or [])],
        "related_artifact": [plain_pd_related_artifact(r) for r in (ad.related_artifacts or [])],
        "library": [{"id": lib.id, "canonical": lib.canonical} for lib in (ad.libraries or [])],
        "participant": [plain_ad_participant(p) for p in (ad.participants or [])],
        "dosage": [plain_ad_dosage(d) for d in (ad.dosages or [])],
        "body_site": [plain_pd_cc_row(b) for b in (ad.body_sites or [])],
        "specimen_requirement": [plain_ad_reference_row(r) for r in (ad.specimen_requirements or [])],
        "observation_requirement": [plain_ad_reference_row(r) for r in (ad.observation_requirements or [])],
        "observation_result_requirement": [plain_ad_reference_row(r) for r in (ad.observation_result_requirements or [])],
        "dynamic_value": [plain_ad_dynamic_value(d) for d in (ad.dynamic_values or [])],
        "user_id": ad.user_id,
        "org_id": ad.org_id,
        "created_at": _iso(ad.created_at),
        "updated_at": _iso(ad.updated_at),
        "created_by": ad.created_by,
        "updated_by": ad.updated_by,
    }
