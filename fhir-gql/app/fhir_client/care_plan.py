"""
FHIR client for CarePlan resources.

Thin wrapper around the shared FhirClient that knows the fhir-server path for
CarePlans. No business logic lives here — all validation and rules belong in
CarePlanService.

A CarePlan describes the intended care for a patient or group: its goals, the
care team and a list of activities (each either a reference to a request resource
or an inline detail with status, schedule, product and performers).

Reference: https://www.hl7.org/fhir/R4/careplan.html
"""

from app.auth.models import AuthUser
from app.fhir_client.client import FhirClient

# Confirmed in fhir-server routers prefix (app/routers/__init__.py: "/care-plans").
_PATH = "/care-plans"


class CarePlanClient:
    """
    Domain-specific HTTP client for CarePlan resources.

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
        POST /care-plans — raise a new CarePlan (with its identifier / category lists).

        Args:
            data:   Serialised CarePlanCreateSchema (exclude_none=True, mode="json").
            actor:  Authenticated caller — FhirClient stamps created_by from actor.sub.
            accept: Content-type preference forwarded to the fhir-server.

        Returns:
            The newly created CarePlan as a dict (plain JSON or FHIR R4).
        """
        return await self._fhir.post(_PATH, data, actor, accept=accept)

    async def get_by_id(self, resource_id: int, accept: str | None = None) -> dict:
        """
        GET /care-plans/{resource_id} — fetch one CarePlan by public ID.

        Args:
            resource_id: The public integer care_plan_id.
            accept:      Content-type preference forwarded to the fhir-server.

        Returns:
            The CarePlan dict with its child lists populated.
        """
        return await self._fhir.get(f"{_PATH}/{resource_id}", accept=accept)

    async def list(self, accept: str | None = None, **params) -> dict:
        """
        GET /care-plans — search with the FHIR R4 search parameters.

        Strips None values (and empty lists) from **params before forwarding.
        Underscore-prefixed names (`_id`, `_lastUpdated`) are passed through
        verbatim by unpacking a dict (`**{"_id": "290000"}`). List values (`date`,
        `_lastUpdated`) are sent as repeated query keys, which the fhir-server
        treats as AND.

        Supported params: _id, identifier, status, intent, category, activity-code,
        activity-reference, based-on, replaces, part-of, care-team, condition, goal, encounter, subject,
        patient, performer, instantiates-canonical, instantiates-uri, date, activity-date, _lastUpdated,
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
        PATCH /care-plans/{resource_id} — partially update fields and/or replace child lists.

        Args:
            resource_id: The public integer care_plan_id.
            data:        Serialised CarePlanPatchSchema (exclude_none=True, mode="json").
            actor:       Authenticated caller — FhirClient stamps updated_by.
            accept:      Content-type preference forwarded to the fhir-server.

        Returns:
            The updated CarePlan resource dict.
        """
        return await self._fhir.patch(f"{_PATH}/{resource_id}", data, actor, accept=accept)

    async def delete(self, resource_id: int) -> None:
        """
        DELETE /care-plans/{resource_id} — permanently remove a CarePlan.

        The fhir-server cascades the delete to the identifier and category rows.

        Args:
            resource_id: The public integer care_plan_id to delete.
        """
        await self._fhir.delete(f"{_PATH}/{resource_id}")
