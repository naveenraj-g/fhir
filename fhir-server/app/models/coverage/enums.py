from enum import Enum


class CoverageStatus(str, Enum):
    """FHIR R4 Coverage.status value set (FM Status — Required)."""

    active = "active"
    cancelled = "cancelled"
    draft = "draft"
    entered_in_error = "entered-in-error"


class CoveragePolicyHolderReferenceType(str, Enum):
    """Allowed reference types for Coverage.policyHolder."""

    PATIENT = "Patient"
    RELATED_PERSON = "RelatedPerson"
    ORGANIZATION = "Organization"


class CoverageSubscriberReferenceType(str, Enum):
    """Allowed reference types for Coverage.subscriber."""

    PATIENT = "Patient"
    RELATED_PERSON = "RelatedPerson"


class CoverageBeneficiaryReferenceType(str, Enum):
    """Allowed reference types for Coverage.beneficiary."""

    PATIENT = "Patient"


class CoveragePayorReferenceType(str, Enum):
    """Allowed reference types for Coverage.payor[]."""

    ORGANIZATION = "Organization"
    PATIENT = "Patient"
    RELATED_PERSON = "RelatedPerson"


class CoverageContractReferenceType(str, Enum):
    """Allowed reference types for Coverage.contract[]."""

    CONTRACT = "Contract"
