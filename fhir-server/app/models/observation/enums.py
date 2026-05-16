from enum import Enum


class ObservationStatus(str, Enum):
    REGISTERED = "registered"
    PRELIMINARY = "preliminary"
    FINAL = "final"
    AMENDED = "amended"
    CORRECTED = "corrected"
    CANCELLED = "cancelled"
    ENTERED_IN_ERROR = "entered-in-error"
    UNKNOWN = "unknown"


class ObservationSubjectReferenceType(str, Enum):
    PATIENT = "Patient"
    GROUP = "Group"
    DEVICE = "Device"
    LOCATION = "Location"


class ObservationEncounterReferenceType(str, Enum):
    ENCOUNTER = "Encounter"


class ObservationSpecimenReferenceType(str, Enum):
    SPECIMEN = "Specimen"


class ObservationDeviceReferenceType(str, Enum):
    DEVICE = "Device"
    DEVICE_METRIC = "DeviceMetric"


class ObservationBasedOnReferenceType(str, Enum):
    CARE_PLAN = "CarePlan"
    DEVICE_REQUEST = "DeviceRequest"
    IMMUNIZATION_RECOMMENDATION = "ImmunizationRecommendation"
    MEDICATION_REQUEST = "MedicationRequest"
    NUTRITION_ORDER = "NutritionOrder"
    SERVICE_REQUEST = "ServiceRequest"


class ObservationPartOfReferenceType(str, Enum):
    MEDICATION_ADMINISTRATION = "MedicationAdministration"
    MEDICATION_DISPENSE = "MedicationDispense"
    MEDICATION_STATEMENT = "MedicationStatement"
    PROCEDURE = "Procedure"
    IMMUNIZATION = "Immunization"
    IMAGING_STUDY = "ImagingStudy"


class ObservationPerformerReferenceType(str, Enum):
    PRACTITIONER = "Practitioner"
    PRACTITIONER_ROLE = "PractitionerRole"
    ORGANIZATION = "Organization"
    CARE_TEAM = "CareTeam"
    PATIENT = "Patient"
    RELATED_PERSON = "RelatedPerson"


class ObservationHasMemberReferenceType(str, Enum):
    OBSERVATION = "Observation"
    QUESTIONNAIRE_RESPONSE = "QuestionnaireResponse"
    MOLECULAR_SEQUENCE = "MolecularSequence"


class ObservationDerivedFromReferenceType(str, Enum):
    DOCUMENT_REFERENCE = "DocumentReference"
    IMAGING_STUDY = "ImagingStudy"
    MEDIA = "Media"
    QUESTIONNAIRE_RESPONSE = "QuestionnaireResponse"
    OBSERVATION = "Observation"
    MOLECULAR_SEQUENCE = "MolecularSequence"
