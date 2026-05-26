from enum import Enum


class MedicationRequestStatus(str, Enum):
    """FHIR R4 MedicationRequest status value set."""

    active = "active"
    on_hold = "on-hold"
    cancelled = "cancelled"
    completed = "completed"
    entered_in_error = "entered-in-error"
    stopped = "stopped"
    draft = "draft"
    unknown = "unknown"


class MedicationRequestIntent(str, Enum):
    """FHIR R4 MedicationRequest intent value set."""

    proposal = "proposal"
    plan = "plan"
    order = "order"
    original_order = "original-order"
    reflex_order = "reflex-order"
    filler_order = "filler-order"
    instance_order = "instance-order"
    option = "option"


class MedicationRequestPriority(str, Enum):
    """FHIR R4 request priority value set."""

    routine = "routine"
    urgent = "urgent"
    asap = "asap"
    stat = "stat"


class MedicationSubjectType(str, Enum):
    """Allowed subject reference types for MedicationRequest.subject."""

    PATIENT = "Patient"
    GROUP = "Group"


class MedicationRequesterType(str, Enum):
    """Allowed reference types for MedicationRequest.requester."""

    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    ORGANIZATION = "Organization"
    PATIENT = "Patient"
    RELATED_PERSON = "RelatedPerson"
    DEVICE = "Device"


class MedicationPerformerType(str, Enum):
    """Allowed reference types for MedicationRequest.performer (R4 single performer)."""

    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    ORGANIZATION = "Organization"
    PATIENT = "Patient"
    DEVICE = "Device"
    RELATED_PERSON = "RelatedPerson"
    CARE_TEAM = "CareTeam"


class MedicationRecorderType(str, Enum):
    """Allowed reference types for MedicationRequest.recorder."""

    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"


class MedicationReportedReferenceType(str, Enum):
    """Allowed reference types for MedicationRequest.reportedReference."""

    PATIENT = "Patient"
    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    RELATED_PERSON = "RelatedPerson"
    ORGANIZATION = "Organization"


class MedicationRequestMedicationReferenceType(str, Enum):
    """Allowed reference types for MedicationRequest.medicationReference."""

    MEDICATION = "Medication"


class MedicationRequestPriorPrescriptionType(str, Enum):
    """Allowed reference types for MedicationRequest.priorPrescription."""

    MEDICATION_REQUEST = "MedicationRequest"


class MedicationRequestReasonReferenceType(str, Enum):
    """Allowed reference types for MedicationRequest.reasonReference[]."""

    CONDITION = "Condition"
    OBSERVATION = "Observation"


class MedicationRequestBasedOnReferenceType(str, Enum):
    """Allowed reference types for MedicationRequest.basedOn[]."""

    CARE_PLAN = "CarePlan"
    MEDICATION_REQUEST = "MedicationRequest"
    SERVICE_REQUEST = "ServiceRequest"
    IMMUNIZATION_RECOMMENDATION = "ImmunizationRecommendation"


class MedicationRequestInsuranceReferenceType(str, Enum):
    """Allowed reference types for MedicationRequest.insurance[]."""

    COVERAGE = "Coverage"
    CLAIM_RESPONSE = "ClaimResponse"


class MedicationRequestNoteAuthorReferenceType(str, Enum):
    """Allowed reference types for MedicationRequest.note[].author (Annotation.authorReference)."""

    PRACTITIONER = "Practitioner"
    PATIENT = "Patient"
    RELATED_PERSON = "RelatedPerson"
    ORGANIZATION = "Organization"


class MedicationRequestDetectedIssueReferenceType(str, Enum):
    """Allowed reference types for MedicationRequest.detectedIssue[]."""

    DETECTED_ISSUE = "DetectedIssue"


class MedicationRequestEventHistoryReferenceType(str, Enum):
    """Allowed reference types for MedicationRequest.eventHistory[]."""

    PROVENANCE = "Provenance"


class MedicationRequestDispensePerformerType(str, Enum):
    """Allowed reference types for MedicationRequest.dispenseRequest.performer."""

    ORGANIZATION = "Organization"
