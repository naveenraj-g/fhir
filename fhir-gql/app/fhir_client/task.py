"""
FHIR client for Task resources.

Thin wrapper around the shared FhirClient that knows the fhir-server path for
Tasks. No business logic lives here — all validation and rules belong in
TaskService.

A Task is a unit of work to be performed: it tracks a request (a focus resource
such as a ServiceRequest) through its lifecycle (status, businessStatus), says
who asked (requester), who should do it (owner / performerType), for whom
(`for`) and when, and carries typed inputs and outputs.

Reference: https://www.hl7.org/fhir/R4/task.html
"""

from app.auth.models import AuthUser
from app.fhir_client.client import FhirClient

# Confirmed in fhir-server routers prefix (app/routers/__init__.py: "/tasks").
_PATH = "/tasks"


class TaskClient:
    """
    Domain-specific HTTP client for Task resources.

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
        POST /tasks — create a new Task with its child lists (identifiers, based_on, part_of,
        performer_types, insurance, notes, relevant_history, restriction_recipients, inputs, outputs).

        Args:
            data:   Serialised TaskCreateSchema (exclude_none=True, mode="json", by_alias=True).
            actor:  Authenticated caller — FhirClient stamps created_by from actor.sub.
            accept: Content-type preference forwarded to the fhir-server.

        Returns:
            The newly created Task as a dict (plain JSON or FHIR R4).
        """
        return await self._fhir.post(_PATH, data, actor, accept=accept)

    async def get_by_id(self, resource_id: int, accept: str | None = None) -> dict:
        """
        GET /tasks/{resource_id} — fetch one Task by public ID.

        Args:
            resource_id: The public integer task_id.
            accept:      Content-type preference forwarded to the fhir-server.

        Returns:
            The Task dict with its child lists populated.
        """
        return await self._fhir.get(f"{_PATH}/{resource_id}", accept=accept)

    async def list(self, accept: str | None = None, **params) -> dict:
        """
        GET /tasks — search with the FHIR R4 search parameters.

        Strips None values (and empty lists) from **params before forwarding.
        Hyphenated and underscore-prefixed names (`group-identifier`, `business-status`,
        `based-on`, `part-of`, `authored-on`, `_id`, `_lastUpdated`) are passed through
        verbatim by unpacking a dict (`**{"based-on": "ServiceRequest/1"}`). List values
        (`authored-on`, `modified`, `period`, `_lastUpdated`) are sent as repeated query
        keys, which the fhir-server treats as AND.

        Supported params: _id, identifier, group-identifier, status, intent, priority, code,
        business-status, subject, patient, focus, encounter, owner, requester, performer,
        based-on, part-of, authored-on, modified, period, _lastUpdated, user_id, org_id,
        limit, offset.

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
        PATCH /tasks/{resource_id} — partially update fields and/or replace child lists.

        Args:
            resource_id: The public integer task_id.
            data:        Serialised TaskPatchSchema (exclude_none=True, mode="json", by_alias=True).
            actor:       Authenticated caller — FhirClient stamps updated_by.
            accept:      Content-type preference forwarded to the fhir-server.

        Returns:
            The updated Task resource dict.
        """
        return await self._fhir.patch(f"{_PATH}/{resource_id}", data, actor, accept=accept)

    async def delete(self, resource_id: int) -> None:
        """
        DELETE /tasks/{resource_id} — permanently remove a Task.

        The fhir-server cascades the delete to every child row.

        Args:
            resource_id: The public integer task_id to delete.
        """
        await self._fhir.delete(f"{_PATH}/{resource_id}")
