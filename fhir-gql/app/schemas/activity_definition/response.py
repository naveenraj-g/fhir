"""
Response schemas for ActivityDefinition resources (fhir-gql gateway).

Plain* classes mirror the fhir-server snake_case output (`application/json`);
FHIR* classes document the `application/fhir+json` shape for Swagger only.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field



# ── FHIR (camelCase) response schemas ─────────────────────────────────────────
# The FHIR representation is deeply nested and choice-typed; sub-elements are documented as objects.


class FHIRActivityDefinitionSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    resourceType: str = Field("ActivityDefinition", description="Always 'ActivityDefinition'.")
    id: str = Field(..., description="Public activity_definition_id as a string.")
    url: Optional[str] = None
    identifier: Optional[List[Dict[str, Any]]] = None
    version: Optional[str] = None
    name: Optional[str] = None
    title: Optional[str] = None
    subtitle: Optional[str] = None
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
    kind: Optional[str] = None
    profile: Optional[str] = None
    code: Optional[Dict[str, Any]] = None
    intent: Optional[str] = None
    priority: Optional[str] = None
    doNotPerform: Optional[bool] = None
    timingTiming: Optional[Dict[str, Any]] = None
    timingDateTime: Optional[str] = None
    timingAge: Optional[Dict[str, Any]] = None
    timingPeriod: Optional[Dict[str, Any]] = None
    timingRange: Optional[Dict[str, Any]] = None
    timingDuration: Optional[Dict[str, Any]] = None
    location: Optional[Dict[str, Any]] = None
    participant: Optional[List[Dict[str, Any]]] = None
    productReference: Optional[Dict[str, Any]] = None
    productCodeableConcept: Optional[Dict[str, Any]] = None
    quantity: Optional[Dict[str, Any]] = None
    dosage: Optional[List[Dict[str, Any]]] = None
    bodySite: Optional[List[Dict[str, Any]]] = None
    specimenRequirement: Optional[List[Dict[str, Any]]] = None
    observationRequirement: Optional[List[Dict[str, Any]]] = None
    observationResultRequirement: Optional[List[Dict[str, Any]]] = None
    transform: Optional[str] = None
    dynamicValue: Optional[List[Dict[str, Any]]] = None


class FHIRActivityDefinitionBundleEntry(BaseModel):
    resource: FHIRActivityDefinitionSchema


class FHIRActivityDefinitionBundle(BaseModel):
    """FHIR R4 Bundle (searchset) for the ActivityDefinition list endpoint."""

    resourceType: str = "Bundle"
    type: str = "searchset"
    total: Optional[int] = None
    entry: Optional[List[FHIRActivityDefinitionBundleEntry]] = None


# ── Plain (snake_case) response schemas ───────────────────────────────────────


class PlainActivityDefinitionCodeableConcept(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class PlainActivityDefinitionReference(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    reference_display: Optional[str] = None


class PlainActivityDefinitionResponse(BaseModel):
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
    subject_cc_system: Optional[str] = None
    subject_cc_code: Optional[str] = None
    subject_cc_display: Optional[str] = None
    subject_cc_text: Optional[str] = None
    subject_reference_type: Optional[str] = None
    subject_reference_id: Optional[int] = None
    subject_reference_display: Optional[str] = None
    kind: Optional[str] = None
    profile: Optional[str] = None
    code_system: Optional[str] = None
    code_code: Optional[str] = None
    code_display: Optional[str] = None
    code_text: Optional[str] = None
    intent: Optional[str] = None
    priority: Optional[str] = None
    do_not_perform: Optional[bool] = None
    timing_datetime: Optional[str] = None
    timing_age: Optional[Dict[str, Any]] = None
    timing_period: Optional[Dict[str, Any]] = None
    timing_range: Optional[Dict[str, Any]] = None
    timing_duration: Optional[Dict[str, Any]] = None
    timing_timing: Optional[Dict[str, Any]] = None
    location_type: Optional[str] = None
    location_id: Optional[int] = None
    location_display: Optional[str] = None
    product_reference_type: Optional[str] = None
    product_reference_id: Optional[int] = None
    product_reference_display: Optional[str] = None
    product_cc_system: Optional[str] = None
    product_cc_code: Optional[str] = None
    product_cc_display: Optional[str] = None
    product_cc_text: Optional[str] = None
    quantity: Optional[Dict[str, Any]] = None
    transform: Optional[str] = None
    identifier: Optional[List[Dict[str, Any]]] = None
    contact: Optional[List[Dict[str, Any]]] = None
    author: Optional[List[Dict[str, Any]]] = None
    editor: Optional[List[Dict[str, Any]]] = None
    reviewer: Optional[List[Dict[str, Any]]] = None
    endorser: Optional[List[Dict[str, Any]]] = None
    use_context: Optional[List[Dict[str, Any]]] = None
    jurisdiction: Optional[List[PlainActivityDefinitionCodeableConcept]] = None
    topic: Optional[List[PlainActivityDefinitionCodeableConcept]] = None
    related_artifact: Optional[List[Dict[str, Any]]] = None
    library: Optional[List[Dict[str, Any]]] = None
    participant: Optional[List[Dict[str, Any]]] = None
    dosage: Optional[List[Dict[str, Any]]] = None
    body_site: Optional[List[PlainActivityDefinitionCodeableConcept]] = None
    specimen_requirement: Optional[List[PlainActivityDefinitionReference]] = None
    observation_requirement: Optional[List[PlainActivityDefinitionReference]] = None
    observation_result_requirement: Optional[List[PlainActivityDefinitionReference]] = None
    dynamic_value: Optional[List[Dict[str, Any]]] = None
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None


class PaginatedActivityDefinitionResponse(BaseModel):
    total: int
    limit: int
    offset: int
    data: List[PlainActivityDefinitionResponse]
