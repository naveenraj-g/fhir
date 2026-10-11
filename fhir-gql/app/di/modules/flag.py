"""
Dependency-injection sub-container for the Flag domain.

Wires FlagClient and FlagService as Factory providers so each request
receives a fresh, stateless instance.
"""

from dependency_injector import containers, providers

from app.fhir_client.flag import FlagClient
from app.services.flag_service import FlagService


class FlagContainer(containers.DeclarativeContainer):
    """
    DI sub-container for Flag resources.

    `core` is a DependenciesContainer placeholder replaced by the root Container
    at wiring time, giving access to `core.fhir_client`.
    """

    # Placeholder resolved by the root Container when this sub-container is mounted.
    core = providers.DependenciesContainer()

    # Domain-specific HTTP client for Flag endpoints on the fhir-server.
    flag_client = providers.Factory(
        FlagClient,
        fhir=core.fhir_client,
    )

    # Business logic service — sits between the router and FlagClient.
    flag_service = providers.Factory(
        FlagService,
        client=flag_client,
    )
