from enum import Enum


class TaskStatus(str, Enum):
    DRAFT = "draft"
    REQUESTED = "requested"
    RECEIVED = "received"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    READY = "ready"
    CANCELLED = "cancelled"
    IN_PROGRESS = "in-progress"
    ON_HOLD = "on-hold"
    FAILED = "failed"
    COMPLETED = "completed"
    ENTERED_IN_ERROR = "entered-in-error"


class TaskIntent(str, Enum):
    UNKNOWN = "unknown"
    PROPOSAL = "proposal"
    PLAN = "plan"
    ORDER = "order"
    ORIGINAL_ORDER = "original-order"
    REFLEX_ORDER = "reflex-order"
    FILLER_ORDER = "filler-order"
    INSTANCE_ORDER = "instance-order"
    OPTION = "option"


class TaskPriority(str, Enum):
    ROUTINE = "routine"
    URGENT = "urgent"
    ASAP = "asap"
    STAT = "stat"


class TaskRequesterReferenceType(str, Enum):
    DEVICE = "Device"
    ORGANIZATION = "Organization"
    PATIENT = "Patient"
    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    RELATED_PERSON = "RelatedPerson"


class TaskOwnerReferenceType(str, Enum):
    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    ORGANIZATION = "Organization"
    CARE_TEAM = "CareTeam"
    HEALTHCARE_SERVICE = "HealthcareService"
    PATIENT = "Patient"
    DEVICE = "Device"
    RELATED_PERSON = "RelatedPerson"


class TaskLocationReferenceType(str, Enum):
    LOCATION = "Location"


class TaskInsuranceReferenceType(str, Enum):
    COVERAGE = "Coverage"
    CLAIM_RESPONSE = "ClaimResponse"


class TaskRelevantHistoryReferenceType(str, Enum):
    PROVENANCE = "Provenance"


class TaskPartOfReferenceType(str, Enum):
    TASK = "Task"


class TaskRestrictionRecipientReferenceType(str, Enum):
    PATIENT = "Patient"
    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    RELATED_PERSON = "RelatedPerson"
    GROUP = "Group"
    ORGANIZATION = "Organization"
