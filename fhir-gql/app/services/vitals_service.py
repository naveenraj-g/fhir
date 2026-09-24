"""
Business logic layer for the Vitals resource.

VitalsService sits between the router and VitalsClient. It owns empty-patch
rejection — the only business rule this proxy needs, since the fhir-server
already validates metric ranges and resolves patient linkage.
"""

from fastapi import HTTPException, status

from app.auth.models import AuthUser
from app.fhir_client.vitals import VitalsClient
from app.schemas.vitals.input import ListVitalsSchema, VitalsCreateSchema, VitalsPatchSchema


class VitalsService:
    """
    Service layer for Vitals CRUD operations.

    Mediates between the FastAPI router and VitalsClient.
    """

    def __init__(self, client: VitalsClient) -> None:
        """
        Initialise with a VitalsClient injected by the DI container.

        Args:
            client: The domain-specific HTTP client for Vitals operations.
        """
        self._client = client

    async def create(self, dto: VitalsCreateSchema, actor: AuthUser) -> dict:
        """
        Create a new Vitals entry on the fhir-server.

        `mode="json"` serialises `recorded_at`/`date`; `exclude_none=True` drops
        unset fields so the fhir-server's own defaults/derivations apply.

        Args:
            dto:   Validated create input from the router.
            actor: Authenticated caller — VitalsClient stamps created_by.

        Returns:
            The newly created Vitals entry dict.
        """
        payload = dto.model_dump(exclude_none=True, mode="json")
        return await self._client.create(payload, actor)

    async def get_by_id(self, vitals_id: int, actor: AuthUser) -> dict:
        """
        Fetch a single Vitals entry by its public integer ID.

        Args:
            vitals_id: The vitals entry's public identifier on the fhir-server.
            actor:     Authenticated caller (kept for RBAC consistency).

        Returns:
            The Vitals entry dict.
        """
        return await self._client.get_by_id(vitals_id)

    async def list(self, filters: ListVitalsSchema, actor: AuthUser) -> dict:
        """
        List Vitals entries with optional filters.

        `date`, `recorded_at_from`, and `recorded_at_to` are serialised to ISO
        8601 strings for the fhir-server query string.

        Args:
            filters: Validated query parameters from the router.
            actor:   Authenticated caller (kept for RBAC consistency).

        Returns:
            Paginated Vitals dict: {total, limit, offset, data: [...]}.
        """
        return await self._client.list(
            user_id=filters.user_id,
            patient_id=filters.patient_id,
            org_id=filters.org_id,
            date=filters.date.isoformat() if filters.date else None,
            recorded_at_from=(
                filters.recorded_at_from.isoformat() if filters.recorded_at_from else None
            ),
            recorded_at_to=(
                filters.recorded_at_to.isoformat() if filters.recorded_at_to else None
            ),
            limit=filters.limit,
            offset=filters.offset,
        )

    async def update(self, vitals_id: int, dto: VitalsPatchSchema, actor: AuthUser) -> dict:
        """
        Partially update metric fields on a Vitals entry.

        Rejects with 422 if the patch body is empty.

        Args:
            vitals_id: The vitals entry's public integer ID.
            dto:       Validated patch input; at least one field must be non-None.
            actor:     Authenticated caller — VitalsClient stamps updated_by.

        Returns:
            The updated Vitals entry dict.

        Raises:
            HTTPException(422): If the patch body is empty.
        """
        payload = dto.model_dump(exclude_none=True, mode="json")
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least one field must be provided for update.",
            )
        return await self._client.patch(vitals_id, payload, actor)

    async def delete(self, vitals_id: int, actor: AuthUser) -> None:
        """
        Permanently delete a Vitals entry.

        Args:
            vitals_id: The vitals entry's public integer ID to delete.
            actor:     Authenticated caller (kept for RBAC consistency).
        """
        await self._client.delete(vitals_id)
