from enum import Enum


class RiskAssessmentStatus(str, Enum):
    """FHIR R4 ObservationStatus value set (RiskAssessment.status, required binding)."""

    registered = "registered"
    preliminary = "preliminary"
    final = "final"
    amended = "amended"
    corrected = "corrected"
    cancelled = "cancelled"
    entered_in_error = "entered-in-error"
    unknown = "unknown"


class RiskAssessmentSubjectType(str, Enum):
    """Allowed reference types for RiskAssessment.subject (R4)."""

    Patient = "Patient"
    Group = "Group"


class RiskAssessmentConditionReferenceType(str, Enum):
    """Allowed reference types for RiskAssessment.condition (R4)."""

    Condition = "Condition"


class RiskAssessmentPerformerType(str, Enum):
    """Allowed reference types for RiskAssessment.performer (R4)."""

    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    Device = "Device"


class RiskAssessmentReasonReferenceType(str, Enum):
    """Allowed reference types for RiskAssessment.reasonReference[] (R4)."""

    Condition = "Condition"
    Observation = "Observation"
    DiagnosticReport = "DiagnosticReport"
    DocumentReference = "DocumentReference"


class RiskAssessmentNoteAuthorReferenceType(str, Enum):
    """Allowed reference types for RiskAssessment.note[].authorReference (Annotation, R4)."""

    Practitioner = "Practitioner"
    Patient = "Patient"
    RelatedPerson = "RelatedPerson"
    Organization = "Organization"
