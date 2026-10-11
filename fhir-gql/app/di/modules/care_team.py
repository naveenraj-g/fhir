"""
Dependency-injection sub-container for the CareTeam domain.

Wires CareTeamClient and CareTeamService as Factory providers so each request
receives a fresh, stateless instance.
"""

from dependency_injector import containers, providers

from app.fhir_client.care_team import CareTeamClient
from app.services.care_team_service import CareTeamService


class CareTeamContainer(containers.DeclarativeContainer):
    """
    DI sub-container for CareTeam resources.

    `core` is a DependenciesContainer placeholder replaced by the root Container
    at wiring time, giving access to `core.fhir_client`.
    """

    # Placeholder resolved by the root Container when this sub-container is mounted.
    core = providers.DependenciesContainer()

    # Domain-specific HTTP client for CareTeam endpoints on the fhir-server.
    care_team_client = providers.Factory(
        CareTeamClient,
        fhir=core.fhir_client,
    )

    # Business logic service — sits between the router and CareTeamClient.
    care_team_service = providers.Factory(
        CareTeamService,
        client=care_team_client,
    )
