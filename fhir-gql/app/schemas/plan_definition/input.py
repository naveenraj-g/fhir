"""
Input schemas for the PlanDefinition resource (FHIR R4) — fhir-gql gateway copy.

Mirrors the fhir-server contract; the fhir-server remains the source of truth for persistence.

https://www.hl7.org/fhir/R4/plandefinition.html

Conventions:
  * CodeableConcept 0..1 fields are flat `<field>_system/_code/_display/_text`; 0..* CodeableConcepts are
    lists of `{coding_system, coding_code, coding_display, text}`.
  * References are `Type/id` strings (format + allowed type validated, existence never).
  * Complex datatypes (Quantity, Range, Period, Expression, Attachment, Timing) are nested objects.
  * Choice types (`subject[x]`, `timing[x]`, `definition[x]`, `detail[x]`, ...) allow at most one variant.
  * `action` nests recursively; the tree is validated for the R4 trigger / data-requirement / expression
    invariants and for referential integrity (goal ids, related-action ids).
"""

from __future__ import annotations

from datetime import date as Date, datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.enums import (
    ActionCardinalityBehavior,
    ActionConditionKind,
    ActionGroupingBehavior,
    ActionParticipantType,
    ActionPrecheckBehavior,
    ActionPriority,
    ActionRelationshipType,
    ActionRequiredBehavior,
    ActionSelectionBehavior,
    PlanDefinitionContactKind,
    PlanDefinitionStatus,
    RelatedArtifactType,
    SortDirection,
    TriggerType,
)


def _utc(d: datetime) -> datetime:
    return d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d


def _any(*values) -> bool:
    return any(v is not None for v in values)


def _one(groups: dict, what: str) -> None:
    """Raise unless at most one choice-type variant is populated."""
    used = [name for name, present in groups.items() if present]
    if len(used) > 1:
        raise ValueError(f"{what}: supply at most one variant; got {used}.")


# ── Nested datatypes ───────────────────────────────────────────────────────────


class PdQuantityInput(BaseModel):
    """Quantity / Duration / Age."""

    model_config = ConfigDict(extra="forbid")

    value: Optional[float] = None
    comparator: Optional[str] = Field(None, description="< | <= | >= | >")
    unit: Optional[str] = None
    system: Optional[str] = None
    code: Optional[str] = None


class PdSimpleQuantityInput(BaseModel):
    """SimpleQuantity (Range bound): a Quantity without comparator."""

    model_config = ConfigDict(extra="forbid")

    value: Optional[float] = None
    unit: Optional[str] = None
    system: Optional[str] = None
    code: Optional[str] = None


class PdRangeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    low: Optional[PdSimpleQuantityInput] = None
    high: Optional[PdSimpleQuantityInput] = None


class PdPeriodInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start: Optional[datetime] = None
    end: Optional[datetime] = None

    @model_validator(mode="after")
    def _ordered(self):
        if self.start and self.end and _utc(self.end) < _utc(self.start):
            raise ValueError("Period end must not be before start.")
        return self


class PdExpressionInput(BaseModel):
    """Expression — `language` is required and either `expression` or `reference` must be given (exp-1)."""

    model_config = ConfigDict(extra="forbid")

    description: Optional[str] = None
    name: Optional[str] = Field(None, description="Short name for reuse (an id).")
    language: str = Field(..., description="Media type of the language, e.g. text/cql, text/fhirpath, application/x-fhir-query.")
    expression: Optional[str] = None
    reference: Optional[str] = Field(None, description="URI where the expression is found.")

    @model_validator(mode="after")
    def _exp1(self):
        if not (self.expression or self.reference):
            raise ValueError("exp-1: an expression or a reference must be provided.")
        return self


class PdAttachmentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content_type: Optional[str] = None
    language: Optional[str] = None
    data: Optional[str] = Field(None, description="base64Binary content.")
    url: Optional[str] = None
    size: Optional[int] = Field(None, ge=0)
    hash: Optional[str] = None
    title: Optional[str] = None
    creation: Optional[datetime] = None


class PdCodeableConceptInput(BaseModel):
    """Nested CodeableConcept (used inside Timing.code)."""

    model_config = ConfigDict(extra="forbid")

    system: Optional[str] = None
    code: Optional[str] = None
    display: Optional[str] = None
    text: Optional[str] = None


class PdTimingRepeatInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bounds_duration: Optional[PdQuantityInput] = None
    bounds_range: Optional[PdRangeInput] = None
    bounds_period: Optional[PdPeriodInput] = None
    count: Optional[int] = Field(None, ge=1)
    count_max: Optional[int] = Field(None, ge=1)
    duration: Optional[float] = None
    duration_max: Optional[float] = None
    duration_unit: Optional[str] = Field(None, description="s|min|h|d|wk|mo|a")
    frequency: Optional[int] = Field(None, ge=1)
    frequency_max: Optional[int] = Field(None, ge=1)
    period: Optional[float] = None
    period_max: Optional[float] = None
    period_unit: Optional[str] = Field(None, description="s|min|h|d|wk|mo|a")
    day_of_week: Optional[List[str]] = Field(None, description="mon|tue|wed|thu|fri|sat|sun")
    time_of_day: Optional[List[str]] = Field(None, description="HH:MM:SS values.")
    when: Optional[List[str]] = Field(None, description="EventTiming codes e.g. MORN, AC, PCV.")
    offset: Optional[int] = Field(None, ge=0)

    @model_validator(mode="after")
    def _bounds_one(self):
        _one({
            "boundsDuration": self.bounds_duration is not None,
            "boundsRange": self.bounds_range is not None,
            "boundsPeriod": self.bounds_period is not None,
        }, "Timing.repeat.bounds[x]")
        return self


class PdTimingInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event: Optional[List[datetime]] = None
    code: Optional[PdCodeableConceptInput] = None
    repeat: Optional[PdTimingRepeatInput] = None


# ── Resource-level children ────────────────────────────────────────────────────


class PlanDefinitionIdentifierInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    use: Optional[str] = None
    type_system: Optional[str] = None
    type_code: Optional[str] = None
    type_display: Optional[str] = None
    type_text: Optional[str] = None
    system: Optional[str] = None
    value: str = Field(..., description="Identifier value.")
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    assigner: Optional[str] = None


class PlanDefinitionCodeableConceptInput(BaseModel):
    """CodeableConcept list entry (jurisdiction, topic, action.code, action.reason, goal.addresses)."""

    model_config = ConfigDict(extra="forbid")

    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class PlanDefinitionTelecomInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    system: Optional[str] = Field(None, description="phone|fax|email|pager|url|sms|other")
    value: Optional[str] = None
    use: Optional[str] = Field(None, description="home|work|temp|old|mobile")
    rank: Optional[int] = Field(None, ge=1)
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class PlanDefinitionContactInput(BaseModel):
    """ContactDetail (contact / author / editor / reviewer / endorser)."""

    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    telecom: Optional[List[PlanDefinitionTelecomInput]] = None


class PlanDefinitionUseContextInput(BaseModel):
    """useContext[] — UsageContext: code + exactly one value[x]."""

    model_config = ConfigDict(extra="forbid")

    code_system: Optional[str] = None
    code_code: str = Field(..., description="UsageContext.code (e.g. 'gender', 'age', 'focus').")
    code_display: Optional[str] = None

    value_cc_system: Optional[str] = None
    value_cc_code: Optional[str] = None
    value_cc_display: Optional[str] = None
    value_cc_text: Optional[str] = None
    value_quantity_value: Optional[float] = None
    value_quantity_unit: Optional[str] = None
    value_quantity_system: Optional[str] = None
    value_quantity_code: Optional[str] = None
    value_range_low_value: Optional[float] = None
    value_range_low_unit: Optional[str] = None
    value_range_low_system: Optional[str] = None
    value_range_low_code: Optional[str] = None
    value_range_high_value: Optional[float] = None
    value_range_high_unit: Optional[str] = None
    value_range_high_system: Optional[str] = None
    value_range_high_code: Optional[str] = None
    value_reference: Optional[str] = Field(
        None, description="FHIR reference: PlanDefinition|ResearchStudy|InsurancePlan|HealthcareService|Group|Location|Organization."
    )
    value_reference_display: Optional[str] = None

    @model_validator(mode="after")
    def _exactly_one(self):
        groups = {
            "CodeableConcept": any([self.value_cc_system, self.value_cc_code, self.value_cc_display, self.value_cc_text]),
            "Quantity": _any(self.value_quantity_value, self.value_quantity_unit, self.value_quantity_system, self.value_quantity_code),
            "Range": _any(
                self.value_range_low_value, self.value_range_low_unit, self.value_range_low_system, self.value_range_low_code,
                self.value_range_high_value, self.value_range_high_unit, self.value_range_high_system, self.value_range_high_code),
            "Reference": self.value_reference is not None,
        }
        used = [k for k, v in groups.items() if v]
        if len(used) != 1:
            raise ValueError(f"useContext requires exactly one value[x] variant; got {used or 'none'}.")
        return self


