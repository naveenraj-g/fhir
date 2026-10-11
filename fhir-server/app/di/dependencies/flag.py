from dependency_injector.wiring import inject, Provide
from fastapi import Depends

from app.di.container import Container
from app.services.flag_service import FlagService


@inject
def get_flag_service(
    service: FlagService = Depends(Provide[Container.flag.flag_service]),
) -> FlagService:
    return service
