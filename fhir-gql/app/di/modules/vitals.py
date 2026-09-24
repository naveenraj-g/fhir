"""
Dependency-injection sub-container for the Vitals domain.

Wires VitalsService as a Factory provider so each request receives a fresh,
stateless instance. Unlike other domain containers, there is no domain-specific
client Factory here — VitalsClient itself is a Singleton registered directly in
CoreContainer (see app/di/core.py) because it owns its own httpx connection pool
against a base URL distinct from the shared FhirClient's.
"""

from dependency_injector import containers, providers

from app.services.vitals_service import VitalsService


class VitalsContainer(containers.DeclarativeContainer):
    """
    DI sub-container for Vitals resources.

    `core` is a DependenciesContainer placeholder replaced by the root Container
    at wiring time, giving access to `core.vitals_client`.
    """

    # Placeholder resolved by the root Container when this sub-container is mounted.
    core = providers.DependenciesContainer()

    # Business logic service — sits between the router and the Singleton VitalsClient.
    vitals_service = providers.Factory(
        VitalsService,
        client=core.vitals_client,
    )
