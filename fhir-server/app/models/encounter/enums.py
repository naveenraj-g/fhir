from enum import Enum


class EncounterClass(str, Enum):
    """FHIR Encounter class value set."""

    INPATIENT = "inpatient"
    AMBULATORY = "ambulatory"
    OBSERVATION = "observation"
    EMERGENCY = "emergency"
    VIRTUAL = "virtual"
    HOME_HEALTH = "home_health"


class EncounterParticipantReferenceType(str, Enum):
    """FHIR individual reference types for Encounter.participant.individual."""

    PATIENT = "Patient"
    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    RELATED_PERSON = "RelatedPerson"


class EncounterStatus(str, Enum):
    """FHIR Encounter status value set."""

    PLANNED = "planned"
    IN_PROGRESS = "in-progress"
    ON_HOLD = "on-hold"
    DISCHARGED = "discharged"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DISCONTINUED = "discontinued"
    ENTERED_IN_ERROR = "entered-in-error"
    UNKNOWN = "unknown"


class EncounterPriority(str, Enum):
    """FHIR Encounter priority value set."""

    ROUTINE = "routine"
    URGENT = "urgent"
    STAT = "stat"
    ASAP = "asap"


class EncounterType(str, Enum):
    """FHIR Encounter type value set."""

    INPATIENT = "inpatient"
    OUTPATIENT = "outpatient"
    EMERGENCY = "emergency"
    WALK_IN = "walk-in"
    OTHER = "other"


class EncounterParticipantType(str, Enum):
    """FHIR Encounter participant type value set."""

    PATIENT = "patient"
    PRACTITIONER = "practitioner"
    PRACTITIONER_ROLE = "practitioner_role"
    RELATED_PERSON = "related_person"


class EncounterDiagnosisUse(str, Enum):
    """FHIR Encounter diagnosis use value set."""

    ADMISSION = "admission"
    DISCHARGE = "discharge"
    BILLING = "billing"
    OTHER = "other"


class EncounterLocationStatus(str, Enum):
    """FHIR Encounter location status value set."""

    PLANNED = "planned"
    ACTIVE = "active"
    RESERVED = "reserved"
    COMPLETED = "completed"


class EncounterReasonCode(str, Enum):
    """FHIR Encounter reason code value set."""

    INPATIENT = "inpatient"
    OUTPATIENT = "outpatient"
    EMERGENCY = "emergency"
    WALK_IN = "walk-in"
    OTHER = "other"


class EncounterBasedOnReferenceType(str, Enum):
    """FHIR reference types for Encounter.basedOn."""

    CARE_PLAN = "CarePlan"
    DEVICE_REQUEST = "DeviceRequest"
    MEDICATION_REQUEST = "MedicationRequest"
    SERVICE_REQUEST = "ServiceRequest"
