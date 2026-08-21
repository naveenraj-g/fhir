from enum import Enum


class StagingObservationStatus(str, Enum):
    registered = "registered"
    preliminary = "preliminary"
    final = "final"
    amended = "amended"
    corrected = "corrected"
    cancelled = "cancelled"
    entered_in_error = "entered-in-error"
    unknown = "unknown"


class StagingObservationSubjectReferenceType(str, Enum):
    Patient = "Patient"
    Group = "Group"
    Device = "Device"
    Location = "Location"


class StagingObservationSpecimenReferenceType(str, Enum):
    Specimen = "Specimen"


class StagingObservationDeviceReferenceType(str, Enum):
    Device = "Device"
    DeviceMetric = "DeviceMetric"


class StagingObservationBasedOnReferenceType(str, Enum):
    CarePlan = "CarePlan"
    DeviceRequest = "DeviceRequest"
    ImmunizationRecommendation = "ImmunizationRecommendation"
    MedicationRequest = "MedicationRequest"
    NutritionOrder = "NutritionOrder"
    ServiceRequest = "ServiceRequest"


class StagingObservationPartOfReferenceType(str, Enum):
    MedicationAdministration = "MedicationAdministration"
    MedicationDispense = "MedicationDispense"
    MedicationStatement = "MedicationStatement"
    Procedure = "Procedure"
    Immunization = "Immunization"
    ImagingStudy = "ImagingStudy"


class StagingObservationPerformerReferenceType(str, Enum):
    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    Organization = "Organization"
    CareTeam = "CareTeam"
    Patient = "Patient"
    RelatedPerson = "RelatedPerson"


class StagingObservationHasMemberReferenceType(str, Enum):
    Observation = "Observation"
    QuestionnaireResponse = "QuestionnaireResponse"
    MolecularSequence = "MolecularSequence"


class StagingObservationDerivedFromReferenceType(str, Enum):
    DocumentReference = "DocumentReference"
    ImagingStudy = "ImagingStudy"
    Media = "Media"
    QuestionnaireResponse = "QuestionnaireResponse"
    Observation = "Observation"
    MolecularSequence = "MolecularSequence"
