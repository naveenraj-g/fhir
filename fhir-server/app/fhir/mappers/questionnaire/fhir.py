"""FHIR R4 (camelCase) builders for Questionnaire."""

from __future__ import annotations

from collections import defaultdict

from app.fhir.datatypes import fhir_enum, fhir_identifier, fhir_split, fhir_telecom


def _g(obj, col: str, name: str):
    """Read `<col>_<name>` from an ORM row, None when the column does not exist."""
    return getattr(obj, f"{col}_{name}", None)


def _strip(d: dict) -> dict:
    """Drop None values (keeps False / 0)."""
    return {k: v for k, v in d.items() if v is not None}


def _fhir_cc(system, code, display, text) -> dict | None:
    coding = {k: v for k, v in {"system": system, "code": code, "display": display}.items() if v}
    entry: dict = {}
    if coding:
        entry["coding"] = [coding]
    if text:
        entry["text"] = text
    return entry or None


def _fhir_ref(ref_type, ref_id, display) -> dict | None:
    entry: dict = {}
    if ref_type is not None and ref_id is not None:
        entry["reference"] = f"{fhir_enum(ref_type)}/{ref_id}"
    if display:
        entry["display"] = display
    return entry or None


def _fhir_value(o, col: str, key: str) -> dict:
    """
    Emit the single populated choice-type element for `<key>[x]`.

    `col` is the column prefix on the ORM row ("answer" or "value"); `key` is the
    FHIR element prefix ("answer" or "value"). Only one variant is ever populated.
    """
    out: dict = {}
    if _g(o, col, "boolean") is not None:
        out[f"{key}Boolean"] = _g(o, col, "boolean")
    elif _g(o, col, "decimal") is not None:
        out[f"{key}Decimal"] = _g(o, col, "decimal")
    elif _g(o, col, "integer") is not None:
        out[f"{key}Integer"] = _g(o, col, "integer")
    elif _g(o, col, "date") is not None:
        out[f"{key}Date"] = _g(o, col, "date").isoformat()
    elif _g(o, col, "datetime") is not None:
        out[f"{key}DateTime"] = _g(o, col, "datetime").isoformat()
    elif _g(o, col, "time") is not None:
        out[f"{key}Time"] = _g(o, col, "time")
    elif _g(o, col, "string") is not None:
        out[f"{key}String"] = _g(o, col, "string")
    elif _g(o, col, "uri") is not None:
        out[f"{key}Uri"] = _g(o, col, "uri")
    elif any(_g(o, col, f"attachment_{n}") is not None for n in (
            "content_type", "language", "data", "url", "size", "hash", "title", "creation")):
        creation = _g(o, col, "attachment_creation")
        out[f"{key}Attachment"] = _strip({
            "contentType": _g(o, col, "attachment_content_type"),
            "language": _g(o, col, "attachment_language"),
            "data": _g(o, col, "attachment_data"),
            "url": _g(o, col, "attachment_url"),
            "size": _g(o, col, "attachment_size"),
            "hash": _g(o, col, "attachment_hash"),
            "title": _g(o, col, "attachment_title"),
            "creation": creation.isoformat() if creation else None,
        })
    elif any(_g(o, col, f"coding_{n}") for n in ("system", "code", "display")):
        out[f"{key}Coding"] = _strip({
            "system": _g(o, col, "coding_system"),
            "code": _g(o, col, "coding_code"),
            "display": _g(o, col, "coding_display"),
        })
    elif any(_g(o, col, f"quantity_{n}") is not None for n in ("value", "unit", "system", "code")):
        out[f"{key}Quantity"] = _strip({
            "value": _g(o, col, "quantity_value"),
            "unit": _g(o, col, "quantity_unit"),
            "system": _g(o, col, "quantity_system"),
            "code": _g(o, col, "quantity_code"),
        })
    elif _g(o, col, "reference_id") is not None or _g(o, col, "reference_display"):
        ref = _fhir_ref(_g(o, col, "reference_type"), _g(o, col, "reference_id"), _g(o, col, "reference_display"))
        if ref:
            out[f"{key}Reference"] = ref
    return out


def fhir_questionnaire_identifier(i) -> dict:
    return fhir_identifier(i)


def fhir_questionnaire_contact(c) -> dict:
    entry: dict = {}
    if c.name:
        entry["name"] = c.name
    telecoms = [fhir_telecom(t) for t in (c.telecoms or [])]
    if telecoms:
        entry["telecom"] = telecoms
    return entry