class PlanDefinitionRelatedArtifactInput(BaseModel):
    """RelatedArtifact — type is required; document is an Attachment, resource a canonical."""

    model_config = ConfigDict(extra="forbid")

    type: RelatedArtifactType = Field(
        ..., description="documentation|justification|citation|predecessor|successor|derived-from|depends-on|composed-of"
    )
    label: Optional[str] = None
    display: Optional[str] = None
    citation: Optional[str] = Field(None, description="Bibliographic citation (markdown).")
    url: Optional[str] = None
    document: Optional[PdAttachmentInput] = None
    resource: Optional[str] = Field(None, description="canonical(Any) of the related resource, e.g. 'http://x/PlanDefinition/1'.")


# ── goal ────────────────────────────────────────────────────────────────────────


class PlanDefinitionGoalTargetInput(BaseModel):
    """goal.target — measure, detail[x] (Quantity | Range | CodeableConcept) and due (Duration)."""

    model_config = ConfigDict(extra="forbid")

    measure_system: Optional[str] = None
    measure_code: Optional[str] = None
    measure_display: Optional[str] = None
    measure_text: Optional[str] = None
    detail_quantity: Optional[PdQuantityInput] = None
    detail_range: Optional[PdRangeInput] = None
    detail_cc_system: Optional[str] = None
    detail_cc_code: Optional[str] = None
    detail_cc_display: Optional[str] = None
    detail_cc_text: Optional[str] = None
    due: Optional[PdQuantityInput] = Field(None, description="Duration within which the target should be met.")

    @model_validator(mode="after")
    def _detail_one(self):
        _one({
            "Quantity": self.detail_quantity is not None,
            "Range": self.detail_range is not None,
            "CodeableConcept": any([self.detail_cc_system, self.detail_cc_code, self.detail_cc_display, self.detail_cc_text]),
        }, "goal.target.detail[x]")
        return self


class PlanDefinitionGoalInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    element_id: Optional[str] = Field(None, description="Element id other parts of the plan refer to (action.goal_id).")
    category_system: Optional[str] = None
    category_code: Optional[str] = None
    category_display: Optional[str] = None
    category_text: Optional[str] = None
    description_system: Optional[str] = None
    description_code: Optional[str] = None
    description_display: Optional[str] = None
    description_text: Optional[str] = None
    priority_system: Optional[str] = None
    priority_code: Optional[str] = None
    priority_display: Optional[str] = None
    priority_text: Optional[str] = None
    start_system: Optional[str] = None
    start_code: Optional[str] = None
    start_display: Optional[str] = None
    start_text: Optional[str] = None
    addresses: Optional[List[PlanDefinitionCodeableConceptInput]] = None
    documentation: Optional[List[PlanDefinitionRelatedArtifactInput]] = None
    target: Optional[List[PlanDefinitionGoalTargetInput]] = None

    @model_validator(mode="after")
    def _description_required(self):
        if not any([self.description_system, self.description_code, self.description_display, self.description_text]):
            raise ValueError("goal.description is required (1..1): provide description_code and/or description_text.")
        return self


# ── action pieces ───────────────────────────────────────────────────────────────


class PlanDefinitionCodingInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    system: Optional[str] = None
    code: Optional[str] = None
    display: Optional[str] = None


class PlanDefinitionCodeFilterInput(BaseModel):
    """DataRequirement.codeFilter — path xor search_param."""

    model_config = ConfigDict(extra="forbid")

    path: Optional[str] = None
    search_param: Optional[str] = None
    value_set: Optional[str] = Field(None, description="canonical(ValueSet)")
    code: Optional[List[PlanDefinitionCodingInput]] = None

    @model_validator(mode="after")
    def _path_xor_param(self):
        if bool(self.path) == bool(self.search_param):
            raise ValueError("drq-1: codeFilter needs exactly one of path or search_param.")
        return self


