from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, Field

from app.schemas.common.fhir import (
    FHIRBundle,
    FHIRCoding,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRReference,
    FHIRPeriod,
)


# ── FHIR R4 sub-schemas ────────────────────────────────────────────────────────


class FHIREncounterStatusHistory(BaseModel):
    status: str
    period: Optional[FHIRPeriod] = None


class FHIREncounterClassHistory(BaseModel):
    class_: Optional[FHIRCoding] = Field(None, alias="class")
    period: Optional[FHIRPeriod] = None

    model_config = {"populate_by_name": True}


class FHIREncounterParticipant(BaseModel):
    type: Optional[List[FHIRCodeableConcept]] = None
    period: Optional[FHIRPeriod] = None
    individual: Optional[FHIRReference] = None


class FHIREncounterDiagnosis(BaseModel):
    condition: Optional[FHIRReference] = None
    use: Optional[FHIRCodeableConcept] = None
    rank: Optional[int] = None


class FHIREncounterHospitalization(BaseModel):
    preAdmissionIdentifier: Optional[FHIRIdentifier] = None
    origin: Optional[FHIRReference] = None
    admitSource: Optional[FHIRCodeableConcept] = None
    reAdmission: Optional[FHIRCodeableConcept] = None
    dietPreference: Optional[List[FHIRCodeableConcept]] = None
    specialArrangement: Optional[List[FHIRCodeableConcept]] = None
    specialCourtesy: Optional[List[FHIRCodeableConcept]] = None
    destination: Optional[FHIRReference] = None
    dischargeDisposition: Optional[FHIRCodeableConcept] = None


class FHIREncounterLocation(BaseModel):
    location: Optional[FHIRReference] = None
    status: Optional[str] = None
    physicalType: Optional[FHIRCodeableConcept] = None
    period: Optional[FHIRPeriod] = None


class FHIREncounterSchema(BaseModel):
    model_config = {"populate_by_name": True}

    resourceType: str = Field("Encounter", description="Always 'Encounter'.")
    id: str = Field(..., description="Public encounter_id as a string.")
    identifier: Optional[List[FHIRIdentifier]] = None
    status: str = Field(..., description="planned|arrived|triaged|in-progress|onleave|finished|cancelled|entered-in-error|unknown")
    statusHistory: Optional[List[FHIREncounterStatusHistory]] = None
    class_: Optional[FHIRCoding] = Field(None, alias="class")
    classHistory: Optional[List[FHIREncounterClassHistory]] = None
    type: Optional[List[FHIRCodeableConcept]] = None
    serviceType: Optional[FHIRCodeableConcept] = None
    priority: Optional[FHIRCodeableConcept] = None
    subject: Optional[FHIRReference] = None
    episodeOfCare: Optional[List[FHIRReference]] = None
    basedOn: Optional[List[FHIRReference]] = None
    participant: Optional[List[FHIREncounterParticipant]] = None
    appointment: Optional[List[FHIRReference]] = None
    period: Optional[FHIRPeriod] = None
    length: Optional[Any] = Field(None, description="Duration — value, comparator, unit, system, code.")
    reasonCode: Optional[List[FHIRCodeableConcept]] = None
    reasonReference: Optional[List[FHIRReference]] = None
    diagnosis: Optional[List[FHIREncounterDiagnosis]] = None
    account: Optional[List[FHIRReference]] = None
    hospitalization: Optional[FHIREncounterHospitalization] = None
    location: Optional[List[FHIREncounterLocation]] = None
    serviceProvider: Optional[FHIRReference] = None
    partOf: Optional[FHIRReference] = None


class FHIREncounterBundleEntry(BaseModel):
    resource: FHIREncounterSchema


class FHIREncounterBundle(FHIRBundle):
    entry: Optional[List[FHIREncounterBundleEntry]] = None


# ── Plain (snake_case) sub-schemas ────────────────────────────────────────────


class PlainEncounterIdentifier(BaseModel):
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


class PlainEncounterStatusHistory(BaseModel):
    status: str
    period_start: Optional[str] = None
    period_end: Optional[str] = None


class PlainEncounterClassHistory(BaseModel):
    class_system: Optional[str] = None
    class_version: Optional[str] = None
    class_code: Optional[str] = None
    class_display: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None


class PlainEncounterType(BaseModel):
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class PlainEncounterEpisodeOfCare(BaseModel):
    episode_of_care_id: Optional[int] = None
    display: Optional[str] = None


class PlainEncounterBasedOn(BaseModel):
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    reference_display: Optional[str] = None


class PlainEncounterParticipantType(BaseModel):
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class PlainEncounterParticipant(BaseModel):
    type: Optional[List[PlainEncounterParticipantType]] = None
    individual_type: Optional[str] = None
    individual_id: Optional[int] = None
    individual_display: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None


