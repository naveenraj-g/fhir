from enum import Enum


class MedicationRequestStatus(str, Enum):
    """FHIR R4 MedicationRequest status value set."""

    ACTIVE = "active"
    ON_HOLD = "on-hold"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    ENTERED_IN_ERROR = "entered-in-error"
    STOPPED = "stopped"
    DRAFT = "draft"
    UNKNOWN = "unknown"


class MedicationRequestIntent(str, Enum):
    """FHIR R4 MedicationRequest intent value set."""

    PROPOSAL = "proposal"
    PLAN = "plan"
    ORDER = "order"
    ORIGINAL_ORDER = "original-order"
    REFLEX_ORDER = "reflex-order"
    FILLER_ORDER = "filler-order"
    INSTANCE_ORDER = "instance-order"
    OPTION = "option"


class MedicationRequestPriority(str, Enum):
    """FHIR R4 request priority value set."""

    ROUTINE = "routine"
    URGENT = "urgent"
    ASAP = "asap"
    STAT = "stat"


class MedicationSubjectType(str, Enum):
    """Allowed subject reference types for MedicationRequest.subject."""

    PATIENT = "Patient"
    GROUP = "Group"


class MedicationRequesterType(str, Enum):
    """Allowed reference types for MedicationRequest.requester."""

    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    ORGANIZATION = "Organization"
    PATIENT = "Patient"
    RELATED_PERSON = "RelatedPerson"
    DEVICE = "Device"


class MedicationPerformerType(str, Enum):
    """Allowed reference types for MedicationRequest.performer (R4 single performer)."""

    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    ORGANIZATION = "Organization"
    PATIENT = "Patient"
    DEVICE = "Device"
    RELATED_PERSON = "RelatedPerson"
    CARE_TEAM = "CareTeam"


class MedicationRecorderType(str, Enum):
    """Allowed reference types for MedicationRequest.recorder."""

    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"


class MedicationReportedReferenceType(str, Enum):
    """Allowed reference types for MedicationRequest.reportedReference."""

    PATIENT = "Patient"
    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    RELATED_PERSON = "RelatedPerson"
    ORGANIZATION = "Organization"
