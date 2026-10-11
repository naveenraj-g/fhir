from dependency_injector.wiring import inject, Provide
from fastapi import Depends

from app.di.container import Container
from app.services.questionnaire_service import QuestionnaireService


@inject
def get_questionnaire_service(
    service: QuestionnaireService = Depends(Provide[Container.questionnaire.questionnaire_service]),
) -> QuestionnaireService:
    return service
