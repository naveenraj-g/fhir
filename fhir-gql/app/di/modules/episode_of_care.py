"""
Dependency-injection sub-container for the EpisodeOfCare domain.

Wires EpisodeOfCareClient and EpisodeOfCareService as Factory providers so each request
receives a fresh, stateless instance.
"""

from dependency_injector import containers, providers

from app.fhir_client.episode_of_care import EpisodeOfCareClient
from app.services.episode_of_care_service import EpisodeOfCareService


class EpisodeOfCareContainer(containers.DeclarativeContainer):
    """
    DI sub-container for EpisodeOfCare resources.

    `core` is a DependenciesContainer placeholder replaced by the root Container
    at wiring time, giving access to `core.fhir_client`.
    """

    # Placeholder resolved by the root Container when this sub-container is mounted.
    core = providers.DependenciesContainer()

    # Domain-specific HTTP client for EpisodeOfCare endpoints on the fhir-server.
    episode_of_care_client = providers.Factory(
        EpisodeOfCareClient,
        fhir=core.fhir_client,
    )

    # Business logic service — sits between the router and EpisodeOfCareClient.
    episode_of_care_service = providers.Factory(
        EpisodeOfCareService,
        client=episode_of_care_client,
    )
