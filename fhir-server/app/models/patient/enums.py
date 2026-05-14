from enum import Enum


class PatientGender(str, Enum):
    """FHIR R4 administrative gender (used by Patient.gender and Patient.contact.gender)."""

    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"


class PatientLinkType(str, Enum):
    """FHIR R4 link type codes for Patient.link.type."""

    REPLACED_BY = "replaced-by"
    REPLACES = "replaces"
    REFER = "refer"
    SEEALSO = "seealso"


class PatientGeneralPractitionerType(str, Enum):
    """Allowed reference types for Patient.generalPractitioner."""

    ORGANIZATION = "Organization"
    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"


class PatientLinkOtherType(str, Enum):
    """Allowed reference types for Patient.link.other."""

    PATIENT = "Patient"
    RELATED_PERSON = "RelatedPerson"
