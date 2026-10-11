"""
FHIR client for CareTeam resources.

Thin wrapper around the shared FhirClient that knows the fhir-server path for
CareTeams. No business logic lives here — all validation and rules belong in
CareTeamService.

A CareTeam lists the people and organizations planned to participate in
coordinating a patient's care: participants with roles, reasons for the team,
managing organizations and a central contact point.

Reference: https://www.hl7.org/fhir/R4/careteam.html
"""

from app.auth.models import AuthUser
from app.fhir_client.client import FhirClient

# Confirmed in fhir-server routers prefix (app/routers/__init__.py: "/care-teams").
_PATH = "/care-teams"


class CareTeamClient:
    """
    Domain-specific HTTP client for CareTeam resources.

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
        POST /care-teams — raise a new CareTeam (with its identifier / category lists).

        Args:
            data:   Serialised CareTeamCreateSchema (exclude_none=True, mode="json").
            actor:  Authenticated caller — FhirClient stamps created_by from actor.sub.
            accept: Content-type preference forwarded to the fhir-server.

        Returns:
            The newly created CareTeam as a dict (plain JSON or FHIR R4).
        """
        return await self._fhir.post(_PATH, data, actor, accept=accept)

    async def get_by_id(self, resource_id: int, accept: str | None = None) -> dict:
        """
        GET /care-teams/{resource_id} — fetch one CareTeam by public ID.

        Args:
            resource_id: The public integer care_team_id.
            accept:      Content-type preference forwarded to the fhir-server.

        Returns:
            The CareTeam dict with its child lists populated.
        """
        return await self._fhir.get(f"{_PATH}/{resource_id}", accept=accept)

    async def list(self, accept: str | None = None, **params) -> dict:
        """
        GET /care-teams — search with the FHIR R4 search parameters.

        Strips None values (and empty lists) from **params before forwarding.
        Underscore-prefixed names (`_id`, `_lastUpdated`) are passed through
        verbatim by unpacking a dict (`**{"_id": "420000"}`). List values (`date`,
        `_lastUpdated`) are sent as repeated query keys, which the fhir-server
        treats as AND.

        Supported params: _id, identifier, status, category, subject, patient, encounter,
        participant, date, _lastUpdated, user_id, org_id, limit, offset.

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
        PATCH /care-teams/{resource_id} — partially update fields and/or replace child lists.

        Args:
            resource_id: The public integer care_team_id.
            data:        Serialised CareTeamPatchSchema (exclude_none=True, mode="json").
            actor:       Authenticated caller — FhirClient stamps updated_by.
            accept:      Content-type preference forwarded to the fhir-server.

        Returns:
            The updated CareTeam resource dict.
        """
        return await self._fhir.patch(f"{_PATH}/{resource_id}", data, actor, accept=accept)

    async def delete(self, resource_id: int) -> None:
        """
        DELETE /care-teams/{resource_id} — permanently remove a CareTeam.

        The fhir-server cascades the delete to the identifier and category rows.

        Args:
            resource_id: The public integer care_team_id to delete.
        """
        await self._fhir.delete(f"{_PATH}/{resource_id}")
