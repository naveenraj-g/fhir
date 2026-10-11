from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.task.task import (
        TaskBasedOn,
        TaskIdentifier,
        TaskInput,
        TaskInsurance,
        TaskModel,
        TaskNote,
        TaskOutput,
        TaskPartOf,
        TaskPerformerType,
        TaskRelevantHistory,
        TaskRestrictionRecipient,
    )


def _ev(v):
    return v.value if v and hasattr(v, "value") else v


def _ref(ref_type, ref_id, display) -> dict | None:
    if not (ref_type and ref_id):
        return None
    t = _ev(ref_type)
    r: dict = {"reference": f"{t}/{ref_id}"}
    if display:
        r["display"] = display
    return r


def _cc(system, code, display, text) -> dict | None:
    coding = {k: v for k, v in {"system": system, "code": code, "display": display}.items() if v}
    result: dict = {}
    if coding:
        result["coding"] = [coding]
    if text:
        result["text"] = text
    return result if result else None


def fhir_task_identifier(i: "TaskIdentifier") -> dict:
    entry: dict = {}
    if i.use:
        entry["use"] = i.use
    coding = {k: v for k, v in {
        "system": i.type_system, "code": i.type_code, "display": i.type_display,
    }.items() if v}
    type_cc: dict = {}
    if coding:
        type_cc["coding"] = [coding]
    if i.type_text:
        type_cc["text"] = i.type_text
    if type_cc:
        entry["type"] = type_cc
    if i.system:
        entry["system"] = i.system
    if i.value:
        entry["value"] = i.value
    period: dict = {}
    if i.period_start:
        period["start"] = i.period_start.isoformat()
    if i.period_end:
        period["end"] = i.period_end.isoformat()
    if period:
        entry["period"] = period
    if i.assigner:
        entry["assigner"] = {"display": i.assigner}
    return entry


def fhir_task_note(n: "TaskNote") -> dict:
    entry: dict = {"text": n.text}
    if n.time:
        entry["time"] = n.time.isoformat()
    if n.author_string:
        entry["authorString"] = n.author_string
    elif n.author_reference_type and n.author_reference_id:
        entry["authorReference"] = {"reference": f"{n.author_reference_type}/{n.author_reference_id}"}
        if n.author_reference_display:
            entry["authorReference"]["display"] = n.author_reference_display
    return entry


def _strip(d: dict) -> dict:
    """Drop None values (keeps 0 / False)."""
    return {k: v for k, v in d.items() if v is not None}


def _fhir_value_x(item: "TaskInput | TaskOutput") -> dict:
    """Emit the single populated value[x] element of a Task.input / Task.output row."""
    g = lambda name: getattr(item, f"value_{name}", None)  # noqa: E731
    simple = (
        ("boolean", "valueBoolean", lambda v: v),
        ("code", "valueCode", lambda v: v),
        ("date", "valueDate", lambda v: v.isoformat()),
        ("date_time", "valueDateTime", lambda v: v.isoformat()),
        ("decimal", "valueDecimal", float),
        ("integer", "valueInteger", lambda v: v),
        ("string", "valueString", lambda v: v),
        ("uri", "valueUri", lambda v: v),
        ("time", "valueTime", lambda v: v),
        ("instant", "valueInstant", lambda v: v.isoformat()),
        ("markdown", "valueMarkdown", lambda v: v),
        ("canonical", "valueCanonical", lambda v: v),
        ("url", "valueUrl", lambda v: v),
        ("positive_int", "valuePositiveInt", lambda v: v),
        ("unsigned_int", "valueUnsignedInt", lambda v: v),
        ("base64_binary", "valueBase64Binary", lambda v: v),
        ("id", "valueId", lambda v: v),
    )
    for name, key, conv in simple:
        if g(name) is not None:
            return {key: conv(g(name))}

    if item.value_reference_type and item.value_reference_id is not None:
        ref: dict = {"reference": f"{item.value_reference_type}/{item.value_reference_id}"}
        if item.value_reference_display:
            ref["display"] = item.value_reference_display
        return {"valueReference": ref}

    if any(g(f"coding_{n}") for n in ("system", "code", "display")):
        return {"valueCoding": _strip({"system": g("coding_system"), "code": g("coding_code"), "display": g("coding_display")})}
    cc = _cc(g("codeable_concept_system"), g("codeable_concept_code"), g("codeable_concept_display"), g("codeable_concept_text"))
    if cc:
        return {"valueCodeableConcept": cc}
    if any(g(f"quantity_{n}") is not None for n in ("value", "unit", "system", "code")):
        return {"valueQuantity": _strip({
            "value": g("quantity_value"), "unit": g("quantity_unit"),
            "system": g("quantity_system"), "code": g("quantity_code")})}
    if g("period_start") or g("period_end"):
        return {"valuePeriod": _strip({
            "start": g("period_start").isoformat() if g("period_start") else None,
            "end": g("period_end").isoformat() if g("period_end") else None})}
    if any(g(f"range_{n}") is not None for n in ("low_value", "low_unit", "high_value", "high_unit")):
        rng: dict = {}
        low = _strip({"value": g("range_low_value"), "unit": g("range_low_unit")})
        high = _strip({"value": g("range_high_value"), "unit": g("range_high_unit")})
        if low:
            rng["low"] = low
        if high:
            rng["high"] = high
        return {"valueRange": rng}
    if any(g(f"attachment_{n}") is not None for n in (
            "content_type", "language", "data", "url", "size", "hash", "title", "creation")):
        creation = g("attachment_creation")
        return {"valueAttachment": _strip({
            "contentType": g("attachment_content_type"), "language": g("attachment_language"),
            "data": g("attachment_data"), "url": g("attachment_url"), "size": g("attachment_size"),
            "hash": g("attachment_hash"), "title": g("attachment_title"),
            "creation": creation.isoformat() if creation else None})}
    if any(g(f"identifier_{n}") for n in ("use", "system", "value")):
        return {"valueIdentifier": _strip({
            "use": g("identifier_use"), "system": g("identifier_system"), "value": g("identifier_value")})}
    if g("money_value") is not None or g("money_currency"):
        return {"valueMoney": _strip({"value": g("money_value"), "currency": g("money_currency")})}
    if any(g(f"ratio_{n}") is not None for n in (
            "numerator_value", "numerator_unit", "denominator_value", "denominator_unit")):
        ratio: dict = {}
        num = _strip({"value": g("ratio_numerator_value"), "unit": g("ratio_numerator_unit")})
        den = _strip({"value": g("ratio_denominator_value"), "unit": g("ratio_denominator_unit")})
        if num:
            ratio["numerator"] = num
        if den:
            ratio["denominator"] = den
        return {"valueRatio": ratio}
    return {}


