"""FHIR R4 (camelCase) builders for PlanDefinition."""

from __future__ import annotations

from app.fhir.datatypes import fhir_enum, fhir_identifier, fhir_telecom
from app.fhir.mappers.plan_definition.codec import camel, unpack
from app.fhir.mappers.plan_definition.index import build_index


def _prune(d: dict) -> dict:
    """Drop None / empty containers (keeps 0 and False)."""
    return {k: v for k, v in d.items() if v is not None and v != {} and v != []}


def _iso(v):
    return v.isoformat() if v is not None else None


def _cc(row, prefix: str) -> dict | None:
    """Flat `<prefix>_system/_code/_display/_text` columns -> FHIR CodeableConcept."""
    coding = {k: v for k, v in {
        "system": getattr(row, f"{prefix}_system", None),
        "code": getattr(row, f"{prefix}_code", None),
        "display": getattr(row, f"{prefix}_display", None),
    }.items() if v}
    text = getattr(row, f"{prefix}_text", None)
    out: dict = {}
    if coding:
        out["coding"] = [coding]
    if text:
        out["text"] = text
    return out or None


def _cc_row(r) -> dict:
    """CodeableConcept list row."""
    return _cc(_Rename(r), "c") or {}


class _Rename:
    """Adapter exposing coding_* / text of a list row under the `c_*` names _cc expects."""

    def __init__(self, r):
        self.c_system, self.c_code, self.c_display, self.c_text = r.coding_system, r.coding_code, r.coding_display, r.text


def _ref(row, prefix: str) -> dict | None:
    rtype = getattr(row, f"{prefix}_type", None)
    rid = getattr(row, f"{prefix}_id", None)
    display = getattr(row, f"{prefix}_display", None)
    out: dict = {}
    if rtype is not None and rid is not None:
        out["reference"] = f"{fhir_enum(rtype)}/{rid}"
    if display:
        out["display"] = display
    return out or None


def _n(row, prefix: str, kind: str):
    """Nested datatype -> camelCase FHIR dict (or None)."""
    return camel(unpack(prefix, kind, row))


def _timing(row, prefix: str):
    t = unpack(prefix, "timing", row)
    if t is None:
        return None
    if t.get("code"):
        code = t["code"]
        coding = {k: v for k, v in {"system": code.get("system"), "code": code.get("code"), "display": code.get("display")}.items() if v}
        t["code"] = _prune({"coding": [coding] if coding else None, "text": code.get("text")})
    return camel(t)


def fhir_pd_related_artifact(r) -> dict:
    return _prune({
        "type": fhir_enum(r.type),
        "label": r.label,
        "display": r.display,
        "citation": r.citation,
        "url": r.url,
        "document": _n(r, "document", "attachment"),
        "resource": r.resource,
    })


def fhir_pd_contact(c) -> dict:
    return _prune({"name": c.name, "telecom": [fhir_telecom(t) for t in (c.telecoms or [])]})


def fhir_pd_use_context(u) -> dict:
    out: dict = {"code": _prune({"system": u.code_system, "code": u.code_code, "display": u.code_display})}
    cc = _cc(u, "value_cc")
    if cc:
        out["valueCodeableConcept"] = cc
    elif unpack("value_quantity", "simple_quantity", u):
        out["valueQuantity"] = _n(u, "value_quantity", "simple_quantity")
    elif unpack("value_range", "range", u):
        out["valueRange"] = _n(u, "value_range", "range")
    else:
        ref = _ref(u, "value_reference")
        if ref:
            out["valueReference"] = ref
    return out


def fhir_pd_data_requirement(dr) -> dict:
    out = {
        "type": dr.type,
        "profile": [p for p in (dr.profile or "").split(",") if p],
        "subjectCodeableConcept": _cc(dr, "subject_cc"),
        "subjectReference": _ref(dr, "subject_reference"),
        "mustSupport": [p for p in (dr.must_support or "").split(",") if p],
        "codeFilter": [
            _prune({
                "path": cf.path, "searchParam": cf.search_param, "valueSet": cf.value_set,
                "code": [_prune({"system": c.system, "code": c.code, "display": c.display}) for c in (cf.codes or [])],
            })
            for cf in (dr.code_filters or [])
        ],
        "dateFilter": [
            _prune({
                "path": df.path, "searchParam": df.search_param,
                "valueDateTime": _iso(df.value_datetime),
                "valuePeriod": _n(df, "value_period", "period"),
                "valueDuration": _n(df, "value_duration", "quantity"),
            })
            for df in (dr.date_filters or [])
        ],
        "limit": dr.limit,
        "sort": [{"path": s.path, "direction": fhir_enum(s.direction)} for s in (dr.sorts or [])],
    }
    return _prune(out)


def fhir_pd_trigger(t, idx) -> dict:
    return _prune({
        "type": fhir_enum(t.type),
        "name": t.name,
        "timingTiming": _timing(t, "timing_timing"),
        "timingReference": _ref(t, "timing_reference"),
        "timingDate": _iso(t.timing_date),
        "timingDateTime": _iso(t.timing_datetime),
        "data": [fhir_pd_data_requirement(d) for d in idx.drs_by_trigger.get(t.id, [])],
        "condition": _n(t, "condition", "expression"),
    })


