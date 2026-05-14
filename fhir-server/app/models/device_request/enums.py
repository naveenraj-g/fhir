from enum import Enum


class DeviceRequestStatus(str, Enum):
    """FHIR R4 RequestStatus value set (used by DeviceRequest.status)."""

    DRAFT = "draft"
    ACTIVE = "active"
    ON_HOLD = "on-hold"
    REVOKED = "revoked"
    COMPLETED = "completed"
    ENTERED_IN_ERROR = "entered-in-error"
    UNKNOWN = "unknown"


class DeviceRequestIntent(str, Enum):
    """FHIR R4 RequestIntent value set (used by DeviceRequest.intent)."""

    PROPOSAL = "proposal"
    PLAN = "plan"
    DIRECTIVE = "directive"
    ORDER = "order"
    ORIGINAL_ORDER = "original-order"
    REFLEX_ORDER = "reflex-order"
    FILLER_ORDER = "filler-order"
    INSTANCE_ORDER = "instance-order"
    OPTION = "option"


class DeviceRequestPriority(str, Enum):
    """FHIR R4 RequestPriority value set."""

    ROUTINE = "routine"
    URGENT = "urgent"
    ASAP = "asap"
    STAT = "stat"


class DeviceRequestSubjectType(str, Enum):
    """Allowed subject reference types for DeviceRequest.subject."""

    PATIENT = "Patient"
    GROUP = "Group"
    LOCATION = "Location"
    DEVICE = "Device"


class DeviceRequestRequesterType(str, Enum):
    """Allowed reference types for DeviceRequest.requester."""

    DEVICE = "Device"
    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    ORGANIZATION = "Organization"


class DeviceRequestPerformerReferenceType(str, Enum):
    """Allowed reference types for DeviceRequest.performer."""

    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    ORGANIZATION = "Organization"
    CARE_TEAM = "CareTeam"
    HEALTHCARE_SERVICE = "HealthcareService"
    PATIENT = "Patient"
    DEVICE = "Device"
    RELATED_PERSON = "RelatedPerson"
