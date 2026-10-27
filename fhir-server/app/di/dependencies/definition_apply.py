from dependency_injector.wiring import inject, Provide
from fastapi import Depends

from app.di.container import Container
from app.services.definition_apply_service import DefinitionApplyService


@inject
def get_definition_apply_service(
    service: DefinitionApplyService = Depends(Provide[Container.definition_apply.definition_apply_service]),
) -> DefinitionApplyService:
    return service
