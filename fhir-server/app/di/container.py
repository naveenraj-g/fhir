from dependency_injector import containers, providers
from app.di.core import CoreContainer
from app.di.modules import PatientContainer, PractitionerContainer, EncounterContainer, AppointmentContainer, QuestionnaireResponseContainer, VitalsContainer


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
