from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.questionnaire_response.questionnaire_response import (
        QuestionnaireResponseModel,
        QuestionnaireResponseItemModel,
        QuestionnaireResponseAnswerModel,
    )


# ── Answer mapper ──────────────────────────────────────────────────────────


def _map_answer_to_fhir(answer: "QuestionnaireResponseAnswerModel") -> dict:
    vt = answer.value_type
    data: dict = {}

    if vt == "boolean":
        data["valueBoolean"] = answer.value_boolean
    elif vt == "decimal":
        data["valueDecimal"] = answer.value_decimal
    elif vt == "integer":
        data["valueInteger"] = answer.value_integer
    elif vt == "date":
        data["valueDate"] = answer.value_string
    elif vt == "dateTime":
        data["valueDateTime"] = answer.value_datetime.isoformat() if answer.value_datetime else None
    elif vt == "time":
        data["valueTime"] = answer.value_string
    elif vt == "string":
        data["valueString"] = answer.value_string
    elif vt == "uri":
        data["valueUri"] = answer.value_string
    elif vt == "coding":
        coding = {k: v for k, v in {
            "system": answer.value_coding_system,
            "code": answer.value_coding_code,
            "display": answer.value_coding_display,
        }.items() if v is not None}
        if coding:
            data["valueCoding"] = coding
    elif vt == "quantity":
        qty = {k: v for k, v in {
            "value": answer.value_quantity_value,
            "unit": answer.value_quantity_unit,
            "system": answer.value_quantity_system,
            "code": answer.value_quantity_code,
        }.items() if v is not None}
        if qty:
            data["valueQuantity"] = qty
    elif vt == "reference":
        ref: dict = {}
        if answer.value_reference:
            ref["reference"] = answer.value_reference
        if answer.value_reference_display:
            ref["display"] = answer.value_reference_display
        if ref:
            data["valueReference"] = ref

    return data


def _map_answer_to_plain(answer: "QuestionnaireResponseAnswerModel") -> dict:
    vt = answer.value_type
    data: dict = {"value_type": vt}

    if vt == "boolean":
        data["value_boolean"] = answer.value_boolean
    elif vt == "decimal":
        data["value_decimal"] = answer.value_decimal
    elif vt == "integer":
        data["value_integer"] = answer.value_integer
    elif vt in ("date", "time", "string", "uri"):
        data["value_string"] = answer.value_string
    elif vt == "dateTime":
        data["value_datetime"] = answer.value_datetime.isoformat() if answer.value_datetime else None
    elif vt == "coding":
        data["value_coding"] = {k: v for k, v in {
            "system": answer.value_coding_system,
            "code": answer.value_coding_code,
            "display": answer.value_coding_display,
        }.items() if v is not None}
    elif vt == "quantity":
        data["value_quantity"] = {k: v for k, v in {
            "value": answer.value_quantity_value,
            "unit": answer.value_quantity_unit,
            "system": answer.value_quantity_system,
            "code": answer.value_quantity_code,
        }.items() if v is not None}
    elif vt == "reference":
        data["value_reference"] = answer.value_reference
        data["value_reference_display"] = answer.value_reference_display

    # Always keep value_type; strip other None values except booleans (False is valid)
    return {k: v for k, v in data.items() if k == "value_type" or v is not None}


# ── Item mapper ────────────────────────────────────────────────────────────


def _map_item_to_fhir(item: "QuestionnaireResponseItemModel") -> dict:
    data: dict = {"linkId": item.link_id}
    if item.text:
        data["text"] = item.text
    if item.definition:
        data["definition"] = item.definition
    if item.answers:
        data["answer"] = [_map_answer_to_fhir(a) for a in item.answers]
    if item.sub_items:
        data["item"] = [_map_item_to_fhir(sub) for sub in item.sub_items]
    return data


