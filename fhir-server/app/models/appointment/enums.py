from enum import Enum


class AppointmentStatus(str, Enum):
    """FHIR R4 Appointment status value set."""

    proposed = "proposed"
    pending = "pending"
    booked = "booked"
    arrived = "arrived"
    fulfilled = "fulfilled"
    cancelled = "cancelled"
    noshow = "noshow"
    entered_in_error = "entered-in-error"
    checked_in = "checked-in"
    waitlist = "waitlist"


class AppointmentParticipantRequired(str, Enum):
    """FHIR R4 participant.required — code type (R5 changed to boolean)."""

    required = "required"
    optional = "optional"
    information_only = "information-only"


class AppointmentParticipantStatus(str, Enum):
    """FHIR R4 participant.status value set."""

    accepted = "accepted"
    declined = "declined"
    tentative = "tentative"
    needs_action = "needs-action"


class AppointmentParticipantActorType(str, Enum):
    """FHIR R4 reference types for Appointment.participant.actor.
    R4 does NOT include Group or CareTeam — those are R5-only."""

    PATIENT = "Patient"
    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    RELATED_PERSON = "RelatedPerson"
    DEVICE = "Device"
    HEALTHCARE_SERVICE = "HealthcareService"
    LOCATION = "Location"
