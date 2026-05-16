from enum import Enum


class ClaimResponseStatus(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    DRAFT = "draft"
    ENTERED_IN_ERROR = "entered-in-error"


class ClaimResponseUse(str, Enum):
    CLAIM = "claim"
    PREAUTHORIZATION = "preauthorization"
    PREDETERMINATION = "predetermination"


class ClaimResponseOutcome(str, Enum):
    QUEUED = "queued"
    COMPLETE = "complete"
    ERROR = "error"
    PARTIAL = "partial"


class ClaimResponsePatientReferenceType(str, Enum):
    PATIENT = "Patient"


class ClaimResponseRequestorReferenceType(str, Enum):
    """Allowed types for ClaimResponse.requestor."""
    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    ORGANIZATION = "Organization"


class ClaimResponseRequestReferenceType(str, Enum):
    CLAIM = "Claim"


class ClaimResponseAddItemProviderReferenceType(str, Enum):
    """Allowed types for ClaimResponse.addItem.provider."""
    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    ORGANIZATION = "Organization"


class ClaimResponseAddItemLocationReferenceType(str, Enum):
    """Allowed Reference type for ClaimResponse.addItem.location[x] Reference variant."""
    LOCATION = "Location"


class ClaimResponseInsuranceCoverageReferenceType(str, Enum):
    COVERAGE = "Coverage"


class ClaimResponseInsuranceClaimResponseReferenceType(str, Enum):
    CLAIM_RESPONSE = "ClaimResponse"


class ClaimResponseCommunicationRequestReferenceType(str, Enum):
    COMMUNICATION_REQUEST = "CommunicationRequest"
