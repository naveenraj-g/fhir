"""
FastAPI dependency bridge for FlagService.

Translates the dependency-injector provider into a FastAPI Depends()-compatible
callable so route handlers can declare:
    service: FlagService = Depends(get_flag_service)
"""

from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.flag_service import FlagService


@inject
def get_flag_service(
    service: FlagService = Depends(Provide[Container.flag.flag_service]),
) -> FlagService:
    """
    Resolve FlagService from the DI container for use in route handlers.

    dependency-injector handles instantiation and wires the FlagClient
    (and its underlying FhirClient) automatically.
    """
    return service
