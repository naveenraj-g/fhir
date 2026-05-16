from enum import Enum


class ClaimStatus(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    DRAFT = "draft"
    ENTERED_IN_ERROR = "entered-in-error"


class ClaimUse(str, Enum):
    CLAIM = "claim"
    PREAUTHORIZATION = "preauthorization"
    PREDETERMINATION = "predetermination"


class ClaimPatientReferenceType(str, Enum):
    PATIENT = "Patient"


class ClaimEntererReferenceType(str, Enum):
    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"


class ClaimProviderReferenceType(str, Enum):
    """Allowed types for claim.provider and careTeam.provider."""
    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    ORGANIZATION = "Organization"


class ClaimPrescriptionReferenceType(str, Enum):
    """Allowed types for prescription and originalPrescription."""
    DEVICE_REQUEST = "DeviceRequest"
    MEDICATION_REQUEST = "MedicationRequest"
    VISION_PRESCRIPTION = "VisionPrescription"


class ClaimReferralReferenceType(str, Enum):
    SERVICE_REQUEST = "ServiceRequest"


class ClaimLocationReferenceType(str, Enum):
    """Allowed reference type for facility, accident.location, and item.location."""
    LOCATION = "Location"


class ClaimPayeePartyReferenceType(str, Enum):
    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    ORGANIZATION = "Organization"
    PATIENT = "Patient"
    RELATED_PERSON = "RelatedPerson"


class ClaimRelatedClaimReferenceType(str, Enum):
    CLAIM = "Claim"


class ClaimDiagnosisConditionReferenceType(str, Enum):
    CONDITION = "Condition"


class ClaimProcedureReferenceType(str, Enum):
    PROCEDURE = "Procedure"


class ClaimDeviceReferenceType(str, Enum):
    """Allowed reference type for all UDI fields (procedure.udi, item.udi, detail.udi, subDetail.udi)."""
    DEVICE = "Device"


class ClaimInsuranceCoverageReferenceType(str, Enum):
    COVERAGE = "Coverage"


class ClaimInsuranceClaimResponseReferenceType(str, Enum):
    CLAIM_RESPONSE = "ClaimResponse"


class ClaimItemEncounterReferenceType(str, Enum):
    ENCOUNTER = "Encounter"