class PlanDefinitionDateFilterInput(BaseModel):
    """DataRequirement.dateFilter — path xor search_param; value[x] = dateTime | Period | Duration."""

    model_config = ConfigDict(extra="forbid")

    path: Optional[str] = None
    search_param: Optional[str] = None
    value_datetime: Optional[datetime] = None
    value_period: Optional[PdPeriodInput] = None
    value_duration: Optional[PdQuantityInput] = None

    @model_validator(mode="after")
    def _checks(self):
        if bool(self.path) == bool(self.search_param):
            raise ValueError("drq-2: dateFilter needs exactly one of path or search_param.")
        _one({
            "dateTime": self.value_datetime is not None,
            "Period": self.value_period is not None,
            "Duration": self.value_duration is not None,
        }, "dateFilter.value[x]")
        return self


class PlanDefinitionSortInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    direction: SortDirection = Field(..., description="ascending|descending")


class PlanDefinitionDataRequirementInput(BaseModel):
    """DataRequirement (action.input / action.output / trigger.data)."""

    model_config = ConfigDict(extra="forbid")

    type: str = Field(..., description="FHIR type the data is (FHIRAllTypes code), e.g. 'Patient', 'Observation'.")
    profile: Optional[List[str]] = Field(None, description="canonical(StructureDefinition) profiles.")
    subject_cc_system: Optional[str] = None
    subject_cc_code: Optional[str] = None
    subject_cc_display: Optional[str] = None
    subject_cc_text: Optional[str] = None
    subject_reference: Optional[str] = Field(None, description="Group reference e.g. 'Group/1'.")
    subject_reference_display: Optional[str] = None
    must_support: Optional[List[str]] = None
    code_filter: Optional[List[PlanDefinitionCodeFilterInput]] = None
    date_filter: Optional[List[PlanDefinitionDateFilterInput]] = None
    limit: Optional[int] = Field(None, ge=1)
    sort: Optional[List[PlanDefinitionSortInput]] = None

    @model_validator(mode="after")
    def _subject_one(self):
        _one({
            "CodeableConcept": any([self.subject_cc_system, self.subject_cc_code, self.subject_cc_display, self.subject_cc_text]),
            "Reference": self.subject_reference is not None,
        }, "DataRequirement.subject[x]")
        return self


class PlanDefinitionTriggerInput(BaseModel):
    """action.trigger — TriggerDefinition."""

    model_config = ConfigDict(extra="forbid")

    type: TriggerType = Field(..., description="named-event|periodic|data-changed|data-added|data-modified|data-removed|data-accessed|data-access-ended")
    name: Optional[str] = None
    timing_timing: Optional[PdTimingInput] = None
    timing_reference: Optional[str] = Field(None, description="Schedule reference e.g. 'Schedule/200001'.")
    timing_reference_display: Optional[str] = None
    timing_date: Optional[Date] = None
    timing_datetime: Optional[datetime] = None
    data: Optional[List[PlanDefinitionDataRequirementInput]] = Field(None, description="Triggering data (multiple = 'and').")
    condition: Optional[PdExpressionInput] = Field(None, description="Boolean expression; only allowed when `data` is present (trd-2).")

    @model_validator(mode="after")
    def _trigger_rules(self):
        _one({
            "Timing": self.timing_timing is not None,
            "Reference": self.timing_reference is not None,
            "date": self.timing_date is not None,
            "dateTime": self.timing_datetime is not None,
        }, "trigger.timing[x]")
        has_timing = any([self.timing_timing, self.timing_reference, self.timing_date, self.timing_datetime])
        if has_timing and self.data:
            raise ValueError("trd-1: a trigger has either timing or data requirements, not both.")
        if self.condition is not None and not self.data:
            raise ValueError("trd-2: a trigger condition is only allowed together with data.")
        return self


class PlanDefinitionConditionInput(BaseModel):
    """action.condition — kind + Expression."""

    model_config = ConfigDict(extra="forbid")

    kind: ActionConditionKind = Field(..., description="applicability|start|stop")
    expression: Optional[PdExpressionInput] = None


class PlanDefinitionRelatedActionInput(BaseModel):
    """action.relatedAction — points at another action's element id."""

    model_config = ConfigDict(extra="forbid")

    action_id: str = Field(..., description="element_id of the related action.")
    relationship: ActionRelationshipType = Field(
        ..., description="before-start|before|before-end|concurrent-with-start|concurrent|concurrent-with-end|after-start|after|after-end"
    )
    offset_duration: Optional[PdQuantityInput] = None
    offset_range: Optional[PdRangeInput] = None

    @model_validator(mode="after")
    def _offset_one(self):
        _one({"Duration": self.offset_duration is not None, "Range": self.offset_range is not None}, "relatedAction.offset[x]")
        return self


class PlanDefinitionParticipantInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: ActionParticipantType = Field(..., description="patient|practitioner|related-person|device")
    role_system: Optional[str] = None
    role_code: Optional[str] = None
    role_display: Optional[str] = None
    role_text: Optional[str] = None


class PlanDefinitionDynamicValueInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: Optional[str] = None
    expression: Optional[PdExpressionInput] = None


class PlanDefinitionActionInput(BaseModel):
    """action[] — a step in the plan; nests recursively through `action`."""

    model_config = ConfigDict(extra="forbid")

    element_id: Optional[str] = Field(None, description="Element id other actions refer to (relatedAction.action_id).")
    prefix: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    text_equivalent: Optional[str] = None
    priority: Optional[ActionPriority] = Field(None, description="routine|urgent|asap|stat")
    code: Optional[List[PlanDefinitionCodeableConceptInput]] = None
    reason: Optional[List[PlanDefinitionCodeableConceptInput]] = None
    documentation: Optional[List[PlanDefinitionRelatedArtifactInput]] = None
    goal_id: Optional[List[str]] = Field(None, description="element_id values of the goals this action addresses.")

    subject_cc_system: Optional[str] = None
    subject_cc_code: Optional[str] = None
    subject_cc_display: Optional[str] = None
    subject_cc_text: Optional[str] = None
    subject_reference: Optional[str] = Field(None, description="Group reference e.g. 'Group/1'.")
    subject_reference_display: Optional[str] = None

    trigger: Optional[List[PlanDefinitionTriggerInput]] = None
    condition: Optional[List[PlanDefinitionConditionInput]] = None
    input: Optional[List[PlanDefinitionDataRequirementInput]] = None
    output: Optional[List[PlanDefinitionDataRequirementInput]] = None
    related_action: Optional[List[PlanDefinitionRelatedActionInput]] = None

    timing_datetime: Optional[datetime] = None
    timing_age: Optional[PdQuantityInput] = None
    timing_period: Optional[PdPeriodInput] = None
    timing_duration: Optional[PdQuantityInput] = None
    timing_range: Optional[PdRangeInput] = None
    timing_timing: Optional[PdTimingInput] = None

    participant: Optional[List[PlanDefinitionParticipantInput]] = None
    type_system: Optional[str] = None
    type_code: Optional[str] = Field(None, description="create|update|remove|fire-event (extensible).")
    type_display: Optional[str] = None
    type_text: Optional[str] = None
    grouping_behavior: Optional[ActionGroupingBehavior] = Field(None, description="visual-group|logical-group|sentence-group")
    selection_behavior: Optional[ActionSelectionBehavior] = Field(None, description="any|all|all-or-none|exactly-one|at-most-one|one-or-more")
    required_behavior: Optional[ActionRequiredBehavior] = Field(None, description="must|could|must-unless-documented")
    precheck_behavior: Optional[ActionPrecheckBehavior] = Field(None, description="yes|no")
    cardinality_behavior: Optional[ActionCardinalityBehavior] = Field(None, description="single|multiple")

    definition_canonical: Optional[str] = Field(None, description="canonical(ActivityDefinition | PlanDefinition | Questionnaire).")
    definition_uri: Optional[str] = None
    transform: Optional[str] = Field(None, description="canonical(StructureMap)")
    dynamic_value: Optional[List[PlanDefinitionDynamicValueInput]] = None
    action: Optional[List["PlanDefinitionActionInput"]] = Field(None, description="Nested actions.")

    @model_validator(mode="after")
    def _choice_types(self):
        _one({
            "dateTime": self.timing_datetime is not None,
            "Age": self.timing_age is not None,
            "Period": self.timing_period is not None,
            "Duration": self.timing_duration is not None,
            "Range": self.timing_range is not None,
            "Timing": self.timing_timing is not None,
        }, "action.timing[x]")
        _one({
            "CodeableConcept": any([self.subject_cc_system, self.subject_cc_code, self.subject_cc_display, self.subject_cc_text]),
            "Reference": self.subject_reference is not None,
        }, "action.subject[x]")
        _one({"canonical": self.definition_canonical is not None, "uri": self.definition_uri is not None}, "action.definition[x]")
        return self


PlanDefinitionActionInput.model_rebuild()


