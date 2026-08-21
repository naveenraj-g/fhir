from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.staging_medical_record import StagingMedicalRecordService


@inject
def get_staging_medical_record_service(
    service: StagingMedicalRecordService = Depends(
        Provide[Container.staging_medical_record.staging_medical_record_service]
    ),
) -> StagingMedicalRecordService:
    return service
