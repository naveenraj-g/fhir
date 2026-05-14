from app.schemas.fhir.common import (
    FHIRAddress,
    FHIRBundle,
    FHIRBundleEntry,
    FHIRCoding,
    FHIRCodeableConcept,
    FHIRContactPoint,
    FHIRHumanName,
    FHIRIdentifier,
    FHIRPeriod,
    FHIRReference,
    PlainCoding,
    PlainIdentifier,
    PlainIdentifierType,
    PlainReasonCode,
)
from app.schemas.fhir.patient import (
    FHIRPatientSchema, FHIRPatientBundle, PaginatedPatientResponse,
    PlainPatientResponse, PlainPatientTelecom, PlainPatientAddress,
)
from app.schemas.fhir.practitioner import (
    FHIRPractitionerSchema, FHIRPractitionerBundle, PaginatedPractitionerResponse,
    PlainPractitionerResponse, PlainPractitionerTelecom, PlainPractitionerAddress, PlainQualification,
)
from app.schemas.fhir.encounter import (
    FHIREncounterSchema, FHIREncounterBundle, PaginatedEncounterResponse,
    PlainEncounterResponse, PlainEncounterBasedOn, PlainEncounterType,
    PlainEncounterParticipant, PlainEncounterDiagnosis, PlainEncounterLocation,
)
from app.schemas.fhir.appointment import (
    FHIRAppointmentSchema, FHIRAppointmentBundle, PaginatedAppointmentResponse,
    PlainAppointmentResponse, PlainAppointmentParticipant,
    PlainWeeklyTemplate, PlainMonthlyTemplate, PlainYearlyTemplate, PlainRecurrenceTemplate,
)
from app.schemas.fhir.questionnaire_response import (
    FHIRQuestionnaireResponseSchema, FHIRQuestionnaireResponseBundle, PaginatedQuestionnaireResponseResponse,
    PlainQuestionnaireResponse, PlainQRItem, PlainQRAnswer,
)

__all__ = [
    # FHIR common
    "FHIRAddress", "FHIRBundle", "FHIRBundleEntry", "FHIRCoding", "FHIRCodeableConcept",
    "FHIRContactPoint", "FHIRHumanName", "FHIRIdentifier", "FHIRPeriod", "FHIRReference",
    # Plain common
    "PlainCoding", "PlainIdentifier", "PlainIdentifierType", "PlainReasonCode",
    # Patient
    "FHIRPatientSchema", "FHIRPatientBundle", "PaginatedPatientResponse",
    "PlainPatientResponse", "PlainPatientTelecom", "PlainPatientAddress",
    # Practitioner
    "FHIRPractitionerSchema", "FHIRPractitionerBundle", "PaginatedPractitionerResponse",
    "PlainPractitionerResponse", "PlainPractitionerTelecom", "PlainPractitionerAddress", "PlainQualification",
    # Encounter
    "FHIREncounterSchema", "FHIREncounterBundle", "PaginatedEncounterResponse",
    "PlainEncounterResponse", "PlainEncounterBasedOn", "PlainEncounterType",
    "PlainEncounterParticipant", "PlainEncounterDiagnosis", "PlainEncounterLocation",
    # Appointment
    "FHIRAppointmentSchema", "FHIRAppointmentBundle", "PaginatedAppointmentResponse",
    "PlainAppointmentResponse", "PlainAppointmentParticipant",
    "PlainWeeklyTemplate", "PlainMonthlyTemplate", "PlainYearlyTemplate", "PlainRecurrenceTemplate",
    # QuestionnaireResponse
    "FHIRQuestionnaireResponseSchema", "FHIRQuestionnaireResponseBundle", "PaginatedQuestionnaireResponseResponse",
    "PlainQuestionnaireResponse", "PlainQRItem", "PlainQRAnswer",
]
