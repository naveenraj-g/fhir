from dependency_injector import containers, providers

from app.di.core import CoreContainer
from app.di.modules import StagingMedicalRecordContainer


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(packages=["app"])

    core = providers.Container(CoreContainer)

    staging_medical_record = providers.Container(
        StagingMedicalRecordContainer,
        core=core,
    )
