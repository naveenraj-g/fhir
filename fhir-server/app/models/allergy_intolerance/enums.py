from enum import Enum


class AllergyIntoleranceType(str, Enum):
    """FHIR R4 AllergyIntolerance.type — allergy | intolerance."""

    ALLERGY = "allergy"
    INTOLERANCE = "intolerance"


class AllergyIntoleranceCriticality(str, Enum):
    """FHIR R4 AllergyIntolerance.criticality."""

    LOW = "low"
    HIGH = "high"
    UNABLE_TO_ASSESS = "unable-to-assess"


class AllergyIntoleranceCategoryCode(str, Enum):
    """Allowed values for AllergyIntolerance.category[]."""

    FOOD = "food"
    MEDICATION = "medication"
    ENVIRONMENT = "environment"
    BIOLOGIC = "biologic"


class AllergyIntoleranceReactionSeverity(str, Enum):
    """FHIR R4 AllergyIntolerance.reaction.severity."""

    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


class AllergyIntolerancePatientReferenceType(str, Enum):
    """Allowed reference type for AllergyIntolerance.patient (1..1)."""

    PATIENT = "Patient"


class AllergyIntoleranceParticipantReferenceType(str, Enum):
    """Allowed reference types for AllergyIntolerance.recorder and asserter.

    Shared PG enum type 'allergy_intolerance_participant_reference_type'
    used for both recorder_type and asserter_type columns (second uses create_type=False).
    """

    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    PATIENT = "Patient"
    RELATED_PERSON = "RelatedPerson"
