from app.schemas.patient.input import (
    PatientCreateSchema,
    PatientPatchSchema,
    NameCreate,
    IdentifierCreate,
    TelecomCreate,
    AddressCreate,
    PhotoCreate,
    ContactCreate,
    ContactRelationshipCreate,
    ContactTelecomCreate,
    CommunicationCreate,
    GeneralPractitionerCreate,
    LinkCreate,
)

# PatientResponseSchema kept for backwards compatibility — use PlainPatientResponse instead
from app.schemas.patient.response import PlainPatientResponse as PatientResponseSchema

__all__ = [
    "PatientCreateSchema",
    "PatientPatchSchema",
    "PatientResponseSchema",
    "NameCreate",
    "IdentifierCreate",
    "TelecomCreate",
    "AddressCreate",
    "PhotoCreate",
    "ContactCreate",
    "ContactRelationshipCreate",
    "ContactTelecomCreate",
    "CommunicationCreate",
    "GeneralPractitionerCreate",
    "LinkCreate",
]
