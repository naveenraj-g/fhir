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
from app.schemas.patient.response import (
    FHIRPatientSchema,
    FHIRPatientBundle,
    PaginatedPatientResponse,
    PlainPatientResponse,
    PlainPatientName,
    PlainPatientIdentifier,
    PlainPatientTelecom,
    PlainPatientAddress,
    PlainPatientPhoto,
    PlainPatientContact,
    PlainPatientCommunication,
    PlainPatientGeneralPractitioner,
    PlainPatientLink,
    FHIRPatientContact,
    FHIRPatientCommunication,
    FHIRPatientLink,
    FHIRAttachment,
)

__all__ = [
    # Input
    "PatientCreateSchema", "PatientPatchSchema",
    "NameCreate", "IdentifierCreate", "TelecomCreate", "AddressCreate",
    "PhotoCreate", "ContactCreate", "ContactRelationshipCreate", "ContactTelecomCreate",
    "CommunicationCreate", "GeneralPractitionerCreate", "LinkCreate",
    # Response
    "FHIRPatientSchema", "FHIRPatientBundle", "PaginatedPatientResponse",
    "PlainPatientResponse", "PlainPatientName", "PlainPatientIdentifier",
    "PlainPatientTelecom", "PlainPatientAddress", "PlainPatientPhoto",
    "PlainPatientContact", "PlainPatientCommunication",
    "PlainPatientGeneralPractitioner", "PlainPatientLink",
    "FHIRPatientContact", "FHIRPatientCommunication", "FHIRPatientLink", "FHIRAttachment",
]
