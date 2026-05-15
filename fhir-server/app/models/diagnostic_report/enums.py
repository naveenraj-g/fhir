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
    """Allowed reference types for DiagnosticReport.performer and resultsInterpreter."""

    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    ORGANIZATION = "Organization"
    CARE_TEAM = "CareTeam"


class DiagnosticReportBasedOnReferenceType(str, Enum):
    """Allowed reference types for DiagnosticReport.basedOn[]."""

    CARE_PLAN = "CarePlan"
    IMMUNIZATION_RECOMMENDATION = "ImmunizationRecommendation"
    MEDICATION_REQUEST = "MedicationRequest"
    NUTRITION_ORDER = "NutritionOrder"
    SERVICE_REQUEST = "ServiceRequest"


class DiagnosticReportSpecimenReferenceType(str, Enum):
    """Allowed reference types for DiagnosticReport.specimen[]."""

    SPECIMEN = "Specimen"


class DiagnosticReportResultReferenceType(str, Enum):
    """Allowed reference types for DiagnosticReport.result[]."""

    OBSERVATION = "Observation"


class DiagnosticReportImagingStudyReferenceType(str, Enum):
    """Allowed reference types for DiagnosticReport.imagingStudy[]."""

    IMAGING_STUDY = "ImagingStudy"


class DiagnosticReportMediaLinkReferenceType(str, Enum):
    """Allowed reference types for DiagnosticReport.media[].link."""

    MEDIA = "Media"
