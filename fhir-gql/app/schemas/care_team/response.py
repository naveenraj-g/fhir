"""
Response schemas for CareTeam resources (fhir-gql gateway).

Plain* classes mirror the fhir-server snake_case output (`application/json`);
FHIR* classes document the `application/fhir+json` shape for Swagger only.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field



class FHIRReference(BaseModel):
    """FHIR Reference datatype (reference + display)."""

    reference: Optional[str] = None
    display: Optional[str] = None


class FHIRCodeableConcept(BaseModel):
    """FHIR CodeableConcept datatype (coding[] + text)."""

    coding: Optional[List[Dict[str, Any]]] = None
    text: Optional[str] = None


class FHIRBundle(BaseModel):
    """FHIR R4 Bundle (searchset) envelope."""

    resourceType: str = "Bundle"
    type: str = "searchset"
    total: Optional[int] = None


# ── FHIR (camelCase) response schemas ─────────────────────────────────────────


class FHIRCareTeamParticipant(BaseModel):
    role: Optional[List[FHIRCodeableConcept]] = None
    member: Optional[FHIRReference] = None
    onBehalfOf: Optional[FHIRReference] = None
    period: Optional[Dict[str, Any]] = None


class FHIRCareTeamSchema(BaseModel):
    resourceType: str = Field("CareTeam", description="Always 'CareTeam'.")
    id: str = Field(..., description="Public care_team_id as a string.")
    identifier: Optional[List[Dict[str, Any]]] = None
    status: Optional[str] = None
    category: Optional[List[FHIRCodeableConcept]] = None
    name: Optional[str] = None
    subject: Optional[FHIRReference] = None
    encounter: Optional[FHIRReference] = None
    period: Optional[Dict[str, Any]] = None
    participant: Optional[List[FHIRCareTeamParticipant]] = None
    reasonCode: Optional[List[FHIRCodeableConcept]] = None
    reasonReference: Optional[List[FHIRReference]] = None
    managingOrganization: Optional[List[FHIRReference]] = None
    telecom: Optional[List[Dict[str, Any]]] = None
    note: Optional[List[Dict[str, Any]]] = None


class FHIRCareTeamBundleEntry(BaseModel):
    resource: FHIRCareTeamSchema


class FHIRCareTeamBundle(FHIRBundle):
    entry: Optional[List[FHIRCareTeamBundleEntry]] = None


# ── Plain (snake_case) response schemas ───────────────────────────────────────


class PlainCareTeamIdentifier(BaseModel):
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


class PlainCareTeamCodeableConcept(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class PlainCareTeamReference(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    reference_display: Optional[str] = None


class PlainCareTeamParticipant(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    role: Optional[List[PlainCareTeamCodeableConcept]] = None
    member_type: Optional[str] = None
    member_id: Optional[int] = None
    member_display: Optional[str] = None
    on_behalf_of_type: Optional[str] = None
    on_behalf_of_id: Optional[int] = None
    on_behalf_of_display: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None


class PlainCareTeamTelecom(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    system: Optional[str] = None
    value: Optional[str] = None
    use: Optional[str] = None
    rank: Optional[int] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None


class PlainCareTeamNote(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    text: str
    time: Optional[str] = None
    author_string: Optional[str] = None
    author_reference_type: Optional[str] = None
    author_reference_id: Optional[int] = None
    author_reference_display: Optional[str] = None


class PlainCareTeamResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    status: Optional[str] = None
    name: Optional[str] = None
    subject_type: Optional[str] = None
    subject_id: Optional[int] = None
    subject_display: Optional[str] = None
    encounter_type: Optional[str] = None
    encounter_id: Optional[int] = None
    encounter_display: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    identifier: Optional[List[PlainCareTeamIdentifier]] = None
    category: Optional[List[PlainCareTeamCodeableConcept]] = None
    participant: Optional[List[PlainCareTeamParticipant]] = None
    reason_code: Optional[List[PlainCareTeamCodeableConcept]] = None
    reason_reference: Optional[List[PlainCareTeamReference]] = None
    managing_organization: Optional[List[PlainCareTeamReference]] = None
    telecom: Optional[List[PlainCareTeamTelecom]] = None
    note: Optional[List[PlainCareTeamNote]] = None
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None


class PaginatedCareTeamResponse(BaseModel):
    total: int
    limit: int
    offset: int
    data: List[PlainCareTeamResponse]
