"""
DI sub-container for the Slot domain.

Declares Factory providers for SlotClient and SlotService. Factory is used (not
Singleton) because both classes are stateless — a new instance per injection is
safe and avoids any risk of cross-request state leakage. The underlying FhirClient
is a Singleton regardless (provided by CoreContainer) so all resource types share
the same HTTP connection pool.

The `core` DependenciesContainer is a placeholder replaced by the root Container
at wiring time, giving this child container access to the shared FhirClient.
"""

from dependency_injector import containers, providers

from app.fhir_client.slot import SlotClient
from app.services.slot_service import SlotService


class SlotContainer(containers.DeclarativeContainer):
    """
    Dependency-injection sub-container for the Slot resource domain.

    Provides:
      - slot_client:  SlotClient wrapping the shared FhirClient singleton.
      - slot_service: SlotService containing all Slot business logic.

    Both are Factory providers — instantiated fresh per injection, which is
    correct for stateless service/client objects.
    """

    # Placeholder wired to the root Container's `core` sub-container at startup.
    # Gives access to core.fhir_client without creating a second FhirClient instance.
    core = providers.DependenciesContainer()

    # SlotClient — thin HTTP wrapper; shares the FhirClient singleton via core.
    slot_client = providers.Factory(
        SlotClient,
        fhir=core.fhir_client,
    )

    # SlotService — business logic layer; receives the client injected above.
    slot_service = providers.Factory(
        SlotService,
        client=slot_client,
    )
