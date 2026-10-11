from dependency_injector import containers, providers

from app.repository.questionnaire_repository import QuestionnaireRepository
from app.services.questionnaire_service import QuestionnaireService


class QuestionnaireContainer(containers.DeclarativeContainer):

    core = providers.DependenciesContainer()

    questionnaire_repository = providers.Factory(
        QuestionnaireRepository,
        session_factory=core.database.provided.session,
    )

    questionnaire_service = providers.Factory(
        QuestionnaireService,
        repository=questionnaire_repository,
    )