def validate_plan_tree(goals, actions, known_goal_ids: Optional[set] = None, check_goal_ids: bool = True) -> None:
    """
    Referential integrity across the goal / action tree:
      * goal element_ids are unique, action element_ids are unique;
      * every action.goal_id refers to a goal element_id (the plan's own goals, or `known_goal_ids`);
      * every relatedAction.action_id refers to an action element_id in the plan.
    """
    goal_ids = set(known_goal_ids or set())
    for g in goals or []:
        if g.element_id:
            if g.element_id in goal_ids:
                raise ValueError(f"Duplicate goal element_id '{g.element_id}'.")
            goal_ids.add(g.element_id)

    action_ids: set = set()
    used_goal_ids: list = []
    related: list = []

    def walk(nodes):
        for a in nodes or []:
            if a.element_id:
                if a.element_id in action_ids:
                    raise ValueError(f"Duplicate action element_id '{a.element_id}'.")
                action_ids.add(a.element_id)
            used_goal_ids.extend(a.goal_id or [])
            related.extend(r.action_id for r in (a.related_action or []))
            walk(a.action)

    walk(actions)
    if check_goal_ids:
        for gid in used_goal_ids:
            if gid not in goal_ids:
                raise ValueError(f"action.goal_id '{gid}' does not match any goal element_id.")
    for rid in related:
        if rid not in action_ids:
            raise ValueError(f"relatedAction.action_id '{rid}' does not match any action element_id.")


# ── Create / Patch ─────────────────────────────────────────────────────────────


