from enum import Enum


class SubjectReferenceType(str, Enum):
    """Shared subject reference types used across Encounter, Appointment, QuestionnaireResponse.
    All three store this as DB type name 'subject_reference_type'."""

    PATIENT = "Patient"
    GROUP = "Group"


class IdentifierUse(str, Enum):
    """FHIR R4 IdentifierUse — used by any resource that stores an identifier.use column."""

    USUAL = "usual"
    OFFICIAL = "official"
    TEMP = "temp"
    SECONDARY = "secondary"
    OLD = "old"
