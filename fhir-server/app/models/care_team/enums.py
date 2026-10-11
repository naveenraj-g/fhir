from enum import Enum


class CareTeamStatus(str, Enum):
    """FHIR R4 CareTeamStatus value set (CareTeam.status, required binding)."""

    proposed = "proposed"
    active = "active"
    suspended = "suspended"
    inactive = "inactive"
    entered_in_error = "entered-in-error"


class CareTeamParticipantMemberType(str, Enum):
    """Allowed reference types for CareTeam.participant.member (R4)."""

    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    RelatedPerson = "RelatedPerson"
    Patient = "Patient"
    Organization = "Organization"
    CareTeam = "CareTeam"


class CareTeamReasonReferenceType(str, Enum):
    """CareTeam.reasonReference -> Reference(Condition)."""

    Condition = "Condition"
