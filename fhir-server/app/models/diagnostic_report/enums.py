from enum import Enum


class DiagnosticReportStatus(str, Enum):
    """FHIR R4 DiagnosticReport status value set (full set)."""

    REGISTERED = "registered"
    PARTIAL = "partial"
    PRELIMINARY = "preliminary"
    FINAL = "final"
    AMENDED = "amended"
    CORRECTED = "corrected"
    APPENDED = "appended"
    CANCELLED = "cancelled"
    ENTERED_IN_ERROR = "entered-in-error"
    UNKNOWN = "unknown"


class DiagnosticReportSubjectType(str, Enum):
    """Allowed subject reference types for DiagnosticReport.subject."""

    PATIENT = "Patient"
    GROUP = "Group"
    DEVICE = "Device"
    LOCATION = "Location"


class DiagnosticReportParticipantType(str, Enum):
    """Allowed reference types for DiagnosticReport.performer and resultsInterpreter.

    Both fields share the same allowed set:
    Practitioner | PractitionerRole | Organization | CareTeam
    """

    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    ORGANIZATION = "Organization"
    CARE_TEAM = "CareTeam"
