"""
DI sub-container for the Slot domain.

Declares Factory providers for SlotClient and SlotService. Factory is used
(not Singleton) because both classes are stateless — a new instance per
injection is safe and avoids cross-request state leakage. The underlying
FhirClient is a Singleton (provided by CoreContainer) so all resource types
share the same HTTP connection pool.

SlotService.generate() now forwards directly to the fhir-server's own
POST /slots/generate, so SlotService no longer depends on ScheduleClient or
PractitionerRoleClient (those remain wired in their own containers for their
own resource routes).

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
      - slot_client:  SlotClient — CRUD and generation operations for Slot resources.
      - slot_service: SlotService — all Slot business logic.

    Both are Factory providers — instantiated fresh per injection, correct for
    stateless service/client objects.
    """

    # Placeholder wired to the root Container's `core` sub-container at startup.
    # Gives access to core.fhir_client without creating a second FhirClient instance.
    core = providers.DependenciesContainer()

    # SlotClient — thin HTTP wrapper for Slot CRUD + generate; shares the FhirClient singleton.
    slot_client = providers.Factory(
        SlotClient,
        fhir=core.fhir_client,
    )

    # SlotService — business logic layer.
    slot_service = providers.Factory(
        SlotService,
        client=slot_client,
    )
