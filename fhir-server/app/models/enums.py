from enum import Enum


class SubjectReferenceType(str, Enum):
    """Shared subject reference types used across Encounter, Appointment, QuestionnaireResponse.
    All three store this as DB type name 'subject_reference_type'."""

    PATIENT = "Patient"
    GROUP = "Group"


class OrganizationReferenceType(str, Enum):
    """Shared enum for any FHIR field whose only allowed reference type is Organization.
    Stored as DB type name 'organization_reference_type' (shared across all tables).
    NOTE: this is a FHIR resource reference — distinct from the tenant org_id column."""

    ORGANIZATION = "Organization"


class IdentifierUse(str, Enum):
    """FHIR R4 IdentifierUse — used by any resource that stores an identifier.use column."""

    USUAL = "usual"
    OFFICIAL = "official"
    TEMP = "temp"
    SECONDARY = "secondary"
    OLD = "old"
