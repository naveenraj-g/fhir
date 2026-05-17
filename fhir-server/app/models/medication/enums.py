from enum import Enum


class MedicationStatus(str, Enum):
    """FHIR R4 Medication.status — active | inactive | entered-in-error."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ENTERED_IN_ERROR = "entered-in-error"


class MedicationIngredientItemReferenceType(str, Enum):
    """Allowed reference types for Medication.ingredient.item[x] reference variant."""

    SUBSTANCE = "Substance"
    MEDICATION = "Medication"
