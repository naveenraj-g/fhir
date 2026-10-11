"""
Dependency-injection sub-container for the CarePlan domain.

Wires CarePlanClient and CarePlanService as Factory providers so each request
receives a fresh, stateless instance.
"""

from dependency_injector import containers, providers

from app.fhir_client.care_plan import CarePlanClient
from app.services.care_plan_service import CarePlanService


class CarePlanContainer(containers.DeclarativeContainer):
    """
    DI sub-container for CarePlan resources.

    `core` is a DependenciesContainer placeholder replaced by the root Container
    at wiring time, giving access to `core.fhir_client`.
    """

    # Placeholder resolved by the root Container when this sub-container is mounted.
    core = providers.DependenciesContainer()

    # Domain-specific HTTP client for CarePlan endpoints on the fhir-server.
    care_plan_client = providers.Factory(
        CarePlanClient,
        fhir=core.fhir_client,
    )

    # Business logic service — sits between the router and CarePlanClient.
    care_plan_service = providers.Factory(
        CarePlanService,
        client=care_plan_client,
    )
