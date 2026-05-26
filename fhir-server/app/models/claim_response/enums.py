from enum import Enum


class ClaimResponseStatus(str, Enum):
    active = "active"
    cancelled = "cancelled"
    draft = "draft"
    entered_in_error = "entered-in-error"


class ClaimResponseUse(str, Enum):
    claim = "claim"
    preauthorization = "preauthorization"
    predetermination = "predetermination"


class ClaimResponseOutcome(str, Enum):
    queued = "queued"
    complete = "complete"
    error = "error"
    partial = "partial"


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
