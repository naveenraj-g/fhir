from enum import Enum


class InvoiceStatus(str, Enum):
    """Invoice.status required binding."""
    DRAFT = "draft"
    ISSUED = "issued"
    BALANCED = "balanced"
    CANCELLED = "cancelled"
    ENTERED_IN_ERROR = "entered-in-error"


class InvoiceSubjectReferenceType(str, Enum):
    """Allowed reference types for Invoice.subject."""
    PATIENT = "Patient"
    GROUP = "Group"


class InvoiceRecipientReferenceType(str, Enum):
    """Allowed reference types for Invoice.recipient."""
    ORGANIZATION = "Organization"
    PATIENT = "Patient"
    RELATED_PERSON = "RelatedPerson"


class InvoiceParticipantActorReferenceType(str, Enum):
    """Allowed reference types for Invoice.participant.actor."""
    PRACTITIONER = "Practitioner"
    ORGANIZATION = "Organization"
    PATIENT = "Patient"
    PRACTITIONER_ROLE = "PractitionerRole"
    DEVICE = "Device"
    RELATED_PERSON = "RelatedPerson"


class InvoiceAccountReferenceType(str, Enum):
    """Allowed reference types for Invoice.account."""
    ACCOUNT = "Account"


class InvoiceLineItemChargeItemReferenceType(str, Enum):
    """Allowed reference type for Invoice.lineItem.chargeItem[x] Reference variant."""
    CHARGE_ITEM = "ChargeItem"
