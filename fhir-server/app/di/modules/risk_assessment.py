from dependency_injector import containers, providers

from app.repository.risk_assessment_repository import RiskAssessmentRepository
from app.services.risk_assessment_service import RiskAssessmentService


class RiskAssessmentContainer(containers.DeclarativeContainer):

    core = providers.DependenciesContainer()

    risk_assessment_repository = providers.Factory(
        RiskAssessmentRepository,
        session_factory=core.database.provided.session,
    )

    risk_assessment_service = providers.Factory(
        RiskAssessmentService,
        repository=risk_assessment_repository,
    )
