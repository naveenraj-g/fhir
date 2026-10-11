from enum import Enum


class FlagStatus(str, Enum):
    """FHIR R4 FlagStatus value set (Flag.status, required binding)."""

    active = "active"
    inactive = "inactive"
    entered_in_error = "entered-in-error"


class FlagSubjectType(str, Enum):
    """Allowed reference types for Flag.subject (R4)."""

    Patient = "Patient"
    Location = "Location"
    Group = "Group"
    Organization = "Organization"
    Practitioner = "Practitioner"
    PlanDefinition = "PlanDefinition"
    Medication = "Medication"
    Procedure = "Procedure"


class FlagAuthorType(str, Enum):
    """Allowed reference types for Flag.author (R4)."""

    Device = "Device"
    Organization = "Organization"
    Patient = "Patient"
    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
