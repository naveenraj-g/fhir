from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common.fhir import FHIRBundle


# ── FHIR (camelCase) response schemas ─────────────────────────────────────────
# The FHIR representation is deeply nested and choice-typed; sub-elements are documented as objects.


class FHIRPlanDefinitionAction(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: Optional[str] = None
    prefix: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    textEquivalent: Optional[str] = None
    priority: Optional[str] = None
    code: Optional[List[Dict[str, Any]]] = None
    reason: Optional[List[Dict[str, Any]]] = None
    documentation: Optional[List[Dict[str, Any]]] = None
    goalId: Optional[List[str]] = None
    subjectCodeableConcept: Optional[Dict[str, Any]] = None
    subjectReference: Optional[Dict[str, Any]] = None
    trigger: Optional[List[Dict[str, Any]]] = None
    condition: Optional[List[Dict[str, Any]]] = None
    input: Optional[List[Dict[str, Any]]] = None
    output: Optional[List[Dict[str, Any]]] = None
    relatedAction: Optional[List[Dict[str, Any]]] = None
    timingDateTime: Optional[str] = None
    timingAge: Optional[Dict[str, Any]] = None
    timingPeriod: Optional[Dict[str, Any]] = None
    timingDuration: Optional[Dict[str, Any]] = None
    timingRange: Optional[Dict[str, Any]] = None
    timingTiming: Optional[Dict[str, Any]] = None
    participant: Optional[List[Dict[str, Any]]] = None
    type: Optional[Dict[str, Any]] = None
    groupingBehavior: Optional[str] = None
    selectionBehavior: Optional[str] = None
    requiredBehavior: Optional[str] = None
    precheckBehavior: Optional[str] = None
    cardinalityBehavior: Optional[str] = None
    definitionCanonical: Optional[str] = None
    definitionUri: Optional[str] = None
    transform: Optional[str] = None
    dynamicValue: Optional[List[Dict[str, Any]]] = None
    action: Optional[List[Dict[str, Any]]] = Field(None, description="Nested actions (same shape, recursive).")


class FHIRPlanDefinitionSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    resourceType: str = Field("PlanDefinition", description="Always 'PlanDefinition'.")
    id: str = Field(..., description="Public plan_definition_id as a string.")
    url: Optional[str] = None
    identifier: Optional[List[Dict[str, Any]]] = None
    version: Optional[str] = None
    name: Optional[str] = None
    title: Optional[str] = None
    subtitle: Optional[str] = None
    type: Optional[Dict[str, Any]] = None
    status: str
    experimental: Optional[bool] = None
    subjectCodeableConcept: Optional[Dict[str, Any]] = None
    subjectReference: Optional[Dict[str, Any]] = None
    date: Optional[str] = None
    publisher: Optional[str] = None
    contact: Optional[List[Dict[str, Any]]] = None
    description: Optional[str] = None
    useContext: Optional[List[Dict[str, Any]]] = None
    jurisdiction: Optional[List[Dict[str, Any]]] = None
    purpose: Optional[str] = None
    usage: Optional[str] = None
    copyright: Optional[str] = None
    approvalDate: Optional[str] = None
    lastReviewDate: Optional[str] = None
    effectivePeriod: Optional[Dict[str, Any]] = None
    topic: Optional[List[Dict[str, Any]]] = None
    author: Optional[List[Dict[str, Any]]] = None
    editor: Optional[List[Dict[str, Any]]] = None
    reviewer: Optional[List[Dict[str, Any]]] = None
    endorser: Optional[List[Dict[str, Any]]] = None
    relatedArtifact: Optional[List[Dict[str, Any]]] = None
    library: Optional[List[str]] = None
    goal: Optional[List[Dict[str, Any]]] = None
    action: Optional[List[FHIRPlanDefinitionAction]] = None


class FHIRPlanDefinitionBundleEntry(BaseModel):
    resource: FHIRPlanDefinitionSchema


class FHIRPlanDefinitionBundle(FHIRBundle):
    entry: Optional[List[FHIRPlanDefinitionBundleEntry]] = None


# ── Plain (snake_case) response schemas ───────────────────────────────────────


class PlainPlanDefinitionCodeableConcept(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class PlainPlanDefinitionAction(BaseModel):
    """One action; sub-actions are returned (recursively) in `action`."""

    model_config = ConfigDict(extra="allow")

    id: int
    element_id: Optional[str] = None
    prefix: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    text_equivalent: Optional[str] = None
    priority: Optional[str] = None
    code: Optional[List[PlainPlanDefinitionCodeableConcept]] = None
    reason: Optional[List[PlainPlanDefinitionCodeableConcept]] = None
    documentation: Optional[List[Dict[str, Any]]] = None
    goal_id: Optional[List[str]] = None
    subject_cc_system: Optional[str] = None
    subject_cc_code: Optional[str] = None
    subject_cc_display: Optional[str] = None
    subject_cc_text: Optional[str] = None
    subject_reference_type: Optional[str] = None
    subject_reference_id: Optional[int] = None
    subject_reference_display: Optional[str] = None
    trigger: Optional[List[Dict[str, Any]]] = None
    condition: Optional[List[Dict[str, Any]]] = None
    input: Optional[List[Dict[str, Any]]] = None
    output: Optional[List[Dict[str, Any]]] = None
    related_action: Optional[List[Dict[str, Any]]] = None
    timing_datetime: Optional[str] = None
    timing_age: Optional[Dict[str, Any]] = None
    timing_period: Optional[Dict[str, Any]] = None
    timing_duration: Optional[Dict[str, Any]] = None
    timing_range: Optional[Dict[str, Any]] = None
    timing_timing: Optional[Dict[str, Any]] = None
    participant: Optional[List[Dict[str, Any]]] = None
    type_system: Optional[str] = None
    type_code: Optional[str] = None
    type_display: Optional[str] = None
    type_text: Optional[str] = None
    grouping_behavior: Optional[str] = None
    selection_behavior: Optional[str] = None
    required_behavior: Optional[str] = None
    precheck_behavior: Optional[str] = None
    cardinality_behavior: Optional[str] = None
    definition_canonical: Optional[str] = None
    definition_uri: Optional[str] = None
    transform: Optional[str] = None
    dynamic_value: Optional[List[Dict[str, Any]]] = None
    action: Optional[List[Dict[str, Any]]] = Field(None, description="Nested actions (same shape, recursive).")


class PlainPlanDefinitionGoal(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    element_id: Optional[str] = None
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
    addresses: Optional[List[PlainPlanDefinitionCodeableConcept]] = None
    documentation: Optional[List[Dict[str, Any]]] = None
    target: Optional[List[Dict[str, Any]]] = None


class PlainPlanDefinitionResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    url: Optional[str] = None
    version: Optional[str] = None
    name: Optional[str] = None
    title: Optional[str] = None
    subtitle: Optional[str] = None
    status: Optional[str] = None
    experimental: Optional[bool] = None
    date: Optional[str] = None
    publisher: Optional[str] = None
    description: Optional[str] = None
    purpose: Optional[str] = None
    usage: Optional[str] = None
    copyright: Optional[str] = None
    approval_date: Optional[str] = None
    last_review_date: Optional[str] = None
    effective_period_start: Optional[str] = None
    effective_period_end: Optional[str] = None
    type_system: Optional[str] = None
    type_code: Optional[str] = None
    type_display: Optional[str] = None
    type_text: Optional[str] = None
    subject_cc_system: Optional[str] = None
    subject_cc_code: Optional[str] = None
    subject_cc_display: Optional[str] = None
    subject_cc_text: Optional[str] = None
    subject_reference_type: Optional[str] = None
    subject_reference_id: Optional[int] = None
    subject_reference_display: Optional[str] = None
    identifier: Optional[List[Dict[str, Any]]] = None
    contact: Optional[List[Dict[str, Any]]] = None
    author: Optional[List[Dict[str, Any]]] = None
    editor: Optional[List[Dict[str, Any]]] = None
    reviewer: Optional[List[Dict[str, Any]]] = None
    endorser: Optional[List[Dict[str, Any]]] = None
    use_context: Optional[List[Dict[str, Any]]] = None
    jurisdiction: Optional[List[PlainPlanDefinitionCodeableConcept]] = None
    topic: Optional[List[PlainPlanDefinitionCodeableConcept]] = None
    related_artifact: Optional[List[Dict[str, Any]]] = None
    library: Optional[List[Dict[str, Any]]] = None
    goal: Optional[List[PlainPlanDefinitionGoal]] = None
    action: Optional[List[PlainPlanDefinitionAction]] = None
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None


class PaginatedPlanDefinitionResponse(BaseModel):
    total: int
    limit: int
    offset: int
    data: List[PlainPlanDefinitionResponse]
