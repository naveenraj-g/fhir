"""
Root dependency-injection container for the entire application.

This module defines the top-level `Container` class using the dependency-injector
library's declarative container pattern. It acts as the composition root — every
service, repository, and client in the application is wired here so that:
  - Dependencies are assembled once at startup rather than on every request.
  - The dependency graph is explicit and testable: replacing a provider (e.g. with
    a mock) requires changing one line here rather than hunting call sites.
  - FastAPI route handlers receive pre-built service instances via Depends() without
    knowing how those instances are constructed.

Wiring:
    WiringConfiguration(packages=["app"]) tells dependency-injector to scan every
    module under the `app` package at startup and inject providers wherever it finds
    the @inject decorator combined with Provide[Container.*] type hints. This avoids
    manually listing every injected module.

Container hierarchy:
    Container (root)
    ├── core               →  CoreContainer               (shared infrastructure: FHIR HTTP client)
    ├── organization       →  OrganizationContainer       (Organisation CRUD service + client)
    ├── location           →  LocationContainer           (Location CRUD service + client)
    ├── healthcare_service →  HealthcareServiceContainer  (HealthcareService CRUD service + client)
    ├── schedule           →  ScheduleContainer           (Schedule CRUD service + client)
    ├── slot               →  SlotContainer               (Slot CRUD service + client)
    ├── practitioner       →  PractitionerContainer       (Practitioner CRUD service + client)
    └── practitioner_role  →  PractitionerRoleContainer   (PractitionerRole CRUD service + client)
"""

from dependency_injector import containers, providers

from app.di.core import CoreContainer
from app.di.modules import (
    HealthcareServiceContainer,
    LocationContainer,
    OrganizationContainer,
    PractitionerContainer,
    PractitionerRoleContainer,
    ScheduleContainer,
    SlotContainer,
)


class Container(containers.DeclarativeContainer):
    """
    Application-wide DI container. Instantiated once in app.main and attached to
    `app.container` so it survives for the full process lifetime.

    Sub-containers are declared as `providers.Container(...)` which creates a
    lazily-initialised child container. Passing `core=core` to each domain container
    wires the shared CoreContainer instance into the child so its providers
    (e.g. fhir_client) can be referenced via `core.fhir_client` inside the child.

    Container hierarchy:
        Container (root)
        ├── core         → CoreContainer          (shared infrastructure: FHIR HTTP client)
        ├── organization → OrganizationContainer  (Organisation CRUD service + client)
        └── location     → LocationContainer      (Location CRUD service + client)
    """

    # Scans all modules under the `app` package for @inject-decorated functions
    # and automatically resolves their Provide[Container.*] dependencies at startup.
    wiring_config = containers.WiringConfiguration(packages=["app"])

    # Shared infrastructure container — holds the singleton FHIR HTTP client.
    core = providers.Container(CoreContainer)

    # Domain container for Organisation resources.
    # Receives `core` so it can depend on the shared FHIR client without creating
    # a second instance (Singleton guarantees one client across the whole app).
    organization = providers.Container(
        OrganizationContainer,
        core=core,
    )

    # Domain container for Location resources.
    # Follows the same pattern as OrganizationContainer — shares the CoreContainer
    # FhirClient singleton so all resource types use the same connection pool.
    location = providers.Container(
        LocationContainer,
        core=core,
    )

    # Domain container for HealthcareService resources.
    healthcare_service = providers.Container(
        HealthcareServiceContainer,
        core=core,
    )

    # Domain container for Schedule resources.
    schedule = providers.Container(
        ScheduleContainer,
        core=core,
    )

    # Domain container for Slot resources.
    # Slots are bookable time windows that belong to a Schedule. Shares the
    # CoreContainer FhirClient singleton so all resource types use the same
    # connection pool.
    slot = providers.Container(
        SlotContainer,
        core=core,
    )

    # Domain container for Practitioner resources.
    # A Practitioner is a person directly or indirectly involved in healthcare.
    practitioner = providers.Container(
        PractitionerContainer,
        core=core,
    )

    # Domain container for PractitionerRole resources.
    # A PractitionerRole describes the role a Practitioner plays at an Organisation.
    practitioner_role = providers.Container(
        PractitionerRoleContainer,
        core=core,
    )
