"""FHIR R4 (camelCase) builders for QuestionnaireResponse."""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum, fhir_identifier

if TYPE_CHECKING:
    from app.models.questionnaire_response.questionnaire_response import (
        QuestionnaireResponseAnswerModel,
        QuestionnaireResponseItemModel,
        QuestionnaireResponseModel,
    )


def _strip(d: dict) -> dict:
    """Drop None values (keeps False / 0)."""
    return {k: v for k, v in d.items() if v is not None}


def _ref(ref_type, ref_id, display) -> dict | None:
    entry: dict = {}
    if ref_type is not None and ref_id is not None:
        entry["reference"] = f"{fhir_enum(ref_type)}/{ref_id}"
    if display:
        entry["display"] = display
    return entry or None


def build_item_index(items) -> tuple[dict, dict]:
    """
    Re-nest the flat item rows.

    Returns (by_parent_item, by_parent_answer): each maps a parent id to its
    children sorted by creation position. Top-level items are
    by_parent_item[None]. Items nested under an answer have parent_answer_id set
    (and no parent_item_id), so they must NOT be treated as top-level.
    """
    by_item: dict = defaultdict(list)
    by_answer: dict = defaultdict(list)
    for it in sorted(items or [], key=lambda x: (x.position or 0, x.id)):
        if it.parent_answer_id is not None:
            by_answer[it.parent_answer_id].append(it)
        else:
            by_item[it.parent_item_id].append(it)
    return by_item, by_answer


def fhir_qr_answer(answer: "QuestionnaireResponseAnswerModel", by_item: dict, by_answer: dict) -> dict:
    vt = answer.value_type
    data: dict = {}

    if vt == "boolean":
        data["valueBoolean"] = answer.value_boolean
    elif vt == "decimal":
        data["valueDecimal"] = answer.value_decimal
    elif vt == "integer":
        data["valueInteger"] = answer.value_integer
    elif vt == "date":
        data["valueDate"] = answer.value_date.isoformat() if answer.value_date else None
    elif vt == "dateTime":
        data["valueDateTime"] = answer.value_datetime.isoformat() if answer.value_datetime else None
    elif vt == "time":
        data["valueTime"] = answer.value_time
    elif vt == "string":
        data["valueString"] = answer.value_string
    elif vt == "uri":
        data["valueUri"] = answer.value_uri
    elif vt == "coding":
        coding = _strip({
            "system": answer.value_coding_system,
            "code": answer.value_coding_code,
            "display": answer.value_coding_display,
        })
        if coding:
            data["valueCoding"] = coding
    elif vt == "quantity":
        qty = _strip({
            "value": answer.value_quantity_value,
            "unit": answer.value_quantity_unit,
            "system": answer.value_quantity_system,
            "code": answer.value_quantity_code,
        })
        if qty:
            data["valueQuantity"] = qty
    elif vt == "reference":
        ref = _strip({"reference": answer.value_reference, "display": answer.value_reference_display})
        if ref:
            data["valueReference"] = ref
    elif vt == "attachment":
        att = _strip({
            "contentType": answer.value_attachment_content_type,
            "language": answer.value_attachment_language,
            "data": answer.value_attachment_data,
            "url": answer.value_attachment_url,
            "size": answer.value_attachment_size,
            "hash": answer.value_attachment_hash,
            "title": answer.value_attachment_title,
            "creation": answer.value_attachment_creation.isoformat() if answer.value_attachment_creation else None,
        })
        if att:
            data["valueAttachment"] = att

    subs = by_answer.get(answer.id)
    if subs:
        data["item"] = [fhir_qr_item(sub, by_item, by_answer) for sub in subs]
    return {k: v for k, v in data.items() if v is not None}


def fhir_qr_item(item: "QuestionnaireResponseItemModel", by_item: dict, by_answer: dict) -> dict:
    data: dict = {"linkId": item.link_id}
    if item.text:
        data["text"] = item.text
    if item.definition:
        data["definition"] = item.definition
    if item.answers:
        data["answer"] = [fhir_qr_answer(a, by_item, by_answer) for a in item.answers]
    subs = by_item.get(item.id)
    if subs:
        data["item"] = [fhir_qr_item(sub, by_item, by_answer) for sub in subs]
    return data


def fhir_qr_reference(r) -> dict:
    """basedOn / partOf child row -> Reference."""
    return _ref(r.reference_type, r.reference_id, r.reference_display) or {}


def to_fhir_questionnaire_response(qr: "QuestionnaireResponseModel") -> dict:
    result: dict = {
        "resourceType": "QuestionnaireResponse",
        "id": str(qr.questionnaire_response_id),
        "questionnaire": qr.questionnaire,
        "status": fhir_enum(qr.status),
        "authored": qr.authored.isoformat() if qr.authored else None,
    }

    # identifier is 0..1 in R4 and stored flat; reuse the shared Identifier builder.
    if qr.identifier_value or qr.identifier_system:
        class _Ident:  # adapter exposing the flat columns under the shared helper's attribute names
            use = qr.identifier_use
            type_system = qr.identifier_type_system
            type_code = qr.identifier_type_code
            type_display = qr.identifier_type_display
            type_text = qr.identifier_type_text
            system = qr.identifier_system
            value = qr.identifier_value
            period_start = qr.identifier_period_start
            period_end = qr.identifier_period_end
            assigner = qr.identifier_assigner

        result["identifier"] = fhir_identifier(_Ident)

    if qr.based_ons:
        result["basedOn"] = [fhir_qr_reference(b) for b in qr.based_ons]
    if qr.part_ofs:
        result["partOf"] = [fhir_qr_reference(p) for p in qr.part_ofs]

    subject = _ref(qr.subject_type, qr.subject_id, qr.subject_display)
    if subject:
        result["subject"] = subject
    if qr.encounter_id is not None:
        enc = {"reference": f"Encounter/{qr.encounter_id}"}
        if qr.encounter_display:
            enc["display"] = qr.encounter_display
        result["encounter"] = enc
    author = _ref(qr.author_type, qr.author_id, qr.author_display)
    if author:
        result["author"] = author
    source = _ref(qr.source_type, qr.source_id, qr.source_display)
    if source:
        result["source"] = source

    by_item, by_answer = build_item_index(qr.items)
    top = by_item.get(None)
    if top:
        result["item"] = [fhir_qr_item(i, by_item, by_answer) for i in top]

    return {k: v for k, v in result.items() if v is not None}
