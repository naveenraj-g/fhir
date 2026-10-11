"""
Business logic layer for the CarePlan resource.

CarePlanService sits between the router and CarePlanClient. It owns empty-patch
rejection, datetime serialisation, and translating the gateway's search schema
into FHIR R4 search parameter names.
"""

from fastapi import HTTPException, status

from app.auth.models import AuthUser
from app.fhir_client.care_plan import CarePlanClient
from app.schemas.care_plan.input import CarePlanCreateSchema, CarePlanPatchSchema, ListCarePlansSchema


class CarePlanService:
    """
    Service layer for CarePlan CRUD + search operations.

    Mediates between the FastAPI router and CarePlanClient.
    """

    def __init__(self, client: CarePlanClient) -> None:
        """
        Initialise with a CarePlanClient injected by the DI container.

        Args:
            client: The domain-specific HTTP client for CarePlan operations.
        """
        self._client = client

    async def create(self, dto: CarePlanCreateSchema, actor: AuthUser, accept: str | None = None) -> dict:
        """
        Raise a new CarePlan on the fhir-server.

        `mode="json"` serialises datetimes to ISO 8601 strings and the status enum to
        its FHIR code. `exclude_none=True` drops unset fields.

        Args:
            dto:    Validated create input from the router.
            actor:  Authenticated caller — FhirClient stamps created_by.
            accept: Content-type preference forwarded to the fhir-server.

        Returns:
            The newly created CarePlan dict (plain JSON or FHIR R4).
        """
        payload = dto.model_dump(exclude_none=True, mode="json")
        return await self._client.create(payload, actor, accept=accept)

    async def get_by_id(self, resource_id: int, actor: AuthUser, accept: str | None = None) -> dict:
        """
        Fetch a single CarePlan by public care_plan_id.

        Args:
            resource_id: The public integer ID on the fhir-server.
            actor:       Authenticated caller (kept for RBAC consistency).
            accept:      Content-type preference forwarded to the fhir-server.

        Returns:
            The CarePlan resource dict.
        """
        return await self._client.get_by_id(resource_id, accept=accept)

    async def list(self, filters: ListCarePlansSchema, actor: AuthUser, accept: str | None = None) -> dict:
        """
        Search CarePlans using the FHIR R4 search parameters.

        Python-friendly filter names are mapped back to the FHIR names the
        fhir-server expects (`id` → `_id`, `activity_code` → `activity-code`, `based_on` → `based-on`, `last_updated` → `_lastUpdated`, ...). The
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
            "intent": filters.intent,
            "category": filters.category,
            "activity-code": filters.activity_code,
            "activity-reference": filters.activity_reference,
            "based-on": filters.based_on,
            "replaces": filters.replaces,
            "part-of": filters.part_of,
            "care-team": filters.care_team,
            "condition": filters.condition,
            "goal": filters.goal,
            "encounter": filters.encounter,
            "subject": filters.subject,
            "patient": filters.patient,
            "performer": filters.performer,
            "instantiates-canonical": filters.instantiates_canonical,
            "instantiates-uri": filters.instantiates_uri,
            "date": filters.date,
            "activity-date": filters.activity_date,
            "_lastUpdated": filters.last_updated,
            "user_id": filters.user_id,
            "org_id": filters.org_id,
            "limit": filters.limit,
            "offset": filters.offset,
        }
        return await self._client.list(accept=accept, **params)

    async def update(
        self, resource_id: int, dto: CarePlanPatchSchema, actor: AuthUser, accept: str | None = None
    ) -> dict:
        """
        Partially update a CarePlan (scalar/reference fields and/or replace child lists).

        Rejects with 422 if the patch body is empty. Because `None` fields are dropped
        from the payload, an optional reference can be changed through this gateway but
        not cleared, and a child list is cleared by sending `[]`.

        Args:
            resource_id: The public integer care_plan_id.
            dto:         Validated patch input; at least one field must be non-None.
            actor:       Authenticated caller — FhirClient stamps updated_by.
            accept:      Content-type preference forwarded to the fhir-server.

        Returns:
            The updated CarePlan resource dict.

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
        Permanently delete a CarePlan and its child records.

        Args:
            resource_id: The public integer care_plan_id to delete.
            actor:       Authenticated caller (kept for RBAC consistency).
        """
        await self._client.delete(resource_id)
