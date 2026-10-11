"""
FastAPI dependency bridge for ActivityDefinitionService.

Translates the dependency-injector provider into a FastAPI Depends()-compatible
callable so route handlers can declare:
    service: ActivityDefinitionService = Depends(get_activity_definition_service)
"""

from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.activity_definition_service import ActivityDefinitionService


@inject
def get_activity_definition_service(
    service: ActivityDefinitionService = Depends(Provide[Container.activity_definition.activity_definition_service]),
) -> ActivityDefinitionService:
    """
    Resolve ActivityDefinitionService from the DI container for use in route handlers.

    dependency-injector handles instantiation and wires the ActivityDefinitionClient
    (and its underlying FhirClient) automatically.
    """
    return service
