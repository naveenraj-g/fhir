from enum import Enum


class ProcedureStatus(str, Enum):
    """FHIR R4 Procedure status value set."""

    PREPARATION = "preparation"
    IN_PROGRESS = "in-progress"
    NOT_DONE = "not-done"
    ON_HOLD = "on-hold"
    STOPPED = "stopped"
    COMPLETED = "completed"
    ENTERED_IN_ERROR = "entered-in-error"
    UNKNOWN = "unknown"


class ProcedureSubjectType(str, Enum):
    """Allowed subject reference types for Procedure.subject (R4)."""

    PATIENT = "Patient"
    GROUP = "Group"


class ProcedureRecorderType(str, Enum):
    """Allowed reference types for Procedure.recorder."""

    PATIENT = "Patient"
    RELATED_PERSON = "RelatedPerson"
    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"


class ProcedureAsserterType(str, Enum):
    """Allowed reference types for Procedure.asserter."""

    PATIENT = "Patient"
    RELATED_PERSON = "RelatedPerson"
    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"


class ProcedurePerformerActorType(str, Enum):
    """Allowed reference types for Procedure.performer.actor."""

    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    ORGANIZATION = "Organization"
    PATIENT = "Patient"
    RELATED_PERSON = "RelatedPerson"
    DEVICE = "Device"
