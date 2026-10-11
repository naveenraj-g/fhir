from dependency_injector import containers, providers

from app.repository.flag_repository import FlagRepository
from app.services.flag_service import FlagService


class FlagContainer(containers.DeclarativeContainer):

    core = providers.DependenciesContainer()

    flag_repository = providers.Factory(
        FlagRepository,
        session_factory=core.database.provided.session,
    )

    flag_service = providers.Factory(
        FlagService,
        repository=flag_repository,
    )
