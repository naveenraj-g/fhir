from enum import Enum


class AppointmentStatus(str, Enum):
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


class AppointmentParticipantStatus(str, Enum):
    accepted = "accepted"
    declined = "declined"
    tentative = "tentative"
    needs_action = "needs-action"


class AppointmentParticipantActorType(str, Enum):
    PATIENT = "Patient"
    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    RELATED_PERSON = "RelatedPerson"
    DEVICE = "Device"
    HEALTHCARE_SERVICE = "HealthcareService"
    LOCATION = "Location"
    GROUP = "Group"
    CARE_TEAM = "CareTeam"


class AppointmentReasonReferenceType(str, Enum):
    """Allowed reference types for Appointment.reason.reference (CodeableReference)."""

    CONDITION = "Condition"
    PROCEDURE = "Procedure"
    OBSERVATION = "Observation"
    IMMUNIZATION_RECOMMENDATION = "ImmunizationRecommendation"
    DIAGNOSTIC_REPORT = "DiagnosticReport"


class AppointmentNoteAuthorReferenceType(str, Enum):
    """Allowed reference types for Appointment.note.author[x] (Annotation.authorReference)."""

    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    PATIENT = "Patient"
    RELATED_PERSON = "RelatedPerson"
    ORGANIZATION = "Organization"


class AppointmentPatientInstructionReferenceType(str, Enum):
    """Allowed reference types for Appointment.patientInstruction.reference (CodeableReference)."""

    DOCUMENT_REFERENCE = "DocumentReference"
    BINARY = "Binary"
    COMMUNICATION = "Communication"


class AppointmentReplacesReferenceType(str, Enum):
    """Allowed reference types for Appointment.replaces[]."""

    APPOINTMENT = "Appointment"


class AppointmentSlotReferenceType(str, Enum):
    """Allowed reference types for Appointment.slot[]."""

    SLOT = "Slot"


class AppointmentAccountReferenceType(str, Enum):
    """Allowed reference types for Appointment.account[]."""

    ACCOUNT = "Account"


class AppointmentServiceTypeReferenceType(str, Enum):
    """Allowed reference types for Appointment.serviceType.reference (CodeableReference)."""

    HEALTHCARE_SERVICE = "HealthcareService"


class AppointmentBasedOnReferenceType(str, Enum):
    """Allowed reference types for Appointment.basedOn (Reference)."""

    CARE_PLAN = "CarePlan"
    DEVICE_REQUEST = "DeviceRequest"
    MEDICATION_REQUEST = "MedicationRequest"
    SERVICE_REQUEST = "ServiceRequest"
    REQUEST_ORCHESTRATION = "RequestOrchestration"
    NUTRITION_ORDER = "NutritionOrder"
    VISION_PRESCRIPTION = "VisionPrescription"
