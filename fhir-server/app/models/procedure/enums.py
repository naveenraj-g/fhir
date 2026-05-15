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


class ProcedureLocationReferenceType(str, Enum):
    """Allowed reference types for Procedure.location."""

    LOCATION = "Location"


class ProcedurePerformerActorType(str, Enum):
    """Allowed reference types for Procedure.performer.actor."""

    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    ORGANIZATION = "Organization"
    PATIENT = "Patient"
    RELATED_PERSON = "RelatedPerson"
    DEVICE = "Device"


class ProcedurePerformerOnBehalfOfType(str, Enum):
    """Allowed reference types for Procedure.performer.onBehalfOf."""

    ORGANIZATION = "Organization"


class ProcedureBasedOnReferenceType(str, Enum):
    """Allowed reference types for Procedure.basedOn[]."""

    CARE_PLAN = "CarePlan"
    SERVICE_REQUEST = "ServiceRequest"


class ProcedurePartOfReferenceType(str, Enum):
    """Allowed reference types for Procedure.partOf[]."""

    PROCEDURE = "Procedure"
    OBSERVATION = "Observation"
    MEDICATION_ADMINISTRATION = "MedicationAdministration"


class ProcedureReasonReferenceType(str, Enum):
    """Allowed reference types for Procedure.reasonReference[]."""

    CONDITION = "Condition"
    OBSERVATION = "Observation"
    PROCEDURE = "Procedure"
    DIAGNOSTIC_REPORT = "DiagnosticReport"
    DOCUMENT_REFERENCE = "DocumentReference"


class ProcedureReportReferenceType(str, Enum):
    """Allowed reference types for Procedure.report[]."""

    DIAGNOSTIC_REPORT = "DiagnosticReport"
    DOCUMENT_REFERENCE = "DocumentReference"
    COMPOSITION = "Composition"


class ProcedureComplicationDetailReferenceType(str, Enum):
    """Allowed reference types for Procedure.complicationDetail[]."""

    CONDITION = "Condition"


class ProcedureNoteAuthorReferenceType(str, Enum):
    """Allowed reference types for Procedure.note[].author (Annotation.authorReference)."""

    PRACTITIONER = "Practitioner"
    PATIENT = "Patient"
    RELATED_PERSON = "RelatedPerson"
    ORGANIZATION = "Organization"


class ProcedureFocalDeviceManipulatedReferenceType(str, Enum):
    """Allowed reference types for Procedure.focalDevice[].manipulated."""

    DEVICE = "Device"


class ProcedureUsedReferenceType(str, Enum):
    """Allowed reference types for Procedure.usedReference[]."""

    DEVICE = "Device"
    MEDICATION = "Medication"
    SUBSTANCE = "Substance"
