from dependency_injector import containers, providers
from app.di.core import CoreContainer
from app.di.modules import PatientContainer, PractitionerContainer, EncounterContainer, AppointmentContainer, QuestionnaireResponseContainer, VitalsContainer, ConditionContainer, ServiceRequestContainer, DeviceRequestContainer, DiagnosticReportContainer, MedicationRequestContainer, ObservationContainer, OrganizationContainer, ProcedureContainer


class Container(containers.DeclarativeContainer):

    wiring_config = containers.WiringConfiguration(packages=["app"])

    core = providers.Container(CoreContainer)

    patient = providers.Container(
        PatientContainer,
        core=core,
    )

    practitioner = providers.Container(
        PractitionerContainer,
        core=core,
    )

    encounter = providers.Container(
        EncounterContainer,
        core=core,
    )

    appointment = providers.Container(
        AppointmentContainer,
        core=core,
    )

    questionnaire_response = providers.Container(
        QuestionnaireResponseContainer,
        core=core,
    )

    vitals = providers.Container(
        VitalsContainer,
        core=core,
    )

    condition = providers.Container(
        ConditionContainer,
        core=core,
    )

    service_request = providers.Container(
        ServiceRequestContainer,
        core=core,
    )

    device_request = providers.Container(
        DeviceRequestContainer,
        core=core,
    )

    diagnostic_report = providers.Container(
        DiagnosticReportContainer,
        core=core,
    )

    medication_request = providers.Container(
        MedicationRequestContainer,
        core=core,
    )

    observation = providers.Container(
        ObservationContainer,
        core=core,
    )

    organization = providers.Container(
        OrganizationContainer,
        core=core,
    )

    procedure = providers.Container(
        ProcedureContainer,
        core=core,
    )

    # Singleton database
    # database = providers.Singleton(
    #     Database,
    #     db_url=settings.FHIR_DATABASE_URL,
    # )

    # # Repository
    # patient_repository = providers.Factory(
    #     PatientRepository,
    #     session_factory=database.provided.session,
    # )
    # # Service
    # patient_service = providers.Factory(
    #     PatientService,
    #     repository=patient_repository,
    # )
