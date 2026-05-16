from enum import Enum


class ScheduleActorReferenceType(str, Enum):
    """Allowed reference types for Schedule.actor."""
    PATIENT = "Patient"
    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    RELATED_PERSON = "RelatedPerson"
    DEVICE = "Device"
    HEALTHCARE_SERVICE = "HealthcareService"
    LOCATION = "Location"
