from enum import Enum


class SpecimenStatus(str, Enum):
    available = "available"
    unavailable = "unavailable"
    unsatisfactory = "unsatisfactory"
    entered_in_error = "entered-in-error"


class SpecimenSubjectReferenceType(str, Enum):
    PATIENT = "Patient"
    GROUP = "Group"
    DEVICE = "Device"
    SUBSTANCE = "Substance"
    LOCATION = "Location"


class SpecimenCollectorReferenceType(str, Enum):
    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"


class SpecimenParentReferenceType(str, Enum):
    SPECIMEN = "Specimen"


class SpecimenRequestReferenceType(str, Enum):
    SERVICE_REQUEST = "ServiceRequest"


class SpecimenProcessingAdditiveReferenceType(str, Enum):
    SUBSTANCE = "Substance"


class SpecimenContainerAdditiveReferenceType(str, Enum):
    SUBSTANCE = "Substance"
