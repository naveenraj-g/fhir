from enum import Enum


class CarePlanStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ON_HOLD = "on-hold"
    REVOKED = "revoked"
    COMPLETED = "completed"
    ENTERED_IN_ERROR = "entered-in-error"
    UNKNOWN = "unknown"


class CarePlanIntent(str, Enum):
    PROPOSAL = "proposal"
    PLAN = "plan"
    ORDER = "order"
    OPTION = "option"


class CarePlanSubjectReferenceType(str, Enum):
    PATIENT = "Patient"
    GROUP = "Group"


class CarePlanAuthorReferenceType(str, Enum):
    PATIENT = "Patient"
    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    DEVICE = "Device"
    RELATED_PERSON = "RelatedPerson"
    ORGANIZATION = "Organization"
    CARE_TEAM = "CareTeam"


class CarePlanContributorReferenceType(str, Enum):
    PATIENT = "Patient"
    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    DEVICE = "Device"
    RELATED_PERSON = "RelatedPerson"
    ORGANIZATION = "Organization"
    CARE_TEAM = "CareTeam"


class CarePlanBasedOnReferenceType(str, Enum):
    CARE_PLAN = "CarePlan"


class CarePlanReplacesReferenceType(str, Enum):
    CARE_PLAN = "CarePlan"


class CarePlanPartOfReferenceType(str, Enum):
    CARE_PLAN = "CarePlan"


class CarePlanCareTeamReferenceType(str, Enum):
    CARE_TEAM = "CareTeam"


class CarePlanAddressesReferenceType(str, Enum):
    CONDITION = "Condition"


class CarePlanGoalReferenceType(str, Enum):
    GOAL = "Goal"


class CarePlanActivityReferenceType(str, Enum):
    APPOINTMENT = "Appointment"
    COMMUNICATION_REQUEST = "CommunicationRequest"
    DEVICE_REQUEST = "DeviceRequest"
    MEDICATION_REQUEST = "MedicationRequest"
    NUTRITION_ORDER = "NutritionOrder"
    TASK = "Task"
    SERVICE_REQUEST = "ServiceRequest"
    VISION_PRESCRIPTION = "VisionPrescription"
    REQUEST_GROUP = "RequestGroup"


class CarePlanDetailActivityStatus(str, Enum):
    NOT_STARTED = "not-started"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in-progress"
    ON_HOLD = "on-hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    STOPPED = "stopped"
    UNKNOWN = "unknown"
    ENTERED_IN_ERROR = "entered-in-error"


class CarePlanDetailLocationReferenceType(str, Enum):
    LOCATION = "Location"


class CarePlanDetailPerformerReferenceType(str, Enum):
    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    ORGANIZATION = "Organization"
    RELATED_PERSON = "RelatedPerson"
    PATIENT = "Patient"
    CARE_TEAM = "CareTeam"
    HEALTHCARE_SERVICE = "HealthcareService"
    DEVICE = "Device"


class CarePlanDetailReasonReferenceType(str, Enum):
    CONDITION = "Condition"
    OBSERVATION = "Observation"
    DIAGNOSTIC_REPORT = "DiagnosticReport"
    DOCUMENT_REFERENCE = "DocumentReference"


class CarePlanDetailGoalReferenceType(str, Enum):
    GOAL = "Goal"


class CarePlanDetailProductReferenceType(str, Enum):
    MEDICATION = "Medication"
    SUBSTANCE = "Substance"
