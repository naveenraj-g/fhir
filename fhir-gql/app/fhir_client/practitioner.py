"""
FHIR client for Practitioner resources.

Thin wrapper around the shared FhirClient that knows the fhir-server path.
No business logic lives here — all validation and rules belong in PractitionerService.

A Practitioner is a person who is directly or indirectly involved in the
provisioning of healthcare. This resource stores the practitioner's demographics
(name, gender, birthDate) and credentials (qualification, identifier).
Child records (names, identifiers, telecom, address, photo, qualification,
communication) are managed via separate sub-routes on the fhir-server.

Reference: https://hl7.org/fhir/R4/practitioner.html
"""

from app.auth.models import AuthUser
from app.fhir_client.client import FhirClient

# Confirmed in fhir-server routers/__init__.py: prefix="/practitioners"
_PATH = "/practitioners"


class PractitionerClient:
    """
    Domain-specific HTTP client for Practitioner resources.

    Delegates every request to the shared FhirClient singleton, which handles
    authentication headers, base-URL resolution, and error propagation.
    The `accept` parameter is threaded through all body-returning methods so
    the caller can request plain JSON or FHIR R4 format.
    """

    def __init__(self, fhir: FhirClient) -> None:
        """
        Initialise with a shared FhirClient injected by the DI container.

        Args:
            fhir: The singleton FhirClient — owns the httpx session and base URL config.
        """
        self._fhir = fhir

    async def create(self, data: dict, actor: AuthUser, accept: str | None = None) -> dict:
        """
        POST /practitioners — create a new Practitioner resource.

        FhirClient.post() stamps `created_by: actor.sub` automatically.
        The payload should only contain top-level scalar fields (active, gender,
        birth_date, deceased_*) — child arrays are not accepted at creation time.

        Args:
            data:   Serialised PractitionerCreateSchema (exclude_none=True applied).
            actor:  Authenticated caller — used by FhirClient to stamp created_by.
            accept: Content-type preference forwarded to the fhir-server.

        Returns:
            The newly created Practitioner as a dict.
        """
        return await self._fhir.post(_PATH, data, actor, accept=accept)

    async def get_by_id(self, resource_id: int, accept: str | None = None) -> dict:
        """
        GET /practitioners/{resource_id} — fetch a single Practitioner by integer ID.

        Args:
            resource_id: The practitioner's primary key on the fhir-server.
            accept:      Content-type preference forwarded to the fhir-server.

        Returns:
            The Practitioner resource dict with all child arrays populated.
        """
        return await self._fhir.get(f"{_PATH}/{resource_id}", accept=accept)

    async def list(self, accept: str | None = None, **params) -> dict:
        """
        GET /practitioners — list Practitioners with optional filters.

        Strips None values from **params to avoid sending null query strings.

        Supported params: family_name, given_name, active, user_id, org_id,
        limit, offset.

        Args:
            accept:   Content-type preference forwarded to the fhir-server.
            **params: Arbitrary keyword filters; None values are dropped.

        Returns:
            Paginated plain JSON or FHIR Bundle depending on `accept`.
        """
        clean = {k: v for k, v in params.items() if v is not None}
        return await self._fhir.get(_PATH, params=clean, accept=accept)

    async def patch(self, resource_id: int, data: dict, actor: AuthUser, accept: str | None = None) -> dict:
        """
        PATCH /practitioners/{resource_id} — partially update a Practitioner.

        FhirClient.patch() stamps `updated_by: actor.sub` automatically.
        Only scalar fields are patchable (active, gender, birth_date, deceased_*).
        Child arrays are managed via separate sub-routes on the fhir-server.

        Args:
            resource_id: The practitioner's integer primary key.
            data:        Serialised PractitionerPatchSchema fields to update.
            actor:       Authenticated caller — used by FhirClient to stamp updated_by.
            accept:      Content-type preference forwarded to the fhir-server.

        Returns:
            The updated Practitioner resource dict.
        """
        return await self._fhir.patch(f"{_PATH}/{resource_id}", data, actor, accept=accept)

    async def delete(self, resource_id: int) -> None:
        """
        DELETE /practitioners/{resource_id} — permanently remove a Practitioner.

        No `accept` parameter — 204 has no response body.

        Args:
            resource_id: The practitioner's integer primary key to delete.
        """
        await self._fhir.delete(f"{_PATH}/{resource_id}")
