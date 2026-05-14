from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ── Sub-resource input schemas ─────────────────────────────────────────────────


class EncounterIdentifierInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    use: Optional[str] = Field(None, description="usual|official|temp|secondary|old")
    type_system: Optional[str] = Field(None, description="Coding system for identifier type.")
    type_code: Optional[str] = Field(None, description="Code for identifier type.")
    type_display: Optional[str] = Field(None, description="Display for identifier type.")
    type_text: Optional[str] = Field(None, description="Plain-text description of identifier type.")
    system: Optional[str] = Field(None, description="URI of the identifier namespace.")
    value: str = Field(..., description="Identifier value.")
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    assigner: Optional[str] = Field(None, description="Display name of assigning organization.")


class EncounterStatusHistoryInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: str = Field(..., description="planned|arrived|triaged|in-progress|onleave|finished|cancelled|entered-in-error|unknown")
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class EncounterClassHistoryInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    class_system: Optional[str] = Field(None, description="Coding system URI, e.g. 'http://terminology.hl7.org/CodeSystem/v3-ActCode'.")
    class_version: Optional[str] = None
    class_code: str = Field(..., description="Class code, e.g. 'AMB', 'IMP', 'EMER'.")
    class_display: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class EncounterTypeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    coding_system: Optional[str] = Field(None, description="Terminology system URI, e.g. 'http://snomed.info/sct'.")
    coding_code: Optional[str] = Field(None, description="Code value.")
    coding_display: Optional[str] = Field(None, description="Human-readable code label.")
    text: Optional[str] = Field(None, description="Plain-text description of the encounter type.")


class EncounterEpisodeOfCareInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    episode_of_care_id: int = Field(..., description="Public EpisodeOfCare ID.")
    display: Optional[str] = None


class EncounterBasedOnInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: str = Field(
        ...,
        description="FHIR reference, e.g. 'ServiceRequest/80001'.",
        examples=["ServiceRequest/80001"],
    )
    display: Optional[str] = Field(None, description="Human-readable label for the referenced resource.")


class EncounterParticipantTypeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class EncounterParticipantInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Optional[List[EncounterParticipantTypeInput]] = Field(
        None, description="Participant role CodeableConcept(s), e.g. [{coding_code: 'PART'}]."
    )
    individual: Optional[str] = Field(
        None,
        description="FHIR reference using the public resource ID, e.g. 'Practitioner/30001'.",
        examples=["Practitioner/30001"],
    )
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class EncounterAppointmentRefInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    appointment_id: int = Field(..., description="Public Appointment ID.")
    display: Optional[str] = None


class EncounterReasonCodeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class EncounterReasonReferenceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: str = Field(
        ...,
        description="FHIR reference, e.g. 'Condition/12345' or 'Observation/99999'.",
        examples=["Condition/12345"],
    )
    display: Optional[str] = None


class EncounterDiagnosisInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    condition: str = Field(
        ...,
        description="Reference to the Condition or Procedure, e.g. 'Condition/12345' or 'Procedure/67890'.",
        examples=["Condition/12345"],
    )
    condition_display: Optional[str] = None
    use_system: Optional[str] = None
    use_code: Optional[str] = Field(None, description="CodeableConcept code for diagnosis role, e.g. 'AD' for admission.")
    use_display: Optional[str] = None
    use_text: Optional[str] = None
    rank: Optional[int] = Field(None, ge=1, description="1 = primary diagnosis.")


class EncounterAccountInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    account_id: int = Field(..., description="Public Account ID.")
    display: Optional[str] = None


class EncounterHospCodeableConceptInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class EncounterHospitalizationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    pre_admission_identifier_system: Optional[str] = None
    pre_admission_identifier_value: Optional[str] = None
    origin: Optional[str] = Field(
        None,
        description="Reference to origin Location or Organization, e.g. 'Location/123'.",
        examples=["Location/123"],
    )
    origin_display: Optional[str] = None
    admit_source_system: Optional[str] = None
    admit_source_code: Optional[str] = Field(None, description="admitSource code, e.g. 'hosp-trans'.")
    admit_source_display: Optional[str] = None
    admit_source_text: Optional[str] = None
    re_admission_system: Optional[str] = None
    re_admission_code: Optional[str] = None
    re_admission_display: Optional[str] = None
    re_admission_text: Optional[str] = None
    diet_preference: Optional[List[EncounterHospCodeableConceptInput]] = None
    special_arrangement: Optional[List[EncounterHospCodeableConceptInput]] = None
    special_courtesy: Optional[List[EncounterHospCodeableConceptInput]] = None
    destination: Optional[str] = Field(
        None,
        description="Reference to destination Location or Organization, e.g. 'Location/456'.",
        examples=["Location/456"],
    )
    destination_display: Optional[str] = None
    discharge_disposition_system: Optional[str] = None
    discharge_disposition_code: Optional[str] = None
    discharge_disposition_display: Optional[str] = None
    discharge_disposition_text: Optional[str] = None


class EncounterLocationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    location: str = Field(
        ...,
        description="Reference to the Location, e.g. 'Location/501'.",
        examples=["Location/501"],
    )
    location_display: Optional[str] = None
    status: Optional[str] = Field(None, description="planned|active|reserved|completed")
    physical_type_system: Optional[str] = None
    physical_type_code: Optional[str] = None
    physical_type_display: Optional[str] = None
    physical_type_text: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


# ── Encounter create / patch ───────────────────────────────────────────────────


class EncounterCreateSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "user_id": "user-uuid-123",
                "org_id": "org-uuid-456",
                "status": "in-progress",
                "class_system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "class_code": "AMB",
                "class_display": "ambulatory",
                "subject": "Patient/10001",
                "period_start": "2026-04-01T09:00:00Z",
                "service_type_code": "11429006",
                "service_type_system": "http://snomed.info/sct",
                "service_type_display": "Consultation",
                "priority_code": "17621005",
                "priority_system": "http://snomed.info/sct",
                "priority_display": "Normal",
                "type": [
                    {
                        "coding_system": "http://snomed.info/sct",
                        "coding_code": "185349003",
                        "coding_display": "Encounter for check up",
                        "text": "Check up",
                    }
                ],
                "participant": [
                    {
                        "type": [{"coding_code": "PART", "text": "Participant"}],
                        "individual": "Practitioner/30001",
                        "period_start": "2026-04-01T09:00:00Z",
                    }
                ],
            }
        },
    )

    user_id: Optional[str] = None
    org_id: Optional[str] = None

    # status (1..1)
    status: str = Field(..., description="planned|arrived|triaged|in-progress|onleave|finished|cancelled|entered-in-error|unknown")

    # class (1..1 Coding)
    class_system: Optional[str] = Field(
        None,
        description="Coding system URI, e.g. 'http://terminology.hl7.org/CodeSystem/v3-ActCode'.",
    )
    class_version: Optional[str] = None
    class_code: Optional[str] = Field(None, description="Class code, e.g. 'AMB', 'IMP', 'EMER', 'VR'.")
    class_display: Optional[str] = None

    # serviceType (0..1 CodeableConcept)
    service_type_system: Optional[str] = None
    service_type_code: Optional[str] = None
    service_type_display: Optional[str] = None
    service_type_text: Optional[str] = None

    # priority (0..1 CodeableConcept)
    priority_system: Optional[str] = None
    priority_code: Optional[str] = None
    priority_display: Optional[str] = None
    priority_text: Optional[str] = None

    # subject (0..1)
    subject: Optional[str] = Field(
        None,
        description="Patient or Group reference, e.g. 'Patient/10001'.",
    )

    # period (0..1)
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None

    # length (0..1 Duration)
    length_value: Optional[float] = Field(None, description="Duration value (numeric).")
    length_comparator: Optional[str] = Field(None, description="<|<=|>=|>")
    length_unit: Optional[str] = Field(None, description="Human-readable unit, e.g. 'min'.")
    length_system: Optional[str] = Field(None, description="System for the duration code, e.g. 'http://unitsofmeasure.org'.")
    length_code: Optional[str] = Field(None, description="UCUM code, e.g. 'min'.")

    # serviceProvider (0..1 Reference(Organization))
    service_provider_id: Optional[int] = Field(None, description="Public Organization ID.")
    service_provider_display: Optional[str] = None

    # partOf (0..1 Reference(Encounter))
    part_of_id: Optional[int] = Field(None, description="Public encounter_id of the parent Encounter.")

    # Sub-resource arrays
    identifier: Optional[List[EncounterIdentifierInput]] = None
    status_history: Optional[List[EncounterStatusHistoryInput]] = None
    class_history: Optional[List[EncounterClassHistoryInput]] = None
    type: Optional[List[EncounterTypeInput]] = None
    episode_of_care: Optional[List[EncounterEpisodeOfCareInput]] = None
    based_on: Optional[List[EncounterBasedOnInput]] = None
    participant: Optional[List[EncounterParticipantInput]] = None
    appointment: Optional[List[EncounterAppointmentRefInput]] = None
    reason_code: Optional[List[EncounterReasonCodeInput]] = None
    reason_reference: Optional[List[EncounterReasonReferenceInput]] = None
    diagnosis: Optional[List[EncounterDiagnosisInput]] = None
    account: Optional[List[EncounterAccountInput]] = None
    hospitalization: Optional[EncounterHospitalizationInput] = None
    location: Optional[List[EncounterLocationInput]] = None


class EncounterPatchSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Optional[str] = Field(None, description="planned|arrived|triaged|in-progress|onleave|finished|cancelled|entered-in-error|unknown")
    period_end: Optional[datetime] = Field(None, description="Close the encounter by setting the period end time.")
    service_type_system: Optional[str] = None
    service_type_code: Optional[str] = None
    service_type_display: Optional[str] = None
    service_type_text: Optional[str] = None
    priority_system: Optional[str] = None
    priority_code: Optional[str] = None
    priority_display: Optional[str] = None
    priority_text: Optional[str] = None
