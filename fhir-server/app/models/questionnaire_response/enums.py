from enum import Enum


class QuestionnaireResponseStatus(str, Enum):
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    AMENDED = "amended"
    ENTERED_IN_ERROR = "entered-in-error"
    STOPPED = "stopped"


class QuestionnaireResponseAuthorReferenceType(str, Enum):
    DEVICE = "Device"
    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    PATIENT = "Patient"
    RELATED_PERSON = "RelatedPerson"
    ORGANIZATION = "Organization"


class QuestionnaireResponseSourceReferenceType(str, Enum):
    PATIENT = "Patient"
    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    RELATED_PERSON = "RelatedPerson"


class QRBasedOnReferenceType(str, Enum):
    CARE_PLAN = "CarePlan"
    SERVICE_REQUEST = "ServiceRequest"


class QRPartOfReferenceType(str, Enum):
    OBSERVATION = "Observation"
    PROCEDURE = "Procedure"
