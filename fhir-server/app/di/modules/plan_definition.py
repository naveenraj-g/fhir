from dependency_injector import containers, providers

from app.repository.plan_definition_repository import PlanDefinitionRepository
from app.services.plan_definition_service import PlanDefinitionService


class PlanDefinitionContainer(containers.DeclarativeContainer):

    core = providers.DependenciesContainer()

    plan_definition_repository = providers.Factory(
        PlanDefinitionRepository,
        session_factory=core.database.provided.session,
    )

    plan_definition_service = providers.Factory(
        PlanDefinitionService,
        repository=plan_definition_repository,
    )
