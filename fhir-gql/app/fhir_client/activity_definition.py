"""
FHIR client for ActivityDefinition resources.

Thin wrapper around the shared FhirClient that knows the fhir-server path for
ActivityDefinitions. No business logic lives here — all validation and rules belong
in ActivityDefinitionService.

An ActivityDefinition describes a protocol, order set or clinical decision-support
rule: goals plus a recursive tree of actions (with triggers, conditions, data
requirements, related actions, participants and dynamic values).

Reference: https://www.hl7.org/fhir/R4/activitydefinition.html
"""

from app.auth.models import AuthUser
from app.fhir_client.client import FhirClient

# Confirmed in fhir-server routers prefix (app/routers/__init__.py: "/activity-definitions").
_PATH = "/activity-definitions"


class ActivityDefinitionClient:
    """
    Domain-specific HTTP client for ActivityDefinition resources.

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
        POST /activity-definitions — raise a new ActivityDefinition (with its identifier / category lists).

        Args:
            data:   Serialised ActivityDefinitionCreateSchema (exclude_none=True, mode="json").
            actor:  Authenticated caller — FhirClient stamps created_by from actor.sub.
            accept: Content-type preference forwarded to the fhir-server.

        Returns:
            The newly created ActivityDefinition as a dict (plain JSON or FHIR R4).
        """
        return await self._fhir.post(_PATH, data, actor, accept=accept)

    async def get_by_id(self, resource_id: int, accept: str | None = None) -> dict:
        """
        GET /activity-definitions/{resource_id} — fetch one ActivityDefinition by public ID.

        Args:
            resource_id: The public integer activity_definition_id.
            accept:      Content-type preference forwarded to the fhir-server.

        Returns:
            The ActivityDefinition dict with its child lists populated.
        """
        return await self._fhir.get(f"{_PATH}/{resource_id}", accept=accept)

    async def list(self, accept: str | None = None, **params) -> dict:
        """
        GET /activity-definitions — search with the FHIR R4 search parameters.

        Strips None values (and empty lists) from **params before forwarding.
        Underscore-prefixed names (`_id`, `_lastUpdated`) are passed through
        verbatim by unpacking a dict (`**{"_id": "410000"}`). List values (`date`,
        `_lastUpdated`) are sent as repeated query keys, which the fhir-server
        treats as AND.

        Supported params: _id, identifier, url, version, name, title, publisher, description
        (+ `:contains` / `:exact`), status, topic, jurisdiction, context, context-type, depends-on,
        derived-from, predecessor, successor, composed-of, date, effective, _lastUpdated,
        user_id, org_id, limit, offset.

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
        PATCH /activity-definitions/{resource_id} — partially update fields and/or replace child lists.

        Args:
            resource_id: The public integer activity_definition_id.
            data:        Serialised ActivityDefinitionPatchSchema (exclude_none=True, mode="json").
            actor:       Authenticated caller — FhirClient stamps updated_by.
            accept:      Content-type preference forwarded to the fhir-server.

        Returns:
            The updated ActivityDefinition resource dict.
        """
        return await self._fhir.patch(f"{_PATH}/{resource_id}", data, actor, accept=accept)

    async def delete(self, resource_id: int) -> None:
        """
        DELETE /activity-definitions/{resource_id} — permanently remove a ActivityDefinition.

        The fhir-server cascades the delete to the identifier and category rows.

        Args:
            resource_id: The public integer activity_definition_id to delete.
        """
        await self._fhir.delete(f"{_PATH}/{resource_id}")
