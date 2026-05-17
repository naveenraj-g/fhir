from enum import Enum


class ProvenanceEntityRole(str, Enum):
    """FHIR R4 Provenance.entity.role — how the entity was used in the activity."""

    DERIVATION = "derivation"
    REVISION = "revision"
    QUOTATION = "quotation"
    SOURCE = "source"
    REMOVAL = "removal"


class ProvenanceAgentWhoReferenceType(str, Enum):
    """Allowed reference types for Provenance.agent.who and agent.onBehalfOf.
    Shared PG enum 'provenance_agent_who_reference_type' (create_type=False for onBehalfOf
    and provenance_entity_agent columns)."""

    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    RELATED_PERSON = "RelatedPerson"
    PATIENT = "Patient"
    DEVICE = "Device"
    ORGANIZATION = "Organization"


class ProvenanceLocationReferenceType(str, Enum):
    """Allowed reference type for Provenance.location."""

    LOCATION = "Location"
