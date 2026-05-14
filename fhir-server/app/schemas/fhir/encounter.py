from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.fhir.common import (
    FHIRBundle,
    FHIRCoding,
    FHIRCodeableConcept,
    FHIRReference,
    FHIRPeriod,
    PlainReasonCode,
)


class FHIREncounterClass(BaseModel):
    code: Optional[str] = Field(None, description="ambulatory | inpatient | emergency | virtual | etc.")


class FHIREncounterTypeEntry(BaseModel):
    coding: Optional[List[FHIRCoding]] = None
    text: Optional[str] = None


class FHIREncounterParticipantType(BaseModel):
    text: Optional[str] = None


class FHIREncounterParticipant(BaseModel):
    type: Optional[List[FHIREncounterParticipantType]] = None
    individual: Optional[FHIRReference] = None
    period: Optional[FHIRPeriod] = None


class FHIREncounterReasonCode(BaseModel):
    coding: Optional[List[FHIRCoding]] = None
    text: Optional[str] = None


class FHIREncounterDiagnosisCondition(BaseModel):
    reference: Optional[str] = None


class FHIREncounterDiagnosis(BaseModel):
    condition: Optional[FHIREncounterDiagnosisCondition] = None
    use: Optional[Dict[str, str]] = None
    rank: Optional[int] = None


class FHIREncounterLocationRef(BaseModel):
    reference: Optional[str] = None


class FHIREncounterLocation(BaseModel):
    location: Optional[FHIREncounterLocationRef] = None
    status: Optional[str] = None
    period: Optional[FHIRPeriod] = None


class FHIREncounterSchema(BaseModel):
    resourceType: str = Field("Encounter", description="Always 'Encounter'.")
    id: str = Field(..., description="Public encounter_id as a string.")
    status: str = Field(..., description="planned | in-progress | finished | cancelled | etc.")
    model_config = {"populate_by_name": True}

    # FHIR uses 'class' which is a Python keyword — alias used in output
    class_: Optional[FHIREncounterClass] = Field(None, alias="class")
    subject: Optional[FHIRReference] = None
    period: Optional[FHIRPeriod] = None
    priority: Optional[Dict[str, str]] = None
    basedOn: Optional[List[FHIRReference]] = None
    type: Optional[List[FHIREncounterTypeEntry]] = None
    participant: Optional[List[FHIREncounterParticipant]] = None
    reasonCode: Optional[List[FHIREncounterReasonCode]] = None
    diagnosis: Optional[List[FHIREncounterDiagnosis]] = None
    location: Optional[List[FHIREncounterLocation]] = None


class FHIREncounterBundleEntry(BaseModel):
    resource: FHIREncounterSchema


class FHIREncounterBundle(FHIRBundle):
    entry: Optional[List[FHIREncounterBundleEntry]] = None


# ── Plain (snake_case) sub-types ──────────────────────────────────────────────


class PlainEncounterBasedOn(BaseModel):
    reference_type: Optional[str] = Field(None, description="e.g. 'ServiceRequest'")
    reference_id: Optional[int] = None
    reference_display: Optional[str] = None


class PlainEncounterType(BaseModel):
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class PlainEncounterParticipant(BaseModel):
    type_text: Optional[str] = None
    reference_type: Optional[str] = Field(None, description="e.g. 'Practitioner'")
    individual_reference: Optional[int] = None
    period_start: Optional[str] = Field(None, description="ISO 8601 datetime string.")
    period_end: Optional[str] = Field(None, description="ISO 8601 datetime string.")


class PlainEncounterDiagnosis(BaseModel):
    condition_reference: Optional[str] = None
    use_text: Optional[str] = None
    rank: Optional[int] = None


class PlainEncounterLocation(BaseModel):
    location_reference: Optional[str] = None
    status: Optional[str] = Field(None, description="planned | active | reserved | completed")
    period_start: Optional[str] = Field(None, description="ISO 8601 datetime string.")
    period_end: Optional[str] = Field(None, description="ISO 8601 datetime string.")


# ── Plain Encounter response ──────────────────────────────────────────────────


class PlainEncounterResponse(BaseModel):
    id: int = Field(..., description="Public encounter_id.")
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    status: Optional[str] = Field(None, description="planned | in-progress | finished | cancelled | etc.")
    class_code: Optional[str] = Field(None, description="ambulatory | inpatient | emergency | virtual | etc.")
    priority: Optional[str] = None
    subject_type: Optional[str] = Field(None, description="e.g. 'Patient'")
    subject_id: Optional[int] = None
    subject_display: Optional[str] = None
    period_start: Optional[str] = Field(None, description="ISO 8601 datetime string.")
    period_end: Optional[str] = Field(None, description="ISO 8601 datetime string.")
    based_on: Optional[List[PlainEncounterBasedOn]] = None
    type: Optional[List[PlainEncounterType]] = None
    participant: Optional[List[PlainEncounterParticipant]] = None
    reason_code: Optional[List[PlainReasonCode]] = None
    diagnosis: Optional[List[PlainEncounterDiagnosis]] = None
    location: Optional[List[PlainEncounterLocation]] = None


# ── Paginated response ────────────────────────────────────────────────────────


class PaginatedEncounterResponse(BaseModel):
    total: int = Field(..., description="Total number of matching encounters.")
    limit: int = Field(..., description="Page size requested.")
    offset: int = Field(..., description="Number of records skipped.")
    data: List[PlainEncounterResponse] = Field(..., description="Array of plain-JSON Encounter objects.")
