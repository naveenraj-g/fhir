from enum import Enum


class DocumentReferenceStatus(str, Enum):
    current = "current"
    superseded = "superseded"
    entered_in_error = "entered-in-error"


class DocumentReferenceDocStatus(str, Enum):
    preliminary = "preliminary"
    final = "final"
    amended = "amended"
    entered_in_error = "entered-in-error"


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

    replaces = "replaces"
    transforms = "transforms"
    signs = "signs"
    appends = "appends"


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
