"""
FastAPI dependency bridge for ProcedureService.

Translates the dependency-injector provider into a FastAPI Depends()-compatible
callable so route handlers can declare:
    service: ProcedureService = Depends(get_procedure_service)
"""

from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.procedure_service import ProcedureService


@inject
def get_procedure_service(
    service: ProcedureService = Depends(Provide[Container.procedure.procedure_service]),
) -> ProcedureService:
    """
    Resolve ProcedureService from the DI container for use in route handlers.

    dependency-injector handles instantiation and wires the ProcedureClient
    (and its underlying FhirClient) automatically.
    """
    return service