def fhir_pd_action(a, idx) -> dict:
    drs = idx.drs_by_action.get(a.id, [])
    codes = idx.codes.get(a.id, [])
    return _prune({
        "id": a.element_id,
        "prefix": a.prefix,
        "title": a.title,
        "description": a.description,
        "textEquivalent": a.text_equivalent,
        "priority": fhir_enum(a.priority),
        "code": [_cc_row(c) for c in codes if c.kind == "code"],
        "reason": [_cc_row(c) for c in codes if c.kind == "reason"],
        "documentation": [fhir_pd_related_artifact(d) for d in idx.docs_by_action.get(a.id, [])],
        "goalId": [g.goal_element_id for g in idx.goal_ids.get(a.id, [])],
        "subjectCodeableConcept": _cc(a, "subject_cc"),
        "subjectReference": _ref(a, "subject_reference"),
        "trigger": [fhir_pd_trigger(t, idx) for t in idx.triggers.get(a.id, [])],
        "condition": [
            _prune({"kind": fhir_enum(c.kind), "expression": _n(c, "expression", "expression")})
            for c in idx.conditions.get(a.id, [])
        ],
        "input": [fhir_pd_data_requirement(d) for d in drs if fhir_enum(d.role) == "input"],
        "output": [fhir_pd_data_requirement(d) for d in drs if fhir_enum(d.role) == "output"],
        "relatedAction": [
            _prune({
                "actionId": r.related_action_id,
                "relationship": fhir_enum(r.relationship_type),
                "offsetDuration": _n(r, "offset_duration", "quantity"),
                "offsetRange": _n(r, "offset_range", "range"),
            })
            for r in idx.related.get(a.id, [])
        ],
        "timingDateTime": _iso(a.timing_datetime),
        "timingAge": _n(a, "timing_age", "quantity"),
        "timingPeriod": _n(a, "timing_period", "period"),
        "timingDuration": _n(a, "timing_duration", "quantity"),
        "timingRange": _n(a, "timing_range", "range"),
        "timingTiming": _timing(a, "timing_timing"),
        "participant": [
            _prune({"type": fhir_enum(p.type), "role": _cc(p, "role")}) for p in idx.participants.get(a.id, [])
        ],
        "type": _cc(a, "type"),
        "groupingBehavior": fhir_enum(a.grouping_behavior),
        "selectionBehavior": fhir_enum(a.selection_behavior),
        "requiredBehavior": fhir_enum(a.required_behavior),
        "precheckBehavior": fhir_enum(a.precheck_behavior),
        "cardinalityBehavior": fhir_enum(a.cardinality_behavior),
        "definitionCanonical": a.definition_canonical,
        "definitionUri": a.definition_uri,
        "transform": a.transform,
        "dynamicValue": [
            _prune({"path": d.path, "expression": _n(d, "expression", "expression")}) for d in idx.dynamic.get(a.id, [])
        ],
        "action": [fhir_pd_action(sub, idx) for sub in idx.actions_by_parent.get(a.id, [])],
    })


def fhir_pd_goal(g, idx) -> dict:
    return _prune({
        "id": g.element_id,
        "category": _cc(g, "category"),
        "description": _cc(g, "description"),
        "priority": _cc(g, "priority"),
        "start": _cc(g, "start"),
        "addresses": [_cc_row(a) for a in (g.addresses or [])],
        "documentation": [fhir_pd_related_artifact(d) for d in idx.docs_by_goal.get(g.id, [])],
        "target": [
            _prune({
                "measure": _cc(t, "measure"),
                "detailQuantity": _n(t, "detail_quantity", "quantity"),
                "detailRange": _n(t, "detail_range", "range"),
                "detailCodeableConcept": _cc(t, "detail_cc"),
                "due": _n(t, "due", "quantity"),
            })
            for t in (g.targets or [])
        ],
    })


def to_fhir_plan_definition(pd) -> dict:
    idx = build_index(pd)
    contacts = lambda kind: [fhir_pd_contact(c) for c in (pd.contacts or []) if fhir_enum(c.kind) == kind]  # noqa: E731
    result = {
        "resourceType": "PlanDefinition",
        "id": str(pd.plan_definition_id),
        "url": pd.url,
        "identifier": [fhir_identifier(i) for i in (pd.identifiers or [])],
        "version": pd.version,
        "name": pd.name,
        "title": pd.title,
        "subtitle": pd.subtitle,
        "type": _cc(pd, "type"),
        "status": fhir_enum(pd.status),
        "experimental": pd.experimental,
        "subjectCodeableConcept": _cc(pd, "subject_cc"),
        "subjectReference": _ref(pd, "subject_reference"),
        "date": _iso(pd.date),
        "publisher": pd.publisher,
        "contact": contacts("contact"),
        "description": pd.description,
        "useContext": [fhir_pd_use_context(u) for u in (pd.use_contexts or [])],
        "jurisdiction": [_cc_row(j) for j in (pd.jurisdictions or [])],
        "purpose": pd.purpose,
        "usage": pd.usage,
        "copyright": pd.copyright,
        "approvalDate": _iso(pd.approval_date),
        "lastReviewDate": _iso(pd.last_review_date),
        "effectivePeriod": camel(unpack("effective_period", "period", pd)),
        "topic": [_cc_row(t) for t in (pd.topics or [])],
        "author": contacts("author"),
        "editor": contacts("editor"),
        "reviewer": contacts("reviewer"),
        "endorser": contacts("endorser"),
        "relatedArtifact": [fhir_pd_related_artifact(r) for r in idx.plan_artifacts],
        "library": [lib.canonical for lib in (pd.libraries or [])],
        "goal": [fhir_pd_goal(g, idx) for g in (pd.goals or [])],
        "action": [fhir_pd_action(a, idx) for a in idx.actions_by_parent.get(None, [])],
    }
    return _prune(result)
