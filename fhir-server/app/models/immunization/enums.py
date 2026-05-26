from enum import Enum


class ImmunizationStatus(str, Enum):
    completed = "completed"
    entered_in_error = "entered-in-error"
    not_done = "not-done"


class ImmunizationPatientReferenceType(str, Enum):
    """Allowed reference type for Immunization.patient."""

    PATIENT = "Patient"


class ImmunizationLocationReferenceType(str, Enum):
    """Allowed reference type for Immunization.location."""

    LOCATION = "Location"


class ImmunizationPerformerActorReferenceType(str, Enum):
    """Allowed reference types for Immunization.performer.actor."""

    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    ORGANIZATION = "Organization"


class ImmunizationReasonReferenceType(str, Enum):
    """Allowed reference types for Immunization.reasonReference."""

    CONDITION = "Condition"
    OBSERVATION = "Observation"
    DIAGNOSTIC_REPORT = "DiagnosticReport"


class ImmunizationReactionDetailReferenceType(str, Enum):
    """Allowed reference type for Immunization.reaction.detail."""

    OBSERVATION = "Observation"
