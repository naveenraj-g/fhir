"""
FastAPI dependency bridge for VitalsService.

Translates the dependency-injector provider into a FastAPI Depends()-compatible
callable so route handlers can declare:
    service: VitalsService = Depends(get_vitals_service)
"""

from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.vitals_service import VitalsService


@inject
def get_vitals_service(
    service: VitalsService = Depends(Provide[Container.vitals.vitals_service]),
) -> VitalsService:
    """
    Resolve VitalsService from the DI container for use in route handlers.

    dependency-injector handles instantiation and wires the Singleton
    VitalsClient (from CoreContainer) automatically.
    """
    return service
