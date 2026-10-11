"""
Response schemas for Procedure resources.

Mirrors the fhir-server PlainProcedure* shapes exactly (snake_case, the
`application/json` representation). `extra="allow"` on every schema means new
fhir-server fields pass through without needing a schema bump here.
"""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict


# ── Plain child-entry response schemas ────────────────────────────────────────


class PlainProcedureIdentifier(BaseModel):
    """Identifier child entry (Procedure.identifier)."""

    model_config = ConfigDict(extra="allow")
    id: int
    use: Optional[str] = None
    type_system: Optional[str] = None
    type_code: Optional[str] = None
    type_display: Optional[str] = None
    type_text: Optional[str] = None
    system: Optional[str] = None
    value: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    assigner: Optional[str] = None


class PlainProcedureReference(BaseModel):
    """
    Generic reference child entry.

    Shared shape for basedOn, partOf, reasonReference, report,
    complicationDetail and usedReference (type + public id + display).
    """

    model_config = ConfigDict(extra="allow")
    id: int
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    reference_display: Optional[str] = None


class PlainProcedureCodeableConcept(BaseModel):
    """
    Generic CodeableConcept child entry.

    Shared shape for reasonCode, bodySite, complication, followUp and usedCode.
    """

    model_config = ConfigDict(extra="allow")
    id: int
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class PlainProcedurePerformer(BaseModel):
    """Performer child entry (function, actor, onBehalfOf)."""

    model_config = ConfigDict(extra="allow")
    id: int
    function_system: Optional[str] = None
    function_code: Optional[str] = None
    function_display: Optional[str] = None
    function_text: Optional[str] = None
    actor_type: Optional[str] = None
    actor_id: Optional[int] = None
    actor_display: Optional[str] = None
    on_behalf_of_type: Optional[str] = None
    on_behalf_of_id: Optional[int] = None
    on_behalf_of_display: Optional[str] = None


class PlainProcedureNote(BaseModel):
    """Note child entry (Annotation)."""

    model_config = ConfigDict(extra="allow")
    id: int
    text: Optional[str] = None
    time: Optional[str] = None
    author_string: Optional[str] = None
    author_reference_type: Optional[str] = None
    author_reference_id: Optional[int] = None
    author_reference_display: Optional[str] = None


class PlainProcedureFocalDevice(BaseModel):
    """FocalDevice child entry (action, manipulated device reference)."""

    model_config = ConfigDict(extra="allow")
    id: int
    action_system: Optional[str] = None
    action_code: Optional[str] = None
    action_display: Optional[str] = None
    action_text: Optional[str] = None
    manipulated_reference_type: Optional[str] = None
    manipulated_reference_id: Optional[int] = None
    manipulated_reference_display: Optional[str] = None


# ── Plain top-level response ──────────────────────────────────────────────────


class ProcedureResponse(BaseModel):
    """Full plain JSON response for a single Procedure."""

    model_config = ConfigDict(extra="allow")

    id: int
    status: Optional[str] = None

    status_reason_system: Optional[str] = None
    status_reason_code: Optional[str] = None
    status_reason_display: Optional[str] = None
    status_reason_text: Optional[str] = None
    category_system: Optional[str] = None
    category_code: Optional[str] = None
    category_display: Optional[str] = None
    category_text: Optional[str] = None
    code_system: Optional[str] = None
    code_code: Optional[str] = None
    code_display: Optional[str] = None
    code_text: Optional[str] = None

    subject_type: Optional[str] = None
    subject_id: Optional[int] = None
    subject_display: Optional[str] = None
    encounter_type: Optional[str] = None
    encounter_id: Optional[int] = None
    encounter_display: Optional[str] = None

    performed_datetime: Optional[str] = None
    performed_period_start: Optional[str] = None
    performed_period_end: Optional[str] = None
    performed_string: Optional[str] = None
    performed_age_value: Optional[float] = None
    performed_age_comparator: Optional[str] = None
    performed_age_unit: Optional[str] = None
    performed_age_system: Optional[str] = None
    performed_age_code: Optional[str] = None
    performed_range_low_value: Optional[float] = None
    performed_range_low_unit: Optional[str] = None
    performed_range_low_system: Optional[str] = None
    performed_range_low_code: Optional[str] = None
    performed_range_high_value: Optional[float] = None
    performed_range_high_unit: Optional[str] = None
    performed_range_high_system: Optional[str] = None
    performed_range_high_code: Optional[str] = None

    recorder_type: Optional[str] = None
    recorder_id: Optional[int] = None
    recorder_display: Optional[str] = None
    asserter_type: Optional[str] = None
    asserter_id: Optional[int] = None
    asserter_display: Optional[str] = None
    location_type: Optional[str] = None
    location_id: Optional[int] = None
    location_display: Optional[str] = None

    outcome_system: Optional[str] = None
    outcome_code: Optional[str] = None
    outcome_display: Optional[str] = None
    outcome_text: Optional[str] = None

    instantiates_canonical: Optional[List[str]] = None
    instantiates_uri: Optional[List[str]] = None

    identifier: Optional[List[PlainProcedureIdentifier]] = None
    based_on: Optional[List[PlainProcedureReference]] = None
    part_of: Optional[List[PlainProcedureReference]] = None
    performer: Optional[List[PlainProcedurePerformer]] = None
    reason_code: Optional[List[PlainProcedureCodeableConcept]] = None
    reason_reference: Optional[List[PlainProcedureReference]] = None
    body_site: Optional[List[PlainProcedureCodeableConcept]] = None
    report: Optional[List[PlainProcedureReference]] = None
    complication: Optional[List[PlainProcedureCodeableConcept]] = None
    complication_detail: Optional[List[PlainProcedureReference]] = None
    follow_up: Optional[List[PlainProcedureCodeableConcept]] = None
    note: Optional[List[PlainProcedureNote]] = None
    focal_device: Optional[List[PlainProcedureFocalDevice]] = None
    used_reference: Optional[List[PlainProcedureReference]] = None
    used_code: Optional[List[PlainProcedureCodeableConcept]] = None

    # Tenant + audit columns.
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None


class PaginatedProcedureResponse(BaseModel):
    """Paginated list wrapper for Procedure resources."""

    model_config = ConfigDict(extra="allow")

    total: int
    limit: int
    offset: int
    data: List[ProcedureResponse]
