"""Plain (snake_case) builders for Questionnaire — mirror the input schema field names."""

from __future__ import annotations

from app.fhir.datatypes import fhir_enum, fhir_split, plain_identifier, plain_telecom
from app.fhir.mappers.questionnaire.fhir import build_item_index


def _iso(v):
    return v.isoformat() if v is not None else None


def plain_questionnaire_identifier(i) -> dict:
    return {"id": i.id, **plain_identifier(i)}


def plain_questionnaire_contact(c) -> dict:
    return {"id": c.id, "name": c.name, "telecom": [plain_telecom(t) for t in (c.telecoms or [])]}


def plain_questionnaire_use_context(u) -> dict:
    return {
        "id": u.id,
        "code_system": u.code_system,
        "code_code": u.code_code,
        "code_display": u.code_display,
        "value_cc_system": u.value_cc_system,
        "value_cc_code": u.value_cc_code,
        "value_cc_display": u.value_cc_display,
        "value_cc_text": u.value_cc_text,
        "value_quantity_value": u.value_quantity_value,
        "value_quantity_unit": u.value_quantity_unit,
        "value_quantity_system": u.value_quantity_system,
        "value_quantity_code": u.value_quantity_code,
        "value_range_low_value": u.value_range_low_value,
        "value_range_low_unit": u.value_range_low_unit,
        "value_range_high_value": u.value_range_high_value,
        "value_range_high_unit": u.value_range_high_unit,
        "value_reference_type": fhir_enum(u.value_reference_type),
        "value_reference_id": u.value_reference_id,
        "value_reference_display": u.value_reference_display,
    }


def plain_questionnaire_jurisdiction(j) -> dict:
    return {
        "id": j.id,
        "coding_system": j.coding_system,
        "coding_code": j.coding_code,
        "coding_display": j.coding_display,
        "text": j.text,
    }


def plain_questionnaire_subject_type(s) -> dict:
    return {"id": s.id, "code": s.code}


def plain_questionnaire_coding(c) -> dict:
    """Coding row (questionnaire.code[] and item.code[])."""
    return {"id": c.id, "system": c.system, "code": c.code, "display": c.display}


def plain_questionnaire_enable_when(e) -> dict:
    return {
        "id": e.id,
        "question": e.question,
        "operator": fhir_enum(e.operator),
        "answer_boolean": e.answer_boolean,
        "answer_decimal": e.answer_decimal,
        "answer_integer": e.answer_integer,
        "answer_date": _iso(e.answer_date),
        "answer_datetime": _iso(e.answer_datetime),
        "answer_time": e.answer_time,
        "answer_string": e.answer_string,
        "answer_coding_system": e.answer_coding_system,
        "answer_coding_code": e.answer_coding_code,
        "answer_coding_display": e.answer_coding_display,
        "answer_quantity_value": e.answer_quantity_value,
        "answer_quantity_unit": e.answer_quantity_unit,
        "answer_quantity_system": e.answer_quantity_system,
        "answer_quantity_code": e.answer_quantity_code,
        "answer_reference_type": e.answer_reference_type,
        "answer_reference_id": e.answer_reference_id,
        "answer_reference_display": e.answer_reference_display,
    }


def plain_questionnaire_answer_option(a) -> dict:
    return {
        "id": a.id,
        "initial_selected": a.initial_selected,
        "value_integer": a.value_integer,
        "value_date": _iso(a.value_date),
        "value_time": a.value_time,
        "value_string": a.value_string,
        "value_coding_system": a.value_coding_system,
        "value_coding_code": a.value_coding_code,
        "value_coding_display": a.value_coding_display,
        "value_reference_type": a.value_reference_type,
        "value_reference_id": a.value_reference_id,
        "value_reference_display": a.value_reference_display,
    }


