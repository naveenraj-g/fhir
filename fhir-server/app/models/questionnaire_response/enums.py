from enum import Enum


class QuestionnaireResponseStatus(str, Enum):
    in_progress = "in-progress"
    completed = "completed"
    amended = "amended"
    entered_in_error = "entered-in-error"
    stopped = "stopped"


class QuestionnaireResponseAuthorReferenceType(str, Enum):
    DEVICE = "Device"
    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    PATIENT = "Patient"
    RELATED_PERSON = "RelatedPerson"
    ORGANIZATION = "Organization"


class QuestionnaireResponseSourceReferenceType(str, Enum):
    """R4 allowed types for QuestionnaireResponse.source."""
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
