from enum import Enum


class EncounterStatus(str, Enum):
    """FHIR R4 Encounter status value set."""

    planned = "planned"
    arrived = "arrived"
    triaged = "triaged"
    in_progress = "in-progress"
    onleave = "onleave"
    finished = "finished"
    cancelled = "cancelled"
    entered_in_error = "entered-in-error"
    unknown = "unknown"


class EncounterLocationStatus(str, Enum):
    """FHIR Encounter location status value set."""

    planned = "planned"
    active = "active"
    reserved = "reserved"
    completed = "completed"


class EncounterParticipantReferenceType(str, Enum):
    """FHIR reference types for Encounter.participant.individual."""

    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    RELATED_PERSON = "RelatedPerson"


class EncounterBasedOnReferenceType(str, Enum):
    """FHIR reference types for Encounter.basedOn (R4: ServiceRequest only)."""

    SERVICE_REQUEST = "ServiceRequest"


class EncounterDiagnosisConditionType(str, Enum):
    """FHIR reference types for Encounter.diagnosis.condition."""

    CONDITION = "Condition"
    PROCEDURE = "Procedure"
