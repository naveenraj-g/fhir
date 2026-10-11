"""
Dependency-injection sub-container for the Task domain.

Wires TaskClient and TaskService as Factory providers so each request
receives a fresh, stateless instance.
"""

from dependency_injector import containers, providers

from app.fhir_client.task import TaskClient
from app.services.task_service import TaskService


class TaskContainer(containers.DeclarativeContainer):
    """
    DI sub-container for Task resources.

    `core` is a DependenciesContainer placeholder replaced by the root Container
    at wiring time, giving access to `core.fhir_client`.
    """

    # Placeholder resolved by the root Container when this sub-container is mounted.
    core = providers.DependenciesContainer()

    # Domain-specific HTTP client for Task endpoints on the fhir-server.
    task_client = providers.Factory(
        TaskClient,
        fhir=core.fhir_client,
    )

    # Business logic service — sits between the router and TaskClient.
    task_service = providers.Factory(
        TaskService,
        client=task_client,
    )
