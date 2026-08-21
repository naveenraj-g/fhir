from dependency_injector import containers, providers

from app.repository.staging_medical_record import StagingMedicalRecordRepository
from app.services.staging_medical_record import StagingMedicalRecordService


class StagingMedicalRecordContainer(containers.DeclarativeContainer):

    core = providers.DependenciesContainer()

    staging_medical_record_repository = providers.Factory(
        StagingMedicalRecordRepository,
        session_factory=core.database.provided.session,
    )

    staging_medical_record_service = providers.Factory(
        StagingMedicalRecordService,
        repository=staging_medical_record_repository,
    )
