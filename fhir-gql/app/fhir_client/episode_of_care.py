"""
FHIR client for EpisodeOfCare resources.

Thin wrapper around the shared FhirClient that knows the fhir-server path for
EpisodesOfCare. No business logic lives here — all validation and rules belong in
EpisodeOfCareService.

An EpisodeOfCare groups the encounters and care that relate to a patient's
particular health condition or care programme: its status (and status history),
type, diagnoses, period, managing organization, care manager, referral requests,
care team and accounts.

Reference: https://www.hl7.org/fhir/R4/episodeofcare.html
"""

from app.auth.models import AuthUser
from app.fhir_client.client import FhirClient

# Confirmed in fhir-server routers prefix (app/routers/__init__.py: "/episode-of-cares").
_PATH = "/episode-of-cares"


class EpisodeOfCareClient:
    """
    Domain-specific HTTP client for EpisodeOfCare resources.

    Delegates every request to the shared FhirClient singleton, which handles
    authentication headers, base-URL resolution, and error propagation.
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
        POST /episode-of-cares — create a new EpisodeOfCare with its child lists
        (identifiers, status_history, types, diagnoses, referral_requests, team, accounts).

        Args:
            data:   Serialised EpisodeOfCareCreateSchema (exclude_none=True, mode="json").
            actor:  Authenticated caller — FhirClient stamps created_by from actor.sub.
            accept: Content-type preference forwarded to the fhir-server.

        Returns:
            The newly created EpisodeOfCare as a dict (plain JSON or FHIR R4).
        """
        return await self._fhir.post(_PATH, data, actor, accept=accept)

    async def get_by_id(self, resource_id: int, accept: str | None = None) -> dict:
        """
        GET /episode-of-cares/{resource_id} — fetch one EpisodeOfCare by public ID.

        Args:
            resource_id: The public integer episode_of_care_id.
            accept:      Content-type preference forwarded to the fhir-server.

        Returns:
            The EpisodeOfCare dict with its child lists populated.
        """
        return await self._fhir.get(f"{_PATH}/{resource_id}", accept=accept)

    async def list(self, accept: str | None = None, **params) -> dict:
        """
        GET /episode-of-cares — search with the FHIR R4 search parameters.

        Strips None values (and empty lists) from **params before forwarding. Hyphenated and
        underscore-prefixed names (`care-manager`, `incoming-referral`, `_id`, `_lastUpdated`)
        are passed through verbatim by unpacking a dict (`**{"care-manager": "Practitioner/1"}`).
        List values (`date`, `_lastUpdated`) are sent as repeated query keys, which the
        fhir-server treats as AND.

        Supported params: _id, identifier, status, type, patient, organization, care-manager,
        condition, incoming-referral, date, _lastUpdated, user_id, org_id (mandatory), limit, offset.

        Args:
            accept:   Content-type preference forwarded to the fhir-server.
            **params: Arbitrary keyword filters; None values (and empty lists) are dropped.

        Returns:
            Paginated plain JSON or FHIR Bundle depending on `accept`.
        """
        clean = {k: v for k, v in params.items() if v is not None and v != []}
        return await self._fhir.get(_PATH, params=clean, accept=accept)

    async def patch(self, resource_id: int, data: dict, actor: AuthUser, accept: str | None = None) -> dict:
        """
        PATCH /episode-of-cares/{resource_id} — partially update fields and/or replace child lists.

        Args:
            resource_id: The public integer episode_of_care_id.
            data:        Serialised EpisodeOfCarePatchSchema (exclude_none=True, mode="json").
            actor:       Authenticated caller — FhirClient stamps updated_by.
            accept:      Content-type preference forwarded to the fhir-server.

        Returns:
            The updated EpisodeOfCare resource dict.
        """
        return await self._fhir.patch(f"{_PATH}/{resource_id}", data, actor, accept=accept)

    async def delete(self, resource_id: int) -> None:
        """
        DELETE /episode-of-cares/{resource_id} — permanently remove an EpisodeOfCare.

        The fhir-server cascades the delete to every child row.

        Args:
            resource_id: The public integer episode_of_care_id to delete.
        """
        await self._fhir.delete(f"{_PATH}/{resource_id}")
