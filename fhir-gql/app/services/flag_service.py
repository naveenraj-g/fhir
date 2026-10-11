"""
Business logic layer for the Flag resource.

FlagService sits between the router and FlagClient. It owns empty-patch
rejection, datetime serialisation, and translating the gateway's search schema
into FHIR R4 search parameter names.
"""

from fastapi import HTTPException, status

from app.auth.models import AuthUser
from app.fhir_client.flag import FlagClient
from app.schemas.flag.input import FlagCreateSchema, FlagPatchSchema, ListFlagsSchema


class FlagService:
    """
    Service layer for Flag CRUD + search operations.

    Mediates between the FastAPI router and FlagClient.
    """

    def __init__(self, client: FlagClient) -> None:
        """
        Initialise with a FlagClient injected by the DI container.

        Args:
            client: The domain-specific HTTP client for Flag operations.
        """
        self._client = client

    async def create(self, dto: FlagCreateSchema, actor: AuthUser, accept: str | None = None) -> dict:
        """
        Raise a new Flag on the fhir-server.

        `mode="json"` serialises datetimes to ISO 8601 strings and the status enum to
        its FHIR code. `exclude_none=True` drops unset fields.

        Args:
            dto:    Validated create input from the router.
            actor:  Authenticated caller — FhirClient stamps created_by.
            accept: Content-type preference forwarded to the fhir-server.

        Returns:
            The newly created Flag dict (plain JSON or FHIR R4).
        """
        payload = dto.model_dump(exclude_none=True, mode="json")
        return await self._client.create(payload, actor, accept=accept)

    async def get_by_id(self, resource_id: int, actor: AuthUser, accept: str | None = None) -> dict:
        """
        Fetch a single Flag by public flag_id.

        Args:
            resource_id: The public integer ID on the fhir-server.
            actor:       Authenticated caller (kept for RBAC consistency).
            accept:      Content-type preference forwarded to the fhir-server.

        Returns:
            The Flag resource dict.
        """
        return await self._client.get_by_id(resource_id, accept=accept)

    async def list(self, filters: ListFlagsSchema, actor: AuthUser, accept: str | None = None) -> dict:
        """
        Search Flags using the FHIR R4 search parameters.

        Python-friendly filter names are mapped back to the FHIR names the
        fhir-server expects (`id` → `_id`, `last_updated` → `_lastUpdated`). The
        dict is unpacked into the client so special keys survive as-is.

        Args:
            filters: Validated search parameters from the router.
            actor:   Authenticated caller (kept for RBAC consistency).
            accept:  Content-type preference forwarded to the fhir-server.

        Returns:
            Paginated plain JSON or FHIR Bundle depending on accept.
        """
        params = {
            "_id": filters.id,
            "identifier": filters.identifier,
            "status": filters.status,
            "category": filters.category,
            "code": filters.code,
            "subject": filters.subject,
            "patient": filters.patient,
            "encounter": filters.encounter,
            "author": filters.author,
            "date": filters.date,
            "_lastUpdated": filters.last_updated,
            "user_id": filters.user_id,
            "org_id": filters.org_id,
            "limit": filters.limit,
            "offset": filters.offset,
        }
        return await self._client.list(accept=accept, **params)

    async def update(
        self, resource_id: int, dto: FlagPatchSchema, actor: AuthUser, accept: str | None = None
    ) -> dict:
        """
        Partially update a Flag (scalar/reference fields and/or replace child lists).

        Rejects with 422 if the patch body is empty. Because `None` fields are dropped
        from the payload, an optional reference can be changed through this gateway but
        not cleared, and a child list is cleared by sending `[]`.

        Args:
            resource_id: The public integer flag_id.
            dto:         Validated patch input; at least one field must be non-None.
            actor:       Authenticated caller — FhirClient stamps updated_by.
            accept:      Content-type preference forwarded to the fhir-server.

        Returns:
            The updated Flag resource dict.

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
        Permanently delete a Flag and its child records.

        Args:
            resource_id: The public integer flag_id to delete.
            actor:       Authenticated caller (kept for RBAC consistency).
        """
        await self._client.delete(resource_id)
