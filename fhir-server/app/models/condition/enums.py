from enum import Enum


class ConditionSubjectType(str, Enum):
    """Allowed subject reference types for Condition.subject."""

    PATIENT = "Patient"
    GROUP = "Group"


class ConditionRecorderType(str, Enum):
    """Allowed reference types for Condition.recorder."""

    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    PATIENT = "Patient"
    RELATED_PERSON = "RelatedPerson"


class ConditionAsserterType(str, Enum):
    """Allowed reference types for Condition.asserter (same set as recorder)."""

    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    PATIENT = "Patient"
    RELATED_PERSON = "RelatedPerson"


class ConditionStageAssessmentType(str, Enum):
    """Allowed reference types for Condition.stage.assessment."""

    CLINICAL_IMPRESSION = "ClinicalImpression"
    DIAGNOSTIC_REPORT = "DiagnosticReport"
    OBSERVATION = "Observation"


class ConditionNoteAuthorReferenceType(str, Enum):
    """Allowed reference types for Condition.note[].author (Annotation.authorReference)."""

    PRACTITIONER = "Practitioner"
    PATIENT = "Patient"
    RELATED_PERSON = "RelatedPerson"
    ORGANIZATION = "Organization"