def fhir_questionnaire_use_context(u) -> dict:
    entry: dict = {"code": _strip({
        "system": u.code_system, "code": u.code_code, "display": u.code_display,
    })}
    cc = _fhir_cc(u.value_cc_system, u.value_cc_code, u.value_cc_display, u.value_cc_text)
    if cc:
        entry["valueCodeableConcept"] = cc
    elif any(v is not None for v in (u.value_quantity_value, u.value_quantity_unit,
                                     u.value_quantity_system, u.value_quantity_code)):
        entry["valueQuantity"] = _strip({
            "value": u.value_quantity_value, "unit": u.value_quantity_unit,
            "system": u.value_quantity_system, "code": u.value_quantity_code,
        })
    elif any(v is not None for v in (u.value_range_low_value, u.value_range_low_unit,
                                     u.value_range_high_value, u.value_range_high_unit)):
        rng: dict = {}
        low = _strip({"value": u.value_range_low_value, "unit": u.value_range_low_unit})
        high = _strip({"value": u.value_range_high_value, "unit": u.value_range_high_unit})
        if low:
            rng["low"] = low
        if high:
            rng["high"] = high
        entry["valueRange"] = rng
    else:
        ref = _fhir_ref(u.value_reference_type, u.value_reference_id, u.value_reference_display)
        if ref:
            entry["valueReference"] = ref
    return entry


def fhir_questionnaire_jurisdiction(j) -> dict:
    return _fhir_cc(j.coding_system, j.coding_code, j.coding_display, j.text) or {}


def fhir_questionnaire_coding(c) -> dict:
    """Coding row (questionnaire.code[] and item.code[])."""
    return _strip({"system": c.system, "code": c.code, "display": c.display})


def fhir_questionnaire_enable_when(e) -> dict:
    return {"question": e.question, "operator": fhir_enum(e.operator), **_fhir_value(e, "answer", "answer")}


def fhir_questionnaire_answer_option(a) -> dict:
    entry = _fhir_value(a, "value", "value")
    if a.initial_selected is not None:
        entry["initialSelected"] = a.initial_selected
    return entry


def fhir_questionnaire_initial(i) -> dict:
    return _fhir_value(i, "value", "value")


def fhir_questionnaire_item(item, children: dict) -> dict:
    """Build one item and (recursively) its nested items from the parent->children index."""
    entry: dict = {"linkId": item.link_id}
    if item.definition:
        entry["definition"] = item.definition
    if item.codes:
        entry["code"] = [fhir_questionnaire_coding(c) for c in item.codes]
    if item.prefix:
        entry["prefix"] = item.prefix
    if item.text:
        entry["text"] = item.text
    entry["type"] = fhir_enum(item.type)
    if item.enable_whens:
        entry["enableWhen"] = [fhir_questionnaire_enable_when(e) for e in item.enable_whens]
    if item.enable_behavior:
        entry["enableBehavior"] = fhir_enum(item.enable_behavior)
    for key, val in (("required", item.required), ("repeats", item.repeats),
                     ("readOnly", item.read_only), ("maxLength", item.max_length)):
        if val is not None:
            entry[key] = val
    if item.answer_value_set:
        entry["answerValueSet"] = item.answer_value_set
    if item.answer_options:
        entry["answerOption"] = [fhir_questionnaire_answer_option(a) for a in item.answer_options]
    if item.initials:
        entry["initial"] = [fhir_questionnaire_initial(i) for i in item.initials]
    subs = children.get(item.id)
    if subs:
        entry["item"] = [fhir_questionnaire_item(s, children) for s in subs]
    return entry


def build_item_index(items) -> dict:
    """Index flat item rows by parent id (None = top level), sorted by creation position."""
    children: dict = defaultdict(list)
    for it in sorted(items or [], key=lambda x: (x.position or 0, x.id)):
        children[it.parent_item_id].append(it)
    return children


def to_fhir_questionnaire(q) -> dict:
    result: dict = {
        "resourceType": "Questionnaire",
        "id": str(q.questionnaire_id),
        "url": q.url,
        "version": q.version,
        "name": q.name,
        "title": q.title,
        "status": fhir_enum(q.status),
        "experimental": q.experimental,
        "date": q.date.isoformat() if q.date else None,
        "publisher": q.publisher,
        "description": q.description,
        "purpose": q.purpose,
        "copyright": q.copyright,
        "approvalDate": q.approval_date.isoformat() if q.approval_date else None,
        "lastReviewDate": q.last_review_date.isoformat() if q.last_review_date else None,
    }
    if q.identifiers:
        result["identifier"] = [fhir_questionnaire_identifier(i) for i in q.identifiers]
    derived = fhir_split(q.derived_from)
    if derived:
        result["derivedFrom"] = derived
    if q.subject_types:
        result["subjectType"] = [s.code for s in q.subject_types]
    if q.contacts:
        result["contact"] = [fhir_questionnaire_contact(c) for c in q.contacts]
    if q.use_contexts:
        result["useContext"] = [fhir_questionnaire_use_context(u) for u in q.use_contexts]
    if q.jurisdictions:
        result["jurisdiction"] = [fhir_questionnaire_jurisdiction(j) for j in q.jurisdictions]
    if q.effective_period_start or q.effective_period_end:
        result["effectivePeriod"] = _strip({
            "start": q.effective_period_start.isoformat() if q.effective_period_start else None,
            "end": q.effective_period_end.isoformat() if q.effective_period_end else None,
        })
    if q.codes:
        result["code"] = [fhir_questionnaire_coding(c) for c in q.codes]
    children = build_item_index(q.items)
    top = children.get(None)
    if top:
        result["item"] = [fhir_questionnaire_item(i, children) for i in top]
    return {k: v for k, v in result.items() if v is not None}
