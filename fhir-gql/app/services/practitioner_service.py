"""
Business logic layer for the Practitioner resource.

PractitionerService sits between the router and PractitionerClient. It owns:
  - Empty-patch rejection (422 if the caller sends an empty PATCH body)
  - Any future business rules (e.g. duplicate NPI detection)

The service does NOT inject created_by or updated_by — FhirClient does that.
The service does NOT inject user_id or org_id — the caller supplies them in the
request body (optional, matching the fhir-server schema).
"""

from fastapi import HTTPException, status

from app.auth.models import AuthUser
from app.fhir_client.practitioner import PractitionerClient
from app.schemas.practitioner.input import ListPractitionersSchema, PractitionerCreateSchema, PractitionerPatchSchema


class PractitionerService:
    """
    Service layer for Practitioner CRUD operations.

    Mediates between the FastAPI router and PractitionerClient. All methods
    accept an optional `accept` string threaded through to the fhir-server for
    content negotiation.
    """

    def __init__(self, client: PractitionerClient) -> None:
        """
        Initialise with a PractitionerClient injected by the DI container.

        Args:
            client: The domain-specific HTTP client for Practitioner operations.
        """
        self._client = client

    async def create(
        self,
        dto: PractitionerCreateSchema,
        actor: AuthUser,
        accept: str | None = None,
    ) -> dict:
        """
        Create a new Practitioner resource on the fhir-server.

        Serialises the DTO with exclude_none=True so Optional fields that
        were not provided are not sent as explicit nulls. FhirClient.post()
        stamps created_by from actor.sub automatically.

        Child sub-resources (name, identifier, telecom, address, photo,
        qualification, communication) are managed via separate fhir-server
        sub-routes and are NOT included in this call.

        Args:
            dto:    Validated create input from the router.
            actor:  Authenticated caller — used by FhirClient for created_by.
            accept: Content-type preference forwarded to the fhir-server.

        Returns:
            The newly created Practitioner dict (plain JSON or FHIR).
        """
        payload = dto.model_dump(exclude_none=True)
        return await self._client.create(payload, actor, accept=accept)

    async def get_by_id(
        self,
        resource_id: int,
        actor: AuthUser,
        accept: str | None = None,
    ) -> dict:
        """
        Fetch a single Practitioner by integer primary key.

        The fhir-server populates all child arrays (name, identifier, telecom, etc.)
        in the response automatically.

        Args:
            resource_id: The practitioner's integer ID on the fhir-server.
            actor:       Authenticated caller (kept for RBAC consistency).
            accept:      Content-type preference forwarded to the fhir-server.

        Returns:
            The Practitioner resource dict with all child arrays populated.
        """
        return await self._client.get_by_id(resource_id, accept=accept)

    async def list(
        self,
        filters: ListPractitionersSchema,
        actor: AuthUser,
        accept: str | None = None,
    ) -> dict:
        """
        List Practitioners with optional filters.

        Forwards all non-None filter values. family_name and given_name search
        the practitioner_name child table on the fhir-server (partial, case-insensitive).

        Args:
            filters: Validated query parameters from the router.
            actor:   Authenticated caller (kept for RBAC consistency).
            accept:  Content-type preference forwarded to the fhir-server.

        Returns:
            Paginated plain JSON or FHIR Bundle depending on accept.
        """
        return await self._client.list(
            accept=accept,
            family_name=filters.family_name,
            given_name=filters.given_name,
            active=filters.active,
            user_id=filters.user_id,
            org_id=filters.org_id,
            limit=filters.limit,
            offset=filters.offset,
        )

    async def update(
        self,
        resource_id: int,
        dto: PractitionerPatchSchema,
        actor: AuthUser,
        accept: str | None = None,
    ) -> dict:
        """
        Partially update a Practitioner resource.

        Rejects the request with 422 if all fields are None (empty body).
        FhirClient.patch() stamps updated_by from actor.sub automatically.

        Only scalar fields are patchable here (active, gender, birth_date,
        deceased_*). Child arrays are managed via separate fhir-server sub-routes.

        Args:
            resource_id: The practitioner's integer primary key.
            dto:         Validated patch input; at least one field must be non-None.
            actor:       Authenticated caller — used by FhirClient for updated_by.
            accept:      Content-type preference forwarded to the fhir-server.

        Returns:
            The updated Practitioner resource dict.

        Raises:
            HTTPException(422): If the patch body is empty.
        """
        payload = dto.model_dump(exclude_none=True)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least one field must be provided for update.",
            )
        return await self._client.patch(resource_id, payload, actor, accept=accept)

    async def delete(self, resource_id: int, actor: AuthUser) -> None:
        """
        Permanently delete a Practitioner and all its child records.

        The fhir-server cascades the delete to all child tables (name, identifier,
        telecom, address, photo, qualification, communication). This operation
        is irreversible.

        Args:
            resource_id: The practitioner's integer primary key to delete.
            actor:       Authenticated caller (kept for RBAC consistency).
        """
        await self._client.delete(resource_id)
