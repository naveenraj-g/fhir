from enum import Enum


class DeviceRequestStatus(str, Enum):
    """FHIR R4 RequestStatus value set (used by DeviceRequest.status)."""

    draft = "draft"
    active = "active"
    on_hold = "on-hold"
    revoked = "revoked"
    completed = "completed"
    entered_in_error = "entered-in-error"
    unknown = "unknown"


class DeviceRequestIntent(str, Enum):
    """FHIR R4 RequestIntent value set (used by DeviceRequest.intent)."""

    proposal = "proposal"
    plan = "plan"
    directive = "directive"
    order = "order"
    original_order = "original-order"
    reflex_order = "reflex-order"
    filler_order = "filler-order"
    instance_order = "instance-order"
    option = "option"


class DeviceRequestPriority(str, Enum):
    """FHIR R4 RequestPriority value set."""

    routine = "routine"
    urgent = "urgent"
    asap = "asap"
    stat = "stat"


class DeviceRequestSubjectType(str, Enum):
    """Allowed subject reference types for DeviceRequest.subject."""

    PATIENT = "Patient"
    GROUP = "Group"
    LOCATION = "Location"
    DEVICE = "Device"


class DeviceRequestRequesterType(str, Enum):
    """Allowed reference types for DeviceRequest.requester."""

    DEVICE = "Device"
    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    ORGANIZATION = "Organization"


class DeviceRequestPerformerReferenceType(str, Enum):
    """Allowed reference types for DeviceRequest.performer."""

    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    ORGANIZATION = "Organization"
    CARE_TEAM = "CareTeam"
    HEALTHCARE_SERVICE = "HealthcareService"
    PATIENT = "Patient"
    DEVICE = "Device"
    RELATED_PERSON = "RelatedPerson"


class DeviceRequestCodeReferenceType(str, Enum):
    """Allowed reference types for DeviceRequest.codeReference."""

    DEVICE = "Device"


class DeviceRequestReasonReferenceType(str, Enum):
    """Allowed reference types for DeviceRequest.reasonReference[]."""

    CONDITION = "Condition"
    OBSERVATION = "Observation"
    DIAGNOSTIC_REPORT = "DiagnosticReport"
    DOCUMENT_REFERENCE = "DocumentReference"


class DeviceRequestInsuranceReferenceType(str, Enum):
    """Allowed reference types for DeviceRequest.insurance[]."""

    COVERAGE = "Coverage"
    CLAIM_RESPONSE = "ClaimResponse"


class DeviceRequestNoteAuthorReferenceType(str, Enum):
    """Allowed reference types for DeviceRequest.note[].author (Annotation.authorReference)."""

    PRACTITIONER = "Practitioner"
    PATIENT = "Patient"
    RELATED_PERSON = "RelatedPerson"
    ORGANIZATION = "Organization"


class DeviceRequestRelevantHistoryReferenceType(str, Enum):
    """Allowed reference types for DeviceRequest.relevantHistory[]."""

    PROVENANCE = "Provenance"
