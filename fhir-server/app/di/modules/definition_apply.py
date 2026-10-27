from dependency_injector import containers, providers

from app.repository.activity_definition_repository import ActivityDefinitionRepository
from app.repository.service_request_repository import ServiceRequestRepository
from app.services.definition_apply_service import DefinitionApplyService


class DefinitionApplyContainer(containers.DeclarativeContainer):

    core = providers.DependenciesContainer()

    activity_definition_repository = providers.Factory(
        ActivityDefinitionRepository,
        session_factory=core.database.provided.session,
    )

    service_request_repository = providers.Factory(
        ServiceRequestRepository,
        session_factory=core.database.provided.session,
    )

    definition_apply_service = providers.Factory(
        DefinitionApplyService,
        activity_definition_repository=activity_definition_repository,
        service_request_repository=service_request_repository,
    )
