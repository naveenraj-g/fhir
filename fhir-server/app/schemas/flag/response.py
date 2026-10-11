from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common.fhir import FHIRBundle, FHIRCodeableConcept, FHIRReference


# ── FHIR (camelCase) response schemas ─────────────────────────────────────────


class FHIRFlagSchema(BaseModel):
    resourceType: str = Field("Flag", description="Always 'Flag'.")
    id: str = Field(..., description="Public flag_id as a string.")
    identifier: Optional[List[Dict[str, Any]]] = None
    status: str
    category: Optional[List[FHIRCodeableConcept]] = None
    code: Optional[FHIRCodeableConcept] = None
    subject: Optional[FHIRReference] = None
    period: Optional[Dict[str, Any]] = None
    encounter: Optional[FHIRReference] = None
    author: Optional[FHIRReference] = None


class FHIRFlagBundleEntry(BaseModel):
    resource: FHIRFlagSchema


class FHIRFlagBundle(FHIRBundle):
    entry: Optional[List[FHIRFlagBundleEntry]] = None


# ── Plain (snake_case) response schemas ───────────────────────────────────────


class PlainFlagIdentifier(BaseModel):
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


class PlainFlagCategory(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class PlainFlagResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    status: Optional[str] = None
    code_system: Optional[str] = None
    code_code: Optional[str] = None
    code_display: Optional[str] = None
    code_text: Optional[str] = None
    subject_type: Optional[str] = None
    subject_id: Optional[int] = None
    subject_display: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    encounter_type: Optional[str] = None
    encounter_id: Optional[int] = None
    encounter_display: Optional[str] = None
    author_type: Optional[str] = None
    author_id: Optional[int] = None
    author_display: Optional[str] = None
    identifier: Optional[List[PlainFlagIdentifier]] = None
    category: Optional[List[PlainFlagCategory]] = None
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None


class PaginatedFlagResponse(BaseModel):
    total: int
    limit: int
    offset: int
    data: List[PlainFlagResponse]