def fhir_task_input(i: "TaskInput") -> dict:
    type_cc = _cc(i.type_system, i.type_code, i.type_display, i.type_text) or {}
    entry: dict = {"type": type_cc}
    entry.update(_fhir_value_x(i))
    return entry


def fhir_task_output(o: "TaskOutput") -> dict:
    type_cc = _cc(o.type_system, o.type_code, o.type_display, o.type_text) or {}
    entry: dict = {"type": type_cc}
    entry.update(_fhir_value_x(o))
    return entry


def to_fhir_task(model: "TaskModel") -> dict:
    result: dict = {
        "resourceType": "Task",
        "id": str(model.task_id),
        "status": _ev(model.status),
        "intent": _ev(model.intent),
    }

    # identifier
    if model.identifiers:
        result["identifier"] = [fhir_task_identifier(i) for i in model.identifiers]

    # instantiatesCanonical / instantiatesUri
    if model.instantiates_canonical:
        result["instantiatesCanonical"] = model.instantiates_canonical
    if model.instantiates_uri:
        result["instantiatesUri"] = model.instantiates_uri

    # basedOn
    if model.based_on:
        result["basedOn"] = [
            {k: v for k, v in {
                "reference": f"{b.reference_type}/{b.reference_id}" if b.reference_type and b.reference_id else None,
                "display": b.reference_display,
            }.items() if v}
            for b in model.based_on
        ]

    # groupIdentifier
    gi: dict = {}
    if model.group_identifier_use:
        gi["use"] = model.group_identifier_use
    gi_type_cc: dict = {}
    gi_coding = {k: v for k, v in {
        "system": model.group_identifier_type_system,
        "code": model.group_identifier_type_code,
        "display": model.group_identifier_type_display,
    }.items() if v}
    if gi_coding:
        gi_type_cc["coding"] = [gi_coding]
    if model.group_identifier_type_text:
        gi_type_cc["text"] = model.group_identifier_type_text
    if gi_type_cc:
        gi["type"] = gi_type_cc
    if model.group_identifier_system:
        gi["system"] = model.group_identifier_system
    if model.group_identifier_value:
        gi["value"] = model.group_identifier_value
    if gi:
        result["groupIdentifier"] = gi

    # partOf
    if model.part_of:
        result["partOf"] = [
            {k: v for k, v in {
                "reference": f"{_ev(p.reference_type)}/{p.reference_id}" if p.reference_type and p.reference_id else None,
                "display": p.reference_display,
            }.items() if v}
            for p in model.part_of
        ]

    # statusReason
    sr = _cc(model.status_reason_system, model.status_reason_code, model.status_reason_display, model.status_reason_text)
    if sr:
        result["statusReason"] = sr

    # businessStatus
    bs = _cc(model.business_status_system, model.business_status_code, model.business_status_display, model.business_status_text)
    if bs:
        result["businessStatus"] = bs

    # priority
    if model.priority:
        result["priority"] = _ev(model.priority)

    # code
    code_cc = _cc(model.code_system, model.code_code, model.code_display, model.code_text)
    if code_cc:
        result["code"] = code_cc

    # description
    if model.description:
        result["description"] = model.description

    # focus
    focus = _ref(model.focus_type, model.focus_id, model.focus_display)
    if focus:
        result["focus"] = focus

    # for (Python keyword — use key "for")
    if model.for_type and model.for_id:
        for_ref: dict = {"reference": f"{model.for_type}/{model.for_id}"}
        if model.for_display:
            for_ref["display"] = model.for_display
        result["for"] = for_ref

    # encounter
    enc = _ref(model.encounter_type, model.encounter_id, model.encounter_display)
    if enc:
        result["encounter"] = enc

    # executionPeriod
    if model.execution_period_start or model.execution_period_end:
        ep: dict = {}
        if model.execution_period_start:
            ep["start"] = model.execution_period_start.isoformat()
        if model.execution_period_end:
            ep["end"] = model.execution_period_end.isoformat()
        result["executionPeriod"] = ep

    # authoredOn
    if model.authored_on:
        result["authoredOn"] = model.authored_on.isoformat()

    # lastModified
    if model.last_modified:
        result["lastModified"] = model.last_modified.isoformat()

    # requester
    req = _ref(model.requester_type, model.requester_id, model.requester_display)
    if req:
        result["requester"] = req

    # performerType
    if model.performer_types:
        result["performerType"] = [
            _cc(pt.coding_system, pt.coding_code, pt.coding_display, pt.text) or {}
            for pt in model.performer_types
        ]

    # owner
    own = _ref(model.owner_type, model.owner_id, model.owner_display)
    if own:
        result["owner"] = own

    # location
    loc = _ref(model.location_type, model.location_id, model.location_display)
    if loc:
        result["location"] = loc

    # reasonCode
    rc = _cc(model.reason_code_system, model.reason_code_code, model.reason_code_display, model.reason_code_text)
    if rc:
        result["reasonCode"] = rc

    # reasonReference
    rr = _ref(model.reason_reference_type, model.reason_reference_id, model.reason_reference_display)
    if rr:
        result["reasonReference"] = rr

    # insurance
    if model.insurance:
        result["insurance"] = [
            {k: v for k, v in {
                "reference": f"{_ev(ins.reference_type)}/{ins.reference_id}" if ins.reference_type and ins.reference_id else None,
                "display": ins.reference_display,
            }.items() if v}
            for ins in model.insurance
        ]

    # note
    if model.notes:
        result["note"] = [fhir_task_note(n) for n in model.notes]

    # relevantHistory
    if model.relevant_history:
        result["relevantHistory"] = [
            {k: v for k, v in {
                "reference": f"{_ev(rh.reference_type)}/{rh.reference_id}" if rh.reference_type and rh.reference_id else None,
                "display": rh.reference_display,
            }.items() if v}
            for rh in model.relevant_history
        ]

    # restriction
    has_restriction = (
        model.restriction_repetitions is not None
        or model.restriction_period_start is not None
        or model.restriction_period_end is not None
        or bool(model.restriction_recipients)
    )
    if has_restriction:
        restriction: dict = {}
        if model.restriction_repetitions is not None:
            restriction["repetitions"] = model.restriction_repetitions
        period: dict = {}
        if model.restriction_period_start:
            period["start"] = model.restriction_period_start.isoformat()
        if model.restriction_period_end:
            period["end"] = model.restriction_period_end.isoformat()
        if period:
            restriction["period"] = period
        if model.restriction_recipients:
            restriction["recipient"] = [
                {k: v for k, v in {
                    "reference": f"{_ev(rr.reference_type)}/{rr.reference_id}" if rr.reference_type and rr.reference_id else None,
                    "display": rr.reference_display,
                }.items() if v}
                for rr in model.restriction_recipients
            ]
        result["restriction"] = restriction

    # input
    if model.inputs:
        result["input"] = [fhir_task_input(i) for i in model.inputs]

    # output
    if model.outputs:
        result["output"] = [fhir_task_output(o) for o in model.outputs]

    return {k: v for k, v in result.items() if v is not None}
