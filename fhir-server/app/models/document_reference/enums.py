from enum import Enum


class DocumentReferenceStatus(str, Enum):
    CURRENT = "current"
    SUPERSEDED = "superseded"
    ENTERED_IN_ERROR = "entered-in-error"


class DocumentReferenceDocStatus(str, Enum):
    PRELIMINARY = "preliminary"
    FINAL = "final"
    AMENDED = "amended"
    ENTERED_IN_ERROR = "entered-in-error"


class DocumentReferenceSubjectReferenceType(str, Enum):
    """Allowed reference types for DocumentReference.subject."""

    PATIENT = "Patient"
    PRACTITIONER = "Practitioner"
    GROUP = "Group"
    DEVICE = "Device"


class DocumentReferenceAuthenticatorReferenceType(str, Enum):
    """Allowed reference types for DocumentReference.authenticator."""

    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    ORGANIZATION = "Organization"


class DocumentReferenceAuthorReferenceType(str, Enum):
    """Allowed reference types for DocumentReference.author."""

    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    ORGANIZATION = "Organization"
    DEVICE = "Device"
    PATIENT = "Patient"
    RELATED_PERSON = "RelatedPerson"


class DocumentReferenceRelatesToCode(str, Enum):
    """Relationship code for DocumentReference.relatesTo.code."""

    REPLACES = "replaces"
    TRANSFORMS = "transforms"
    SIGNS = "signs"
    APPENDS = "appends"


class DocumentReferenceRelatesToTargetType(str, Enum):
    """Allowed reference type for DocumentReference.relatesTo.target."""

    DOCUMENT_REFERENCE = "DocumentReference"


class DocumentReferenceContextEncounterType(str, Enum):
    """Allowed reference types for DocumentReference.context.encounter."""

    ENCOUNTER = "Encounter"
    EPISODE_OF_CARE = "EpisodeOfCare"


class DocumentReferenceContextSourcePatientInfoType(str, Enum):
    """Allowed reference type for DocumentReference.context.sourcePatientInfo."""

    PATIENT = "Patient"
