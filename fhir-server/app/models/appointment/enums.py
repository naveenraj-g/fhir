from enum import Enum


class AppointmentStatus(str, Enum):
    PROPOSED = "proposed"
    PENDING = "pending"
    BOOKED = "booked"
    ARRIVED = "arrived"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"
    NOSHOW = "noshow"
    ENTERED_IN_ERROR = "entered-in-error"
    CHECKED_IN = "checked-in"
    WAITLIST = "waitlist"


class AppointmentParticipantRequired(str, Enum):
    REQUIRED = "required"
    OPTIONAL = "optional"
    INFORMATION_ONLY = "information-only"


class AppointmentParticipantStatus(str, Enum):
    ACCEPTED = "accepted"
    DECLINED = "declined"
    TENTATIVE = "tentative"
    NEEDS_ACTION = "needs-action"


class AppointmentParticipantActorType(str, Enum):
    PATIENT = "Patient"
    GROUP = "Group"
    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    CARE_TEAM = "CareTeam"
    RELATED_PERSON = "RelatedPerson"
    DEVICE = "Device"
    HEALTHCARE_SERVICE = "HealthcareService"
    LOCATION = "Location"
