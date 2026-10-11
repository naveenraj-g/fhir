from dependency_injector.wiring import inject, Provide
from fastapi import Depends

from app.di.container import Container
from app.services.care_team_service import CareTeamService


@inject
def get_care_team_service(
    service: CareTeamService = Depends(Provide[Container.care_team.care_team_service]),
) -> CareTeamService:
    return service
