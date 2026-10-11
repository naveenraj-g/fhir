"""
Dependency-injection sub-container for the ActivityDefinition domain.

Wires ActivityDefinitionClient and ActivityDefinitionService as Factory providers so each request
receives a fresh, stateless instance.
"""

from dependency_injector import containers, providers

from app.fhir_client.activity_definition import ActivityDefinitionClient
from app.services.activity_definition_service import ActivityDefinitionService


class ActivityDefinitionContainer(containers.DeclarativeContainer):
    """
    DI sub-container for ActivityDefinition resources.

    `core` is a DependenciesContainer placeholder replaced by the root Container
    at wiring time, giving access to `core.fhir_client`.
    """

    # Placeholder resolved by the root Container when this sub-container is mounted.
    core = providers.DependenciesContainer()

    # Domain-specific HTTP client for ActivityDefinition endpoints on the fhir-server.
    activity_definition_client = providers.Factory(
        ActivityDefinitionClient,
        fhir=core.fhir_client,
    )

    # Business logic service — sits between the router and ActivityDefinitionClient.
    activity_definition_service = providers.Factory(
        ActivityDefinitionService,
        client=activity_definition_client,
    )
