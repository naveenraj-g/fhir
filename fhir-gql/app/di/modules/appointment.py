"""
Dependency-injection sub-container for the Appointment domain.

Wires AppointmentClient and AppointmentService as Factory providers so each
request receives a fresh, stateless instance. The shared FhirClient Singleton
(in CoreContainer) is reused across all domain containers.
"""

from dependency_injector import containers, providers

from app.fhir_client.appointment import AppointmentClient
from app.services.appointment_service import AppointmentService


class AppointmentContainer(containers.DeclarativeContainer):
    """
    DI sub-container for Appointment resources.

    `core` is a DependenciesContainer placeholder replaced by the root Container
    at wiring time, giving access to `core.fhir_client` (the Singleton HTTP client).

    Both providers are Factory (not Singleton) — AppointmentClient and
    AppointmentService are stateless, so per-injection creation is safe and
    avoids any cross-request state leakage.
    """

    # Placeholder resolved by the root Container when this sub-container is mounted.
    core = providers.DependenciesContainer()

    # Domain-specific HTTP client for Appointment endpoints on the fhir-server.
    appointment_client = providers.Factory(
        AppointmentClient,
        fhir=core.fhir_client,
    )

    # Business logic service — sits between the router and the client.
    appointment_service = providers.Factory(
        AppointmentService,
        client=appointment_client,
    )
