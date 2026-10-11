"""
Business logic layer for the Procedure resource.

ProcedureService sits between the router and ProcedureClient. It owns
empty-patch rejection, datetime serialisation, and translating the gateway's
search schema into FHIR R4 search parameter names.
"""

from fastapi import HTTPException, status

from app.auth.models import AuthUser
from app.fhir_client.procedure import ProcedureClient
from app.schemas.procedure.input import (
    ListProceduresSchema,
    ProcedureCreateSchema,
    ProcedurePatchSchema,
)


class ProcedureService:
    """
    Service layer for Procedure CRUD + search operations.

    Mediates between the FastAPI router and ProcedureClient.
    """

    def __init__(self, client: ProcedureClient) -> None:
        """
        Initialise with a ProcedureClient injected by the DI container.

        Args:
            client: The domain-specific HTTP client for Procedure operations.
        """
        self._client = client

    async def create(
        self,
        dto: ProcedureCreateSchema,
        actor: AuthUser,
        accept: str | None = None,
    ) -> dict:
        """
        Create a new Procedure resource on the fhir-server.

        `mode="json"` serialises datetimes (performed_*, note.time, identifier
        periods) to ISO 8601 strings and the ProcedureStatus enum to its FHIR code.
        `exclude_none=True` drops unset fields.

        Args:
            dto:    Validated create input from the router.
            actor:  Authenticated caller — FhirClient stamps created_by.
            accept: Content-type preference forwarded to the fhir-server.

        Returns:
            The newly created Procedure dict (plain JSON or FHIR R4).
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
        Fetch a single Procedure by public procedure_id.

        Args:
            resource_id: The procedure's public integer ID on the fhir-server.
            actor:       Authenticated caller (kept for RBAC consistency).
            accept:      Content-type preference forwarded to the fhir-server.

        Returns:
            The Procedure resource dict with all child arrays populated.
        """
        return await self._client.get_by_id(resource_id, accept=accept)

    async def list(
        self,
        filters: ListProceduresSchema,
        actor: AuthUser,
        accept: str | None = None,
    ) -> dict:
        """
        Search Procedures using the FHIR R4 search parameters.

        Python-friendly filter names are mapped back to the FHIR parameter names
        the fhir-server expects (`id` → `_id`, `part_of` → `part-of`,
        `last_updated` → `_lastUpdated`, ...). The dict is unpacked into the
        client so hyphenated/underscore-prefixed keys survive as-is.

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
            "patient": filters.patient,
            "subject": filters.subject,
            "encounter": filters.encounter,
            "date": filters.date,
            "performer": filters.performer,
            "location": filters.location,
            "part-of": filters.part_of,
            "based-on": filters.based_on,
            "reason-code": filters.reason_code,
            "reason-reference": filters.reason_reference,
            "instantiates-canonical": filters.instantiates_canonical,
            "instantiates-uri": filters.instantiates_uri,
            "_lastUpdated": filters.last_updated,
            "user_id": filters.user_id,
            "org_id": filters.org_id,
            "limit": filters.limit,
            "offset": filters.offset,
        }
        return await self._client.list(accept=accept, **params)

    async def update(
        self,
        resource_id: int,
        dto: ProcedurePatchSchema,
        actor: AuthUser,
        accept: str | None = None,
    ) -> dict:
        """
        Partially update scalar and reference fields on a Procedure.

        Rejects with 422 if the patch body is empty. `mode="json"` serialises
        datetimes and the status enum.

        Args:
            resource_id: The procedure's public integer ID.
            dto:         Validated patch input; at least one field must be non-None.
            actor:       Authenticated caller — FhirClient stamps updated_by.
            accept:      Content-type preference forwarded to the fhir-server.

        Returns:
            The updated Procedure resource dict.

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
        Permanently delete a Procedure and all its child records.

        The fhir-server cascades to every child table.

        Args:
            resource_id: The procedure's public integer ID to delete.
            actor:       Authenticated caller (kept for RBAC consistency).
        """
        await self._client.delete(resource_id)
