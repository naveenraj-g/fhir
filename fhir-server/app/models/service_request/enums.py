from enum import Enum


class ServiceRequestStatus(str, Enum):
    """FHIR R4 ServiceRequest status value set."""

    DRAFT = "draft"
    ACTIVE = "active"
    ON_HOLD = "on-hold"
    REVOKED = "revoked"
    COMPLETED = "completed"
    ENTERED_IN_ERROR = "entered-in-error"
    UNKNOWN = "unknown"


class ServiceRequestIntent(str, Enum):
    """FHIR R4 ServiceRequest intent value set."""

    PROPOSAL = "proposal"
    PLAN = "plan"
    DIRECTIVE = "directive"
    ORDER = "order"
    ORIGINAL_ORDER = "original-order"
    REFLEX_ORDER = "reflex-order"
    FILLER_ORDER = "filler-order"
    INSTANCE_ORDER = "instance-order"
    OPTION = "option"


class ServiceRequestPriority(str, Enum):
    """FHIR R4 request priority value set."""

    ROUTINE = "routine"
    URGENT = "urgent"
    ASAP = "asap"
    STAT = "stat"


class ServiceRequestSubjectType(str, Enum):
    """Allowed subject reference types for ServiceRequest.subject."""

    PATIENT = "Patient"
    GROUP = "Group"
    LOCATION = "Location"
    DEVICE = "Device"


class ServiceRequestRequesterType(str, Enum):
    """Allowed reference types for ServiceRequest.requester."""

    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    ORGANIZATION = "Organization"
    PATIENT = "Patient"
    RELATED_PERSON = "RelatedPerson"
    DEVICE = "Device"


class ServiceRequestPerformerReferenceType(str, Enum):
    """Allowed reference types for ServiceRequest.performer[]."""

    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    ORGANIZATION = "Organization"
    CARE_TEAM = "CareTeam"
    HEALTHCARE_SERVICE = "HealthcareService"
    PATIENT = "Patient"
    DEVICE = "Device"
    RELATED_PERSON = "RelatedPerson"
