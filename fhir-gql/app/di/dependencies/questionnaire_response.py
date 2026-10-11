"""
FastAPI dependency bridge for QuestionnaireResponseService.

Translates the dependency-injector provider into a FastAPI Depends()-compatible
callable so route handlers can declare:
    service: QuestionnaireResponseService = Depends(get_questionnaire_response_service)
"""

from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.questionnaire_response_service import QuestionnaireResponseService


@inject
def get_questionnaire_response_service(
    service: QuestionnaireResponseService = Depends(Provide[Container.questionnaire_response.questionnaire_response_service]),
) -> QuestionnaireResponseService:
    """
    Resolve QuestionnaireResponseService from the DI container for use in route handlers.

    dependency-injector handles instantiation and wires the QuestionnaireResponseClient
    (and its underlying FhirClient) automatically.
    """
    return service
