from enum import Enum


class EpisodeOfCareStatus(str, Enum):
    PLANNED = "planned"
    WAITLIST = "waitlist"
    ACTIVE = "active"
    ONHOLD = "onhold"
    FINISHED = "finished"
    CANCELLED = "cancelled"
    ENTERED_IN_ERROR = "entered-in-error"


class EpisodeOfCarePatientReferenceType(str, Enum):
    """Allowed reference type for EpisodeOfCare.patient."""

    PATIENT = "Patient"


class EpisodeOfCareCareManagerReferenceType(str, Enum):
    """Allowed reference types for EpisodeOfCare.careManager."""

    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"


class EpisodeOfCareDiagnosisReferenceType(str, Enum):
    """Allowed reference type for EpisodeOfCare.diagnosis.condition."""

    CONDITION = "Condition"


class EpisodeOfCareReferralRequestReferenceType(str, Enum):
    """Allowed reference type for EpisodeOfCare.referralRequest."""

    SERVICE_REQUEST = "ServiceRequest"


class EpisodeOfCareTeamReferenceType(str, Enum):
    """Allowed reference type for EpisodeOfCare.team."""

    CARE_TEAM = "CareTeam"


class EpisodeOfCareAccountReferenceType(str, Enum):
    """Allowed reference type for EpisodeOfCare.account."""

    ACCOUNT = "Account"
