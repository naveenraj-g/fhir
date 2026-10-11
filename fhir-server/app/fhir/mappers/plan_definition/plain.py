"""Plain (snake_case) builders for PlanDefinition — field names mirror the input schema."""

from __future__ import annotations

from app.fhir.datatypes import fhir_enum, plain_identifier
from app.fhir.mappers.plan_definition.codec import unpack
from app.fhir.mappers.plan_definition.index import build_index


def _iso(v):
    return v.isoformat() if v is not None else None


def _flat(row, prefix: str, fields) -> dict:
    """Flat `<prefix>_<field>` columns copied under the same names (CodeableConcept / reference style)."""
    return {f"{prefix}_{f}": getattr(row, f"{prefix}_{f}", None) for f in fields}


_CC = ("system", "code", "display", "text")
_REF = ("type", "id", "display")


def _cc_flat(row, prefix: str) -> dict:
    return _flat(row, prefix, _CC)


def _ref_flat(row, prefix: str) -> dict:
    out = _flat(row, prefix, _REF)
    out[f"{prefix}_type"] = fhir_enum(out[f"{prefix}_type"])
    return out


def plain_pd_cc_row(r) -> dict:
    """CodeableConcept list row (jurisdiction / topic / action.code / action.reason / goal.addresses)."""
    return {"id": r.id, "coding_system": r.coding_system, "coding_code": r.coding_code,
            "coding_display": r.coding_display, "text": r.text}


def plain_pd_related_artifact(r) -> dict:
    return {
        "id": r.id,
        "type": fhir_enum(r.type),
        "label": r.label,
        "display": r.display,
        "citation": r.citation,
        "url": r.url,
        "document": unpack("document", "attachment", r),
        "resource": r.resource,
    }


def plain_pd_contact(c) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "telecom": [
            {"id": t.id, "system": t.system, "value": t.value, "use": t.use, "rank": t.rank,
             "period_start": _iso(t.period_start), "period_end": _iso(t.period_end)}
            for t in (c.telecoms or [])
        ],
    }


def plain_pd_use_context(u) -> dict:
    return {
        "id": u.id,
        "code_system": u.code_system, "code_code": u.code_code, "code_display": u.code_display,
        **_cc_flat(u, "value_cc"),
        **_flat(u, "value_quantity", ("value", "unit", "system", "code")),
        **_flat(u, "value_range_low", ("value", "unit", "system", "code")),
        **_flat(u, "value_range_high", ("value", "unit", "system", "code")),
        **_ref_flat(u, "value_reference"),
    }


def plain_pd_data_requirement(dr) -> dict:
    return {
        "id": dr.id,
        "type": dr.type,
        "profile": [p for p in (dr.profile or "").split(",") if p] or None,
        **_cc_flat(dr, "subject_cc"),
        **_ref_flat(dr, "subject_reference"),
        "must_support": [p for p in (dr.must_support or "").split(",") if p] or None,
        "code_filter": [
            {
                "id": cf.id, "path": cf.path, "search_param": cf.search_param, "value_set": cf.value_set,
                "code": [{"id": c.id, "system": c.system, "code": c.code, "display": c.display} for c in (cf.codes or [])],
            }
            for cf in (dr.code_filters or [])
        ],
        "date_filter": [
            {
                "id": df.id, "path": df.path, "search_param": df.search_param,
                "value_datetime": _iso(df.value_datetime),
                "value_period": unpack("value_period", "period", df),
                "value_duration": unpack("value_duration", "quantity", df),
            }
            for df in (dr.date_filters or [])
        ],
        "limit": dr.limit,
        "sort": [{"id": s.id, "path": s.path, "direction": fhir_enum(s.direction)} for s in (dr.sorts or [])],
    }


def plain_pd_trigger(t, idx) -> dict:
    return {
        "id": t.id,
        "type": fhir_enum(t.type),
        "name": t.name,
        "timing_timing": unpack("timing_timing", "timing", t),
        **_ref_flat(t, "timing_reference"),
        "timing_date": _iso(t.timing_date),
        "timing_datetime": _iso(t.timing_datetime),
        "data": [plain_pd_data_requirement(d) for d in idx.drs_by_trigger.get(t.id, [])],
        "condition": unpack("condition", "expression", t),
    }


