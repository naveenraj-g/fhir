"""Plain (snake_case) builders for QuestionnaireResponse — field names mirror the input schema."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum
from app.fhir.mappers.questionnaire_response.fhir import build_item_index

if TYPE_CHECKING:
    from app.models.questionnaire_response.questionnaire_response import (
        QuestionnaireResponseAnswerModel,
        QuestionnaireResponseItemModel,
        QuestionnaireResponseModel,
    )


def _strip(d: dict) -> dict:
    return {k: v for k, v in d.items() if v is not None}


def plain_qr_answer(answer: "QuestionnaireResponseAnswerModel", by_item: dict, by_answer: dict) -> dict:
    vt = answer.value_type
    data: dict = {"value_type": vt}

    if vt == "boolean":
        data["value_boolean"] = answer.value_boolean
    elif vt == "decimal":
        data["value_decimal"] = answer.value_decimal
    elif vt == "integer":
        data["value_integer"] = answer.value_integer
    elif vt == "date":
        data["value_date"] = answer.value_date.isoformat() if answer.value_date else None
    elif vt == "dateTime":
        data["value_datetime"] = answer.value_datetime.isoformat() if answer.value_datetime else None
    elif vt == "time":
        data["value_time"] = answer.value_time
    elif vt == "string":
        data["value_string"] = answer.value_string
    elif vt == "uri":
        data["value_uri"] = answer.value_uri
    elif vt == "coding":
        data["value_coding"] = _strip({
            "system": answer.value_coding_system,
            "code": answer.value_coding_code,
            "display": answer.value_coding_display,
        })
    elif vt == "quantity":
        data["value_quantity"] = _strip({
            "value": answer.value_quantity_value,
            "unit": answer.value_quantity_unit,
            "system": answer.value_quantity_system,
            "code": answer.value_quantity_code,
        })
    elif vt == "reference":
        data["value_reference"] = answer.value_reference
        data["value_reference_display"] = answer.value_reference_display
    elif vt == "attachment":
        data["value_attachment"] = _strip({
            "content_type": answer.value_attachment_content_type,
            "language": answer.value_attachment_language,
            "data": answer.value_attachment_data,
            "url": answer.value_attachment_url,
            "size": answer.value_attachment_size,
            "hash": answer.value_attachment_hash,
            "title": answer.value_attachment_title,
            "creation": answer.value_attachment_creation.isoformat() if answer.value_attachment_creation else None,
        }) or None

    subs = by_answer.get(answer.id)
    if subs:
        data["item"] = [plain_qr_item(sub, by_item, by_answer) for sub in subs]

    return {k: v for k, v in data.items() if k == "value_type" or v is not None}


def plain_qr_item(item: "QuestionnaireResponseItemModel", by_item: dict, by_answer: dict) -> dict:
    data: dict = {"link_id": item.link_id}
    if item.text:
        data["text"] = item.text
    if item.definition:
        data["definition"] = item.definition
    if item.answers:
        data["answer"] = [plain_qr_answer(a, by_item, by_answer) for a in item.answers]
    subs = by_item.get(item.id)
    if subs:
        data["item"] = [plain_qr_item(sub, by_item, by_answer) for sub in subs]
    return data


def plain_qr_reference(r) -> dict:
    """basedOn / partOf child row."""
    return {
        "reference_type": fhir_enum(r.reference_type),
        "reference_id": r.reference_id,
        "reference_display": r.reference_display,
    }


def to_plain_questionnaire_response(qr: "QuestionnaireResponseModel") -> dict:
    result: dict = {
        "id": qr.questionnaire_response_id,
        "user_id": qr.user_id,
        "org_id": qr.org_id,
        "questionnaire": qr.questionnaire,
        "status": fhir_enum(qr.status),
        "identifier_use": fhir_enum(qr.identifier_use),
        "identifier_type_system": qr.identifier_type_system,
        "identifier_type_code": qr.identifier_type_code,
        "identifier_type_display": qr.identifier_type_display,
        "identifier_type_text": qr.identifier_type_text,
        "identifier_system": qr.identifier_system,
        "identifier_value": qr.identifier_value,
        "identifier_period_start": qr.identifier_period_start.isoformat() if qr.identifier_period_start else None,
        "identifier_period_end": qr.identifier_period_end.isoformat() if qr.identifier_period_end else None,
        "identifier_assigner": qr.identifier_assigner,
        "based_on": [plain_qr_reference(b) for b in qr.based_ons] if qr.based_ons else None,
        "part_of": [plain_qr_reference(p) for p in qr.part_ofs] if qr.part_ofs else None,
        "subject_type": fhir_enum(qr.subject_type),
        "subject_id": qr.subject_id,
        "subject_display": qr.subject_display,
        "encounter_type": fhir_enum(qr.encounter_type),
        "encounter_id": qr.encounter_id,
        "encounter_display": qr.encounter_display,
        "authored": qr.authored.isoformat() if qr.authored else None,
        "author_type": fhir_enum(qr.author_type),
        "author_id": qr.author_id,
        "author_display": qr.author_display,
        "source_type": fhir_enum(qr.source_type),
        "source_id": qr.source_id,
        "source_display": qr.source_display,
        "created_at": qr.created_at.isoformat() if qr.created_at else None,
        "updated_at": qr.updated_at.isoformat() if qr.updated_at else None,
        "created_by": qr.created_by,
        "updated_by": qr.updated_by,
    }

    by_item, by_answer = build_item_index(qr.items)
    top = by_item.get(None)
    if top:
        result["item"] = [plain_qr_item(i, by_item, by_answer) for i in top]

    return {k: v for k, v in result.items() if v is not None}
