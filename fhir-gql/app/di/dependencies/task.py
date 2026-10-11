"""
FastAPI dependency bridge for TaskService.

Translates the dependency-injector provider into a FastAPI Depends()-compatible
callable so route handlers can declare:
    service: TaskService = Depends(get_task_service)
"""

from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.task_service import TaskService


@inject
def get_task_service(
    service: TaskService = Depends(Provide[Container.task.task_service]),
) -> TaskService:
    """
    Resolve TaskService from the DI container for use in route handlers.

    dependency-injector handles instantiation and wires the TaskClient
    (and its underlying FhirClient) automatically.
    """
    return service