def plain_pd_action(a, idx) -> dict:
    drs = idx.drs_by_action.get(a.id, [])
    codes = idx.codes.get(a.id, [])
    return {
        "id": a.id,
        "element_id": a.element_id,
        "prefix": a.prefix,
        "title": a.title,
        "description": a.description,
        "text_equivalent": a.text_equivalent,
        "priority": fhir_enum(a.priority),
        "code": [plain_pd_cc_row(c) for c in codes if c.kind == "code"],
        "reason": [plain_pd_cc_row(c) for c in codes if c.kind == "reason"],
        "documentation": [plain_pd_related_artifact(d) for d in idx.docs_by_action.get(a.id, [])],
        "goal_id": [g.goal_element_id for g in idx.goal_ids.get(a.id, [])],
        **_cc_flat(a, "subject_cc"),
        **_ref_flat(a, "subject_reference"),
        "trigger": [plain_pd_trigger(t, idx) for t in idx.triggers.get(a.id, [])],
        "condition": [
            {"id": c.id, "kind": fhir_enum(c.kind), "expression": unpack("expression", "expression", c)}
            for c in idx.conditions.get(a.id, [])
        ],
        "input": [plain_pd_data_requirement(d) for d in drs if fhir_enum(d.role) == "input"],
        "output": [plain_pd_data_requirement(d) for d in drs if fhir_enum(d.role) == "output"],
        "related_action": [
            {
                "id": r.id, "action_id": r.related_action_id, "relationship": fhir_enum(r.relationship_type),
                "offset_duration": unpack("offset_duration", "quantity", r),
                "offset_range": unpack("offset_range", "range", r),
            }
            for r in idx.related.get(a.id, [])
        ],
        "timing_datetime": _iso(a.timing_datetime),
        "timing_age": unpack("timing_age", "quantity", a),
        "timing_period": unpack("timing_period", "period", a),
        "timing_duration": unpack("timing_duration", "quantity", a),
        "timing_range": unpack("timing_range", "range", a),
        "timing_timing": unpack("timing_timing", "timing", a),
        "participant": [
            {"id": p.id, "type": fhir_enum(p.type), **_cc_flat(p, "role")} for p in idx.participants.get(a.id, [])
        ],
        **_cc_flat(a, "type"),
        "grouping_behavior": fhir_enum(a.grouping_behavior),
        "selection_behavior": fhir_enum(a.selection_behavior),
        "required_behavior": fhir_enum(a.required_behavior),
        "precheck_behavior": fhir_enum(a.precheck_behavior),
        "cardinality_behavior": fhir_enum(a.cardinality_behavior),
        "definition_canonical": a.definition_canonical,
        "definition_uri": a.definition_uri,
        "transform": a.transform,
        "dynamic_value": [
            {"id": d.id, "path": d.path, "expression": unpack("expression", "expression", d)}
            for d in idx.dynamic.get(a.id, [])
        ],
        "action": [plain_pd_action(sub, idx) for sub in idx.actions_by_parent.get(a.id, [])],
    }


def plain_pd_goal(g, idx) -> dict:
    return {
        "id": g.id,
        "element_id": g.element_id,
        **_cc_flat(g, "category"),
        **_cc_flat(g, "description"),
        **_cc_flat(g, "priority"),
        **_cc_flat(g, "start"),
        "addresses": [plain_pd_cc_row(a) for a in (g.addresses or [])],
        "documentation": [plain_pd_related_artifact(d) for d in idx.docs_by_goal.get(g.id, [])],
        "target": [
            {
                "id": t.id,
                **_cc_flat(t, "measure"),
                "detail_quantity": unpack("detail_quantity", "quantity", t),
                "detail_range": unpack("detail_range", "range", t),
                **_cc_flat(t, "detail_cc"),
                "due": unpack("due", "quantity", t),
            }
            for t in (g.targets or [])
        ],
    }


def to_plain_plan_definition(pd) -> dict:
    idx = build_index(pd)
    contacts = lambda kind: [plain_pd_contact(c) for c in (pd.contacts or []) if fhir_enum(c.kind) == kind]  # noqa: E731
    return {
        "id": pd.plan_definition_id,
        "url": pd.url,
        "version": pd.version,
        "name": pd.name,
        "title": pd.title,
        "subtitle": pd.subtitle,
        "status": fhir_enum(pd.status),
        "experimental": pd.experimental,
        "date": _iso(pd.date),
        "publisher": pd.publisher,
        "description": pd.description,
        "purpose": pd.purpose,
        "usage": pd.usage,
        "copyright": pd.copyright,
        "approval_date": _iso(pd.approval_date),
        "last_review_date": _iso(pd.last_review_date),
        "effective_period_start": _iso(pd.effective_period_start),
        "effective_period_end": _iso(pd.effective_period_end),
        **_cc_flat(pd, "type"),
        **_cc_flat(pd, "subject_cc"),
        **_ref_flat(pd, "subject_reference"),
        "identifier": [{"id": i.id, **plain_identifier(i)} for i in (pd.identifiers or [])],
        "contact": contacts("contact"),
        "author": contacts("author"),
        "editor": contacts("editor"),
        "reviewer": contacts("reviewer"),
        "endorser": contacts("endorser"),
        "use_context": [plain_pd_use_context(u) for u in (pd.use_contexts or [])],
        "jurisdiction": [plain_pd_cc_row(j) for j in (pd.jurisdictions or [])],
        "topic": [plain_pd_cc_row(t) for t in (pd.topics or [])],
        "related_artifact": [plain_pd_related_artifact(r) for r in idx.plan_artifacts],
        "library": [{"id": lib.id, "canonical": lib.canonical} for lib in (pd.libraries or [])],
        "goal": [plain_pd_goal(g, idx) for g in (pd.goals or [])],
        "action": [plain_pd_action(a, idx) for a in idx.actions_by_parent.get(None, [])],
        "user_id": pd.user_id,
        "org_id": pd.org_id,
        "created_at": _iso(pd.created_at),
        "updated_at": _iso(pd.updated_at),
        "created_by": pd.created_by,
        "updated_by": pd.updated_by,
    }
