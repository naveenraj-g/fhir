from app.di.modules.appointment import AppointmentContainer
from app.di.modules.condition import ConditionContainer
from app.di.modules.diagnostic_report import DiagnosticReportContainer
from app.di.modules.document_reference import DocumentReferenceContainer
from app.di.modules.encounter import EncounterContainer
from app.di.modules.healthcare_service import HealthcareServiceContainer
from app.di.modules.location import LocationContainer
from app.di.modules.medication_request import MedicationRequestContainer
from app.di.modules.observation import ObservationContainer
from app.di.modules.organization import OrganizationContainer
from app.di.modules.patient import PatientContainer
from app.di.modules.practitioner import PractitionerContainer
from app.di.modules.practitioner_role import PractitionerRoleContainer
from app.di.modules.procedure import ProcedureContainer
from app.di.modules.questionnaire import QuestionnaireContainer
from app.di.modules.questionnaire_response import QuestionnaireResponseContainer
from app.di.modules.risk_assessment import RiskAssessmentContainer
from app.di.modules.flag import FlagContainer
from app.di.modules.plan_definition import PlanDefinitionContainer
from app.di.modules.care_plan import CarePlanContainer
from app.di.modules.care_team import CareTeamContainer
from app.di.modules.activity_definition import ActivityDefinitionContainer
from app.di.modules.task import TaskContainer
from app.di.modules.episode_of_care import EpisodeOfCareContainer
from app.di.modules.schedule import ScheduleContainer
from app.di.modules.service_request import ServiceRequestContainer
from app.di.modules.slot import SlotContainer
from app.di.modules.vitals import VitalsContainer

__all__ = [
    "OrganizationContainer",
    "LocationContainer",
    "HealthcareServiceContainer",
    "ScheduleContainer",
    "SlotContainer",
    "PractitionerContainer",
    "PractitionerRoleContainer",
    "PatientContainer",
    "AppointmentContainer",
    "EncounterContainer",
    "ServiceRequestContainer",
    "MedicationRequestContainer",
    "ObservationContainer",
    "ConditionContainer",
    "DiagnosticReportContainer",
    "DocumentReferenceContainer",
    "VitalsContainer",
    "ProcedureContainer",
    "QuestionnaireContainer",
    "QuestionnaireResponseContainer",
    "RiskAssessmentContainer",
    "FlagContainer",
    "PlanDefinitionContainer",
    "CarePlanContainer",
    "CareTeamContainer",
    "ActivityDefinitionContainer",
    "TaskContainer",
    "EpisodeOfCareContainer",
]
