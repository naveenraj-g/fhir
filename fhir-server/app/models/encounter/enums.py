from enum import Enum


class EncounterStatus(str, Enum):
    """FHIR R5 Encounter status value set."""

    planned = "planned"
    in_progress = "in-progress"
    on_hold = "on-hold"
    discharged = "discharged"
    completed = "completed"
    cancelled = "cancelled"
    discontinued = "discontinued"
    entered_in_error = "entered-in-error"
    unknown = "unknown"


class EncounterLocationStatus(str, Enum):
    """FHIR Encounter location status value set."""

    planned = "planned"
    active = "active"
    reserved = "reserved"
    completed = "completed"


class EncounterParticipantReferenceType(str, Enum):
    """FHIR R5 reference types for Encounter.participant.actor."""

    PATIENT = "Patient"
    GROUP = "Group"
    RELATED_PERSON = "RelatedPerson"
    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    DEVICE = "Device"
    HEALTHCARE_SERVICE = "HealthcareService"


class EncounterBasedOnReferenceType(str, Enum):
    """FHIR R5 reference types for Encounter.basedOn."""

    CARE_PLAN = "CarePlan"
    DEVICE_REQUEST = "DeviceRequest"
    MEDICATION_REQUEST = "MedicationRequest"
    SERVICE_REQUEST = "ServiceRequest"
    REQUEST_ORCHESTRATION = "RequestOrchestration"
    NUTRITION_ORDER = "NutritionOrder"
    VISION_PRESCRIPTION = "VisionPrescription"


class EncounterDiagnosisConditionType(str, Enum):
    """FHIR R5 reference types for Encounter.diagnosis.condition (CodeableReference)."""

    CONDITION = "Condition"


class EncounterServiceTypeReferenceType(str, Enum):
    """FHIR R5 reference types for Encounter.serviceType.reference (CodeableReference)."""

    HEALTHCARE_SERVICE = "HealthcareService"


class EncounterReasonValueReferenceType(str, Enum):
    """FHIR R5 reference types for Encounter.reason.value.reference (CodeableReference)."""

    CONDITION = "Condition"
    DIAGNOSTIC_REPORT = "DiagnosticReport"
    OBSERVATION = "Observation"
    PROCEDURE = "Procedure"


class EncounterEpisodeOfCareReferenceType(str, Enum):
    """Allowed reference types for Encounter.episodeOfCare[]."""

    EPISODE_OF_CARE = "EpisodeOfCare"


class EncounterCareTeamReferenceType(str, Enum):
    """Allowed reference types for Encounter.careTeam[] — R5 new."""

    CARE_TEAM = "CareTeam"


class EncounterAppointmentReferenceType(str, Enum):
    """Allowed reference types for Encounter.appointment[]."""

    APPOINTMENT = "Appointment"


class EncounterAccountReferenceType(str, Enum):
    """Allowed reference types for Encounter.account[]."""

    ACCOUNT = "Account"


class EncounterLocationReferenceType(str, Enum):
    """Allowed reference types for Encounter.location[].location."""

    LOCATION = "Location"