class PlainEncounterAppointmentRef(BaseModel):
    appointment_id: Optional[int] = None
    display: Optional[str] = None


class PlainEncounterReasonCode(BaseModel):
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class PlainEncounterReasonReference(BaseModel):
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    reference_display: Optional[str] = None


class PlainEncounterDiagnosis(BaseModel):
    condition_type: Optional[str] = None
    condition_id: Optional[int] = None
    condition_display: Optional[str] = None
    use_system: Optional[str] = None
    use_code: Optional[str] = None
    use_display: Optional[str] = None
    use_text: Optional[str] = None
    rank: Optional[int] = None


class PlainEncounterAccount(BaseModel):
    account_id: Optional[int] = None
    display: Optional[str] = None


class PlainEncounterHospCodeableConcept(BaseModel):
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class PlainEncounterHospitalization(BaseModel):
    pre_admission_identifier_system: Optional[str] = None
    pre_admission_identifier_value: Optional[str] = None
    origin_type: Optional[str] = None
    origin_id: Optional[int] = None
    origin_display: Optional[str] = None
    admit_source_system: Optional[str] = None
    admit_source_code: Optional[str] = None
    admit_source_display: Optional[str] = None
    admit_source_text: Optional[str] = None
    re_admission_system: Optional[str] = None
    re_admission_code: Optional[str] = None
    re_admission_display: Optional[str] = None
    re_admission_text: Optional[str] = None
    diet_preference: Optional[List[PlainEncounterHospCodeableConcept]] = None
    special_arrangement: Optional[List[PlainEncounterHospCodeableConcept]] = None
    special_courtesy: Optional[List[PlainEncounterHospCodeableConcept]] = None
    destination_type: Optional[str] = None
    destination_id: Optional[int] = None
    destination_display: Optional[str] = None
    discharge_disposition_system: Optional[str] = None
    discharge_disposition_code: Optional[str] = None
    discharge_disposition_display: Optional[str] = None
    discharge_disposition_text: Optional[str] = None


class PlainEncounterLocation(BaseModel):
    location_id: Optional[int] = None
    location_display: Optional[str] = None
    status: Optional[str] = None
    physical_type_system: Optional[str] = None
    physical_type_code: Optional[str] = None
    physical_type_display: Optional[str] = None
    physical_type_text: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None


class PlainEncounterLength(BaseModel):
    value: Optional[float] = None
    comparator: Optional[str] = None
    unit: Optional[str] = None
    system: Optional[str] = None
    code: Optional[str] = None


# ── Full plain Encounter response ─────────────────────────────────────────────


class PlainEncounterResponse(BaseModel):
    id: int = Field(..., description="Public encounter_id.")
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    status: Optional[str] = None
    class_system: Optional[str] = None
    class_version: Optional[str] = None
    class_code: Optional[str] = None
    class_display: Optional[str] = None
    service_type_system: Optional[str] = None
    service_type_code: Optional[str] = None
    service_type_display: Optional[str] = None
    service_type_text: Optional[str] = None
    priority_system: Optional[str] = None
    priority_code: Optional[str] = None
    priority_display: Optional[str] = None
    priority_text: Optional[str] = None
    subject_type: Optional[str] = None
    subject_id: Optional[int] = None
    subject_display: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    length: Optional[PlainEncounterLength] = None
    service_provider_id: Optional[int] = None
    service_provider_display: Optional[str] = None
    part_of_id: Optional[int] = None
    identifier: Optional[List[PlainEncounterIdentifier]] = None
    status_history: Optional[List[PlainEncounterStatusHistory]] = None
    class_history: Optional[List[PlainEncounterClassHistory]] = None
    type: Optional[List[PlainEncounterType]] = None
    episode_of_care: Optional[List[PlainEncounterEpisodeOfCare]] = None
    based_on: Optional[List[PlainEncounterBasedOn]] = None
    participant: Optional[List[PlainEncounterParticipant]] = None
    appointment: Optional[List[PlainEncounterAppointmentRef]] = None
    reason_code: Optional[List[PlainEncounterReasonCode]] = None
    reason_reference: Optional[List[PlainEncounterReasonReference]] = None
    diagnosis: Optional[List[PlainEncounterDiagnosis]] = None
    account: Optional[List[PlainEncounterAccount]] = None
    hospitalization: Optional[PlainEncounterHospitalization] = None
    location: Optional[List[PlainEncounterLocation]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None


# ── Paginated response ────────────────────────────────────────────────────────


class PaginatedEncounterResponse(BaseModel):
    total: int = Field(..., description="Total number of matching encounters.")
    limit: int = Field(..., description="Page size requested.")
    offset: int = Field(..., description="Number of records skipped.")
    data: List[PlainEncounterResponse] = Field(..., description="Array of plain-JSON Encounter objects.")
