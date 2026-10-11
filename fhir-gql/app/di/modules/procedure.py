"""
Dependency-injection sub-container for the Procedure domain.

Wires ProcedureClient and ProcedureService as Factory providers so each request
receives a fresh, stateless instance.
"""

from dependency_injector import containers, providers

from app.fhir_client.procedure import ProcedureClient
from app.services.procedure_service import ProcedureService


class ProcedureContainer(containers.DeclarativeContainer):
    """
    DI sub-container for Procedure resources.

    `core` is a DependenciesContainer placeholder replaced by the root Container
    at wiring time, giving access to `core.fhir_client`.
    """

    # Placeholder resolved by the root Container when this sub-container is mounted.
    core = providers.DependenciesContainer()

    # Domain-specific HTTP client for Procedure endpoints on the fhir-server.
    procedure_client = providers.Factory(
        ProcedureClient,
        fhir=core.fhir_client,
    )

    # Business logic service — sits between the router and ProcedureClient.
    procedure_service = providers.Factory(
        ProcedureService,
        client=procedure_client,
    )
