"""
Business logic layer for the Slot resource.

SlotService sits between the router and SlotClient. It owns:
  - Empty-patch rejection (422 if the caller sends an empty PATCH body)
  - Any future business rules (e.g. preventing booking into a busy slot)

The service does NOT inject `created_by` or `updated_by` into the payload —
FhirClient.post() and FhirClient.patch() do that automatically from actor.sub.

The service does NOT inject `user_id` or `org_id` — the caller supplies those
in the request body (or omits them, matching the fhir-server's Optional schema).
"""

from fastapi import HTTPException, status

from app.auth.models import AuthUser
from app.fhir_client.slot import SlotClient
from app.schemas.slot.input import ListSlotsSchema, SlotCreateSchema, SlotPatchSchema


class SlotService:
    """
    Service layer for Slot CRUD operations.

    Mediates between the FastAPI router and the SlotClient. All methods accept
    an optional `accept` string that is threaded through to the fhir-server so
    content negotiation is honoured end-to-end.
    """

    def __init__(self, client: SlotClient) -> None:
        """
        Initialise with a SlotClient injected by the DI container.

        Args:
            client: The domain-specific HTTP client for Slot operations.
        """
        self._client = client

    async def create(
        self,
        dto: SlotCreateSchema,
        actor: AuthUser,
        accept: str | None = None,
    ) -> dict:
        """
        Create a new Slot resource on the fhir-server.

        Serialises the DTO with exclude_none=True so empty Optional fields
        are not sent as explicit nulls. FhirClient.post() stamps created_by
        from actor.sub automatically — do not add it here.

        Args:
            dto:    Validated create input from the router.
            actor:  Authenticated caller — used by FhirClient for created_by.
            accept: Content-type preference forwarded to the fhir-server.

        Returns:
            The newly created Slot as a dict (plain JSON or FHIR depending on accept).
        """
        payload = dto.model_dump(exclude_none=True, mode="json")
        return await self._client.create(payload, actor, accept=accept)

    async def get_by_id(
        self,
        resource_id: int,
        actor: AuthUser,
        accept: str | None = None,
    ) -> dict:
        """
        Fetch a single Slot by its integer primary key.

        Args:
            resource_id: The slot's integer ID on the fhir-server.
            actor:       Authenticated caller (kept for RBAC consistency — not used here).
            accept:      Content-type preference forwarded to the fhir-server.

        Returns:
            The Slot resource dict (plain JSON or FHIR depending on accept).
        """
        return await self._client.get_by_id(resource_id, accept=accept)

    async def list(
        self,
        filters: ListSlotsSchema,
        actor: AuthUser,
        accept: str | None = None,
    ) -> dict:
        """
        List Slots with optional filters.

        Forwards all non-None filter values to SlotClient.list(), which strips
        remaining Nones before hitting the fhir-server.

        Available filters: status, schedule_id, practitioner_role_id, date, start_from, start_to, user_id, org_id.

        Args:
            filters: Validated query parameters from the router.
            actor:   Authenticated caller (kept for RBAC consistency — not used here).
            accept:  Content-type preference forwarded to the fhir-server.

        Returns:
            Paginated plain JSON or a FHIR Bundle depending on accept.
        """
        return await self._client.list(
            accept=accept,
            status=filters.status,
            schedule_id=filters.schedule_id,
            practitioner_role_id=filters.practitioner_role_id,
            date=filters.date,
            start_from=filters.start_from,
            start_to=filters.start_to,
            user_id=filters.user_id,
            org_id=filters.org_id,
            limit=filters.limit,
            offset=filters.offset,
        )

    async def update(
        self,
        resource_id: int,
        dto: SlotPatchSchema,
        actor: AuthUser,
        accept: str | None = None,
    ) -> dict:
        """
        Partially update a Slot resource.

        Rejects the request with 422 if the caller sends an empty body (all None)
        so the fhir-server receives a meaningful PATCH. FhirClient.patch() stamps
        updated_by from actor.sub automatically.

        Patchable fields: status, start, end, overbooked, comment, appointment_type_*.
        Arrays (identifier, serviceCategory, serviceType, specialty) and schedule
        reference are NOT patchable — delete and re-create the Slot to change those.

        Args:
            resource_id: The slot's integer primary key.
            dto:         Validated patch input; at least one field must be non-None.
            actor:       Authenticated caller — used by FhirClient for updated_by.
            accept:      Content-type preference forwarded to the fhir-server.

        Returns:
            The updated Slot resource dict (plain JSON or FHIR depending on accept).

        Raises:
            HTTPException(422): If the patch body is empty.
        """
        payload = dto.model_dump(exclude_none=True, mode="json")
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least one field must be provided for update.",
            )
        return await self._client.patch(resource_id, payload, actor, accept=accept)

    async def delete(self, resource_id: int, actor: AuthUser) -> None:
        """
        Permanently delete a Slot and all its child records.

        The fhir-server cascades the delete to identifier, serviceCategory,
        serviceType, and specialty child tables. This operation is irreversible.

        Args:
            resource_id: The slot's integer primary key to delete.
            actor:       Authenticated caller (kept for RBAC consistency — not used here).
        """
        await self._client.delete(resource_id)
