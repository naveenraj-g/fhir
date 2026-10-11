from dependency_injector import containers, providers

from app.repository.care_team_repository import CareTeamRepository
from app.services.care_team_service import CareTeamService


class CareTeamContainer(containers.DeclarativeContainer):

    core = providers.DependenciesContainer()

    care_team_repository = providers.Factory(
        CareTeamRepository,
        session_factory=core.database.provided.session,
    )

    care_team_service = providers.Factory(
        CareTeamService,
        repository=care_team_repository,
    )
