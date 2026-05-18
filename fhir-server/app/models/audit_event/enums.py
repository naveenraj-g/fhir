from enum import Enum


class AuditEventWhoReferenceType(str, Enum):
    """Allowed reference types for AuditEvent.agent.who and AuditEvent.source.observer."""

    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    ORGANIZATION = "Organization"
    DEVICE = "Device"
    PATIENT = "Patient"
    RELATED_PERSON = "RelatedPerson"


class AuditEventLocationReferenceType(str, Enum):
    """Allowed reference type for AuditEvent.agent.location."""

    LOCATION = "Location"
