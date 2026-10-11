"""
Dependency-injection sub-container for the PlanDefinition domain.

Wires PlanDefinitionClient and PlanDefinitionService as Factory providers so each request
receives a fresh, stateless instance.
"""

from dependency_injector import containers, providers

from app.fhir_client.plan_definition import PlanDefinitionClient
from app.services.plan_definition_service import PlanDefinitionService


class PlanDefinitionContainer(containers.DeclarativeContainer):
    """
    DI sub-container for PlanDefinition resources.

    `core` is a DependenciesContainer placeholder replaced by the root Container
    at wiring time, giving access to `core.fhir_client`.
    """

    # Placeholder resolved by the root Container when this sub-container is mounted.
    core = providers.DependenciesContainer()

    # Domain-specific HTTP client for PlanDefinition endpoints on the fhir-server.
    plan_definition_client = providers.Factory(
        PlanDefinitionClient,
        fhir=core.fhir_client,
    )

    # Business logic service — sits between the router and PlanDefinitionClient.
    plan_definition_service = providers.Factory(
        PlanDefinitionService,
        client=plan_definition_client,
    )