class PlanDefinitionCreateSchema(BaseModel):
    """Request body for POST /plan-definitions. Only `status` is required (R4 1..1)."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "user_id": "user-123",
                "org_id": "org-456",
                "url": "http://example.org/fhir/PlanDefinition/diabetes-care",
                "version": "1.0.0",
                "name": "diabetes_care",
                "title": "Diabetes care protocol",
                "status": "active",
                "type_code": "clinical-protocol",
                "publisher": "Example Health",
                "goal": [
                    {
                        "element_id": "g1",
                        "description_text": "HbA1c below 7%",
                        "target": [{"measure_code": "4548-4", "detail_range": {"high": {"value": 7, "unit": "%"}}}],
                    }
                ],
                "action": [
                    {
                        "element_id": "a1",
                        "title": "Order HbA1c",
                        "goal_id": ["g1"],
                        "timing_timing": {"repeat": {"frequency": 1, "period": 3, "period_unit": "mo"}},
                        "definition_canonical": "http://example.org/fhir/ActivityDefinition/hba1c",
                    },
                    {
                        "element_id": "a2",
                        "title": "Review results",
                        "related_action": [{"action_id": "a1", "relationship": "after", "offset_duration": {"value": 1, "unit": "d"}}],
                    },
                ],
            }
        },
    )

    user_id: Optional[str] = Field(None, description="JWT sub of the record owner.")
    org_id: Optional[str] = Field(None, description="Active organization ID from JWT.")
    created_by: Optional[str] = None

    url: Optional[str] = None
    version: Optional[str] = None
    name: Optional[str] = None
    title: Optional[str] = None
    subtitle: Optional[str] = None
    status: PlanDefinitionStatus = Field(..., description="draft|active|retired|unknown")
    experimental: Optional[bool] = None
    date: Optional[datetime] = Field(None, description="Date last changed.")
    publisher: Optional[str] = None
    description: Optional[str] = Field(None, description="markdown")
    purpose: Optional[str] = Field(None, description="markdown")
    usage: Optional[str] = None
    copyright: Optional[str] = Field(None, description="markdown")
    approval_date: Optional[Date] = None
    last_review_date: Optional[Date] = None
    effective_period_start: Optional[datetime] = None
    effective_period_end: Optional[datetime] = None

    type_system: Optional[str] = None
    type_code: Optional[str] = Field(None, description="order-set|clinical-protocol|eca-rule|workflow-definition (extensible).")
    type_display: Optional[str] = None
    type_text: Optional[str] = None

    subject_cc_system: Optional[str] = None
    subject_cc_code: Optional[str] = None
    subject_cc_display: Optional[str] = None
    subject_cc_text: Optional[str] = None
    subject_reference: Optional[str] = Field(None, description="Group reference e.g. 'Group/1'.")
    subject_reference_display: Optional[str] = None

    identifier: Optional[List[PlanDefinitionIdentifierInput]] = None
    contact: Optional[List[PlanDefinitionContactInput]] = None
    author: Optional[List[PlanDefinitionContactInput]] = None
    editor: Optional[List[PlanDefinitionContactInput]] = None
    reviewer: Optional[List[PlanDefinitionContactInput]] = None
    endorser: Optional[List[PlanDefinitionContactInput]] = None
    use_context: Optional[List[PlanDefinitionUseContextInput]] = None
    jurisdiction: Optional[List[PlanDefinitionCodeableConceptInput]] = None
    topic: Optional[List[PlanDefinitionCodeableConceptInput]] = None
    related_artifact: Optional[List[PlanDefinitionRelatedArtifactInput]] = None
    library: Optional[List[str]] = Field(None, description="canonical(Library) URLs.")
    goal: Optional[List[PlanDefinitionGoalInput]] = None
    action: Optional[List[PlanDefinitionActionInput]] = None

    @model_validator(mode="after")
    def _validate(self):
        if self.effective_period_start and self.effective_period_end and _utc(self.effective_period_end) < _utc(self.effective_period_start):
            raise ValueError("effective_period_end must not be before effective_period_start.")
        _one({
            "CodeableConcept": any([self.subject_cc_system, self.subject_cc_code, self.subject_cc_display, self.subject_cc_text]),
            "Reference": self.subject_reference is not None,
        }, "subject[x]")
        validate_plan_tree(self.goal, self.action)
        return self


class PlanDefinitionPatchSchema(BaseModel):
    """
    Request body for PATCH /plan-definitions/{id}. All optional. `status` cannot be null.

    Child lists (identifier, contact, author, editor, reviewer, endorser, use_context, jurisdiction, topic,
    related_artifact, library, goal, action) use REPLACE semantics: a list that is sent replaces the stored
    one in full, `[]` (or null) clears it, an omitted list is left untouched. Sending `action` replaces the
    ENTIRE action tree and `goal` the whole goal list. References are `Type/id` strings; null clears one.
    """

    model_config = ConfigDict(extra="forbid")

    url: Optional[str] = None
    version: Optional[str] = None
    name: Optional[str] = None
    title: Optional[str] = None
    subtitle: Optional[str] = None
    status: Optional[PlanDefinitionStatus] = Field(None, description="Cannot be null.")
    experimental: Optional[bool] = None
    date: Optional[datetime] = None
    publisher: Optional[str] = None
    description: Optional[str] = None
    purpose: Optional[str] = None
    usage: Optional[str] = None
    copyright: Optional[str] = None
    approval_date: Optional[Date] = None
    last_review_date: Optional[Date] = None
    effective_period_start: Optional[datetime] = None
    effective_period_end: Optional[datetime] = None
    type_system: Optional[str] = None
    type_code: Optional[str] = None
    type_display: Optional[str] = None
    type_text: Optional[str] = None
    subject_cc_system: Optional[str] = None
    subject_cc_code: Optional[str] = None
    subject_cc_display: Optional[str] = None
    subject_cc_text: Optional[str] = None
    subject_reference: Optional[str] = None
    subject_reference_display: Optional[str] = None
    updated_by: Optional[str] = None

    identifier: Optional[List[PlanDefinitionIdentifierInput]] = None
    contact: Optional[List[PlanDefinitionContactInput]] = None
    author: Optional[List[PlanDefinitionContactInput]] = None
    editor: Optional[List[PlanDefinitionContactInput]] = None
    reviewer: Optional[List[PlanDefinitionContactInput]] = None
    endorser: Optional[List[PlanDefinitionContactInput]] = None
    use_context: Optional[List[PlanDefinitionUseContextInput]] = None
    jurisdiction: Optional[List[PlanDefinitionCodeableConceptInput]] = None
    topic: Optional[List[PlanDefinitionCodeableConceptInput]] = None
    related_artifact: Optional[List[PlanDefinitionRelatedArtifactInput]] = None
    library: Optional[List[str]] = None
    goal: Optional[List[PlanDefinitionGoalInput]] = None
    action: Optional[List[PlanDefinitionActionInput]] = None

    @field_validator("status")
    @classmethod
    def _status_not_null(cls, v):
        if v is None:
            raise ValueError("must not be null")
        return v

    @model_validator(mode="after")
    def _validate(self):
        if self.effective_period_start and self.effective_period_end and _utc(self.effective_period_end) < _utc(self.effective_period_start):
            raise ValueError("effective_period_end must not be before effective_period_start.")
        # goal_id references are checked against stored goals in the repository when `goal` is not sent.
        validate_plan_tree(self.goal, self.action, check_goal_ids="goal" in self.model_fields_set)
        return self


# ── Search ─────────────────────────────────────────────────────────────────────


class ListPlanDefinitionsSchema(BaseModel):
    """
    Search parameters for GET /plan-definitions — the FHIR R4 PlanDefinition search params plus `_id`
    and `_lastUpdated`.

    The router builds this from explicitly declared Query parameters (`_id`, `_lastUpdated` and the
    hyphenated / `:modifier` names are not valid Python identifiers); the service then forwards it to the
    fhir-server under the FHIR parameter names.

    Token params: `code` | `system|code` | `|code` | `system|`; comma = OR.
    String params (name/title/publisher/description): prefix match by default, `*_contains` / `*_exact` variants.
    Date params (`date`, `effective`, `last_updated`): optional prefix eq|ne|gt|lt|ge|le|sa|eb|ap; repeat for AND.
    """

    model_config = ConfigDict(extra="forbid")

    id: Optional[str] = Field(None, description="_id — public plan_definition_id(s), comma-separated.")
    identifier: Optional[str] = Field(None, description="Token `[system|]value` of PlanDefinition.identifier.")
    url: Optional[str] = Field(None, description="Canonical URL(s), comma = OR.")
    version: Optional[str] = Field(None, description="Business version(s), comma = OR.")
    name: Optional[str] = Field(None, description="Name — prefix match.")
    name_contains: Optional[str] = Field(None, description="name:contains — substring.")
    name_exact: Optional[str] = Field(None, description="name:exact — case-sensitive full match.")
    title: Optional[str] = Field(None, description="Title — prefix match.")
    title_contains: Optional[str] = Field(None, description="title:contains — substring.")
    title_exact: Optional[str] = Field(None, description="title:exact — case-sensitive full match.")
    publisher: Optional[str] = Field(None, description="Publisher — prefix match.")
    publisher_contains: Optional[str] = Field(None, description="publisher:contains — substring.")
    publisher_exact: Optional[str] = Field(None, description="publisher:exact — case-sensitive full match.")
    description: Optional[str] = Field(None, description="Description — prefix match.")
    description_contains: Optional[str] = Field(None, description="description:contains — substring.")
    description_exact: Optional[str] = Field(None, description="description:exact — case-sensitive full match.")
    status: Optional[str] = Field(None, description="Token: draft|active|retired|unknown (comma = OR).")
    type: Optional[str] = Field(None, description="Token `[system|]code` of PlanDefinition.type.")
    topic: Optional[str] = Field(None, description="Token `[system|]code` of PlanDefinition.topic.")
    jurisdiction: Optional[str] = Field(None, description="Token `[system|]code` of PlanDefinition.jurisdiction.")
    context: Optional[str] = Field(None, description="Token of useContext.valueCodeableConcept.")
    context_type: Optional[str] = Field(None, description="context-type — token of useContext.code.")
    definition: Optional[str] = Field(None, description="Action definition canonical, e.g. 'ActivityDefinition/1' or a full URL.")
    depends_on: Optional[str] = Field(None, description="depends-on — resource the plan depends on (relatedArtifact / library).")
    derived_from: Optional[str] = Field(None, description="derived-from — resource the plan is derived from.")
    predecessor: Optional[str] = Field(None, description="Predecessor resource.")
    successor: Optional[str] = Field(None, description="Successor resource.")
    composed_of: Optional[str] = Field(None, description="composed-of — resource the plan is composed of.")
    date: Optional[List[str]] = Field(None, description="Publication date with optional prefix e.g. 'ge2024-01-01'.")
    effective: Optional[List[str]] = Field(None, description="Effective period with optional prefix.")
    last_updated: Optional[List[str]] = Field(None, description="_lastUpdated instant with optional prefix.")
    # Tenant-scoping filters — org_id is mandatory, user_id optional.
    user_id: Optional[str] = Field(None, description="Optional: restrict to records owned by this user (JWT subject).")
    org_id: str = Field(..., min_length=1, description="Tenant organization ID — mandatory scope of every search.")
    limit: int = Field(50, ge=1, le=200, description="Max records per page.")
    offset: int = Field(0, ge=0, description="Records to skip.")

    @field_validator("status")
    @classmethod
    def _validate_status_tokens(cls, v: Optional[str]) -> Optional[str]:
        """Reject unknown status codes early (comma-separated OR list allowed) with a gateway 422."""
        if v is None:
            return v
        allowed = {s.value for s in PlanDefinitionStatus}
        bad = [t for t in v.split(",") if t.strip() and t.strip() not in allowed]
        if bad:
            raise ValueError(f"Invalid status {bad}. Allowed: {sorted(allowed)}")
        return v
