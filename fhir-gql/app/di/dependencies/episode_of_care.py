"""
FastAPI dependency bridge for EpisodeOfCareService.

Translates the dependency-injector provider into a FastAPI Depends()-compatible
callable so route handlers can declare:
    service: EpisodeOfCareService = Depends(get_episode_of_care_service)
"""

from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.episode_of_care_service import EpisodeOfCareService


@inject
def get_episode_of_care_service(
    service: EpisodeOfCareService = Depends(Provide[Container.episode_of_care.episode_of_care_service]),
) -> EpisodeOfCareService:
    """
    Resolve EpisodeOfCareService from the DI container for use in route handlers.

    dependency-injector handles instantiation and wires the EpisodeOfCareClient
    (and its underlying FhirClient) automatically.
    """
    return service
