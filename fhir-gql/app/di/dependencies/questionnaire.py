"""
FastAPI dependency bridge for QuestionnaireService.

Translates the dependency-injector provider into a FastAPI Depends()-compatible
callable so route handlers can declare:
    service: QuestionnaireService = Depends(get_questionnaire_service)
"""

from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.questionnaire_service import QuestionnaireService


@inject
def get_questionnaire_service(
    service: QuestionnaireService = Depends(Provide[Container.questionnaire.questionnaire_service]),
) -> QuestionnaireService:
    """
    Resolve QuestionnaireService from the DI container for use in route handlers.

    dependency-injector handles instantiation and wires the QuestionnaireClient
    (and its underlying FhirClient) automatically.
    """
    return service
