from enum import Enum


class EpisodeOfCareStatus(str, Enum):
    planned = "planned"
    waitlist = "waitlist"
    active = "active"
    onhold = "onhold"
    finished = "finished"
    cancelled = "cancelled"
    entered_in_error = "entered-in-error"


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