def plain_questionnaire_initial(i) -> dict:
    return {
        "id": i.id,
        "value_boolean": i.value_boolean,
        "value_decimal": i.value_decimal,
        "value_integer": i.value_integer,
        "value_date": _iso(i.value_date),
        "value_datetime": _iso(i.value_datetime),
        "value_time": i.value_time,
        "value_string": i.value_string,
        "value_uri": i.value_uri,
        "value_attachment_content_type": i.value_attachment_content_type,
        "value_attachment_language": i.value_attachment_language,
        "value_attachment_data": i.value_attachment_data,
        "value_attachment_url": i.value_attachment_url,
        "value_attachment_size": i.value_attachment_size,
        "value_attachment_hash": i.value_attachment_hash,
        "value_attachment_title": i.value_attachment_title,
        "value_attachment_creation": _iso(i.value_attachment_creation),
        "value_coding_system": i.value_coding_system,
        "value_coding_code": i.value_coding_code,
        "value_coding_display": i.value_coding_display,
        "value_quantity_value": i.value_quantity_value,
        "value_quantity_unit": i.value_quantity_unit,
        "value_quantity_system": i.value_quantity_system,
        "value_quantity_code": i.value_quantity_code,
        "value_reference_type": i.value_reference_type,
        "value_reference_id": i.value_reference_id,
        "value_reference_display": i.value_reference_display,
    }


def plain_questionnaire_item(item, children: dict) -> dict:
    """Build one item and (recursively) its nested items from the parent->children index."""
    return {
        "id": item.id,
        "link_id": item.link_id,
        "definition": item.definition,
        "code": [plain_questionnaire_coding(c) for c in (item.codes or [])],
        "prefix": item.prefix,
        "text": item.text,
        "type": fhir_enum(item.type),
        "enable_when": [plain_questionnaire_enable_when(e) for e in (item.enable_whens or [])],
        "enable_behavior": fhir_enum(item.enable_behavior),
        "required": item.required,
        "repeats": item.repeats,
        "read_only": item.read_only,
        "max_length": item.max_length,
        "answer_value_set": item.answer_value_set,
        "answer_option": [plain_questionnaire_answer_option(a) for a in (item.answer_options or [])],
        "initial": [plain_questionnaire_initial(i) for i in (item.initials or [])],
        "item": [plain_questionnaire_item(s, children) for s in children.get(item.id, [])],
    }


def to_plain_questionnaire(q) -> dict:
    children = build_item_index(q.items)
    return {
        "id": q.questionnaire_id,
        "url": q.url,
        "version": q.version,
        "name": q.name,
        "title": q.title,
        "status": fhir_enum(q.status),
        "experimental": q.experimental,
        "date": _iso(q.date),
        "publisher": q.publisher,
        "description": q.description,
        "purpose": q.purpose,
        "copyright": q.copyright,
        "approval_date": _iso(q.approval_date),
        "last_review_date": _iso(q.last_review_date),
        "effective_period_start": _iso(q.effective_period_start),
        "effective_period_end": _iso(q.effective_period_end),
        "derived_from": fhir_split(q.derived_from),
        "identifier": [plain_questionnaire_identifier(i) for i in (q.identifiers or [])],
        "subject_type": [plain_questionnaire_subject_type(s) for s in (q.subject_types or [])],
        "contact": [plain_questionnaire_contact(c) for c in (q.contacts or [])],
        "use_context": [plain_questionnaire_use_context(u) for u in (q.use_contexts or [])],
        "jurisdiction": [plain_questionnaire_jurisdiction(j) for j in (q.jurisdictions or [])],
        "code": [plain_questionnaire_coding(c) for c in (q.codes or [])],
        "item": [plain_questionnaire_item(i, children) for i in children.get(None, [])],
        "user_id": q.user_id,
        "org_id": q.org_id,
        "created_at": _iso(q.created_at),
        "updated_at": _iso(q.updated_at),
        "created_by": q.created_by,
        "updated_by": q.updated_by,
    }