def _map_item_to_plain(item: "QuestionnaireResponseItemModel") -> dict:
    data: dict = {"link_id": item.link_id}
    if item.text:
        data["text"] = item.text
    if item.definition:
        data["definition"] = item.definition
    if item.answers:
        data["answer"] = [_map_answer_to_plain(a) for a in item.answers]
    if item.sub_items:
        data["item"] = [_map_item_to_plain(sub) for sub in item.sub_items]
    return data


# ── Top-level mappers ──────────────────────────────────────────────────────


def to_fhir_questionnaire_response(qr: "QuestionnaireResponseModel") -> dict:
    """
    Convert QuestionnaireResponseModel (with relationships loaded) to a
    FHIR R4 QuestionnaireResponse dict.

    Rules:
      - Uses questionnaire_response_id (public) as FHIR logical id.
      - References reconstructed from stored type enum + public ID.
      - Encounter reference uses loaded relationship → public encounter_id.
      - Nested items reconstructed from sub_items relationships.
    """
    result: dict = {
        "resourceType": "QuestionnaireResponse",
        "id": str(qr.questionnaire_response_id),
        "questionnaire": qr.questionnaire,
        "status": qr.status,
    }

    # subject
    if qr.subject_type and qr.subject_id:
        subject: dict = {
            "reference": f"{qr.subject_type.value}/{qr.subject_id}"
        }
        if qr.subject_display:
            subject["display"] = qr.subject_display
        result["subject"] = subject

    # encounter (via FK relationship → public encounter_id)
    if qr.encounter and qr.encounter.encounter_id:
        result["encounter"] = {
            "reference": f"Encounter/{qr.encounter.encounter_id}"
        }

    if qr.authored:
        result["authored"] = qr.authored.isoformat()

    # author
    if qr.author_reference_type and qr.author_reference_id:
        author: dict = {
            "reference": f"{qr.author_reference_type.value}/{qr.author_reference_id}"
        }
        if qr.author_reference_display:
            author["display"] = qr.author_reference_display
        result["author"] = author

    # source
    if qr.source_reference_type and qr.source_reference_id:
        source: dict = {
            "reference": f"{qr.source_reference_type.value}/{qr.source_reference_id}"
        }
        if qr.source_reference_display:
            source["display"] = qr.source_reference_display
        result["source"] = source

    # Only emit top-level items (parent_item_id is None); sub_items carry the children
    top_level = [i for i in qr.items if i.parent_item_id is None]
    if top_level:
        result["item"] = [_map_item_to_fhir(i) for i in top_level]

    return {k: v for k, v in result.items() if v is not None}


def to_plain_questionnaire_response(qr: "QuestionnaireResponseModel") -> dict:
    """
    Return the QuestionnaireResponse as a flat snake_case JSON object.
    Uses public questionnaire_response_id as `id`.
    """
    result: dict = {
        "id": qr.questionnaire_response_id,
        "user_id": qr.user_id,
        "org_id": qr.org_id,
        "questionnaire": qr.questionnaire,
        "status": qr.status.value if qr.status else None,
        "subject_type": qr.subject_type.value if qr.subject_type else None,
        "subject_id": qr.subject_id,
        "subject_display": qr.subject_display,
        "encounter_id": (
            qr.encounter.encounter_id
            if qr.encounter and qr.encounter.encounter_id
            else None
        ),
        "authored": qr.authored.isoformat() if qr.authored else None,
        "author_type": qr.author_reference_type.value if qr.author_reference_type else None,
        "author_id": qr.author_reference_id,
        "author_display": qr.author_reference_display,
        "source_type": qr.source_reference_type.value if qr.source_reference_type else None,
        "source_id": qr.source_reference_id,
        "source_display": qr.source_reference_display,
    }

    top_level = [i for i in qr.items if i.parent_item_id is None]
    if top_level:
        result["item"] = [_map_item_to_plain(i) for i in top_level]

    return {k: v for k, v in result.items() if v is not None}
