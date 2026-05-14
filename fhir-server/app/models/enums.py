from enum import Enum


class SubjectReferenceType(str, Enum):
    """FHIR subject reference types for Encounter.subject."""

    PATIENT = "Patient"
    GROUP = "Group"


class GenderType(str, Enum):
    """
    FHIR AdministrativeGender value set.

    The gender of a person for administrative purposes.
    """

    male = "male"
    female = "female"
    other = "other"
    unknown = "unknown"


class IdentifierUse(str, Enum):
    """
    FHIR IdentifierUse value set.

    Indicates the purpose of the identifier.
    """

    usual = "usual"  # The identifier the resource owner normally uses
    official = (
        "official"  # The identifier considered official for legal/administrative use
    )
    temp = "temp"  # Temporary identifier
    secondary = "secondary"  # Additional identifier
    old = "old"  # No longer valid identifier


class PractitionerRole(str, Enum):
    doctor = "doctor"
    nurse = "nurse"
