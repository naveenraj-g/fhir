from enum import Enum

# Value sets shared with PlanDefinition (same R4 bindings) are re-used rather than redefined.
from app.models.plan_definition.enums import (  # noqa: F401
    ActionParticipantType,
    ActionPriority,
    PlanDefinitionContactKind,
    PlanDefinitionGroupReferenceType,
    PlanDefinitionStatus,
    PlanDefinitionUseContextReferenceType,
    RelatedArtifactScope,
    RelatedArtifactType,
)


class ActivityDefinitionKind(str, Enum):
    """FHIR R4 RequestResourceType (ActivityDefinition.kind, required binding)."""

    Appointment = "Appointment"
    AppointmentResponse = "AppointmentResponse"
    CarePlan = "CarePlan"
    Claim = "Claim"
    CommunicationRequest = "CommunicationRequest"
    Contract = "Contract"
    DeviceRequest = "DeviceRequest"
    EnrollmentRequest = "EnrollmentRequest"
    ImmunizationRecommendation = "ImmunizationRecommendation"
    MedicationRequest = "MedicationRequest"
    NutritionOrder = "NutritionOrder"
    ServiceRequest = "ServiceRequest"
    SupplyRequest = "SupplyRequest"
    Task = "Task"
    VisionPrescription = "VisionPrescription"


class ActivityDefinitionIntent(str, Enum):
    """FHIR R4 RequestIntent (ActivityDefinition.intent, required binding)."""

    proposal = "proposal"
    plan = "plan"
    directive = "directive"
    order = "order"
    original_order = "original-order"
    reflex_order = "reflex-order"
    filler_order = "filler-order"
    instance_order = "instance-order"
    option = "option"


class ActivityDefinitionLocationReferenceType(str, Enum):
    """ActivityDefinition.location -> Reference(Location)."""

    Location = "Location"


class ActivityDefinitionProductReferenceType(str, Enum):
    """ActivityDefinition.productReference -> Reference(Medication | Substance)."""

    Medication = "Medication"
    Substance = "Substance"


class ActivityDefinitionSpecimenReferenceType(str, Enum):
    """ActivityDefinition.specimenRequirement -> Reference(SpecimenDefinition)."""

    SpecimenDefinition = "SpecimenDefinition"


class ActivityDefinitionObservationReferenceType(str, Enum):
    """ActivityDefinition.observationRequirement / observationResultRequirement -> Reference(ObservationDefinition)."""

    ObservationDefinition = "ObservationDefinition"
