"""
FastAPI dependency bridge for CareTeamService.

Translates the dependency-injector provider into a FastAPI Depends()-compatible
callable so route handlers can declare:
    service: CareTeamService = Depends(get_care_team_service)
"""

from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.care_team_service import CareTeamService


@inject
def get_care_team_service(
    service: CareTeamService = Depends(Provide[Container.care_team.care_team_service]),
) -> CareTeamService:
    """
    Resolve CareTeamService from the DI container for use in route handlers.

    dependency-injector handles instantiation and wires the CareTeamClient
    (and its underlying FhirClient) automatically.
    """
    return service
