from enum import Enum


class TaskStatus(str, Enum):
    draft = "draft"
    requested = "requested"
    received = "received"
    accepted = "accepted"
    rejected = "rejected"
    ready = "ready"
    cancelled = "cancelled"
    in_progress = "in-progress"
    on_hold = "on-hold"
    failed = "failed"
    completed = "completed"
    entered_in_error = "entered-in-error"


class TaskIntent(str, Enum):
    unknown = "unknown"
    proposal = "proposal"
    plan = "plan"
    order = "order"
    original_order = "original-order"
    reflex_order = "reflex-order"
    filler_order = "filler-order"
    instance_order = "instance-order"
    option = "option"


class TaskPriority(str, Enum):
    routine = "routine"
    urgent = "urgent"
    asap = "asap"
    stat = "stat"


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
