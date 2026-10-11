"""
FastAPI dependency bridge for CarePlanService.

Translates the dependency-injector provider into a FastAPI Depends()-compatible
callable so route handlers can declare:
    service: CarePlanService = Depends(get_care_plan_service)
"""

from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.care_plan_service import CarePlanService


@inject
def get_care_plan_service(
    service: CarePlanService = Depends(Provide[Container.care_plan.care_plan_service]),
) -> CarePlanService:
    """
    Resolve CarePlanService from the DI container for use in route handlers.

    dependency-injector handles instantiation and wires the CarePlanClient
    (and its underlying FhirClient) automatically.
    """
    return service
