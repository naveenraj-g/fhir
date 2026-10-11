"""
FastAPI dependency bridge for PlanDefinitionService.

Translates the dependency-injector provider into a FastAPI Depends()-compatible
callable so route handlers can declare:
    service: PlanDefinitionService = Depends(get_plan_definition_service)
"""

from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.plan_definition_service import PlanDefinitionService


@inject
def get_plan_definition_service(
    service: PlanDefinitionService = Depends(Provide[Container.plan_definition.plan_definition_service]),
) -> PlanDefinitionService:
    """
    Resolve PlanDefinitionService from the DI container for use in route handlers.

    dependency-injector handles instantiation and wires the PlanDefinitionClient
    (and its underlying FhirClient) automatically.
    """
    return service
