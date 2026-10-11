"""
Business logic layer for the Task resource.

TaskService sits between the router and TaskClient. It owns empty-patch
rejection, datetime serialisation, and translating the gateway's search schema
into FHIR R4 search parameter names.
"""

from fastapi import HTTPException, status

from app.auth.models import AuthUser
from app.fhir_client.task import TaskClient
from app.schemas.task.input import ListTasksSchema, TaskCreateSchema, TaskPatchSchema


class TaskService:
    """
    Service layer for Task CRUD + search operations.

    Mediates between the FastAPI router and TaskClient.
    """

    def __init__(self, client: TaskClient) -> None:
        """
        Initialise with a TaskClient injected by the DI container.

        Args:
            client: The domain-specific HTTP client for Task operations.
        """
        self._client = client

    async def create(self, dto: TaskCreateSchema, actor: AuthUser, accept: str | None = None) -> dict:
        """
        Create a new Task (with its child lists) on the fhir-server.

        `mode="json"` serialises datetimes/dates to ISO 8601 strings and enums (status,
        intent, priority) to their FHIR codes; `by_alias=True` sends the FHIR name `for`
        (the Python field is `for_reference` because `for` is a keyword); `exclude_none=True`
        drops unset fields at every nesting level.

        Args:
            dto:    Validated create input from the router.
            actor:  Authenticated caller — FhirClient stamps created_by.
            accept: Content-type preference forwarded to the fhir-server.

        Returns:
            The newly created Task dict (plain JSON or FHIR R4).
        """
        payload = dto.model_dump(exclude_none=True, mode="json", by_alias=True)
        return await self._client.create(payload, actor, accept=accept)

    async def get_by_id(self, resource_id: int, actor: AuthUser, accept: str | None = None) -> dict:
        """
        Fetch a single Task by public task_id.

        Args:
            resource_id: The public integer ID on the fhir-server.
            actor:       Authenticated caller (kept for RBAC consistency).
            accept:      Content-type preference forwarded to the fhir-server.

        Returns:
            The Task resource dict.
        """
        return await self._client.get_by_id(resource_id, accept=accept)

    async def list(self, filters: ListTasksSchema, actor: AuthUser, accept: str | None = None) -> dict:
        """
        Search Tasks using the FHIR R4 search parameters.

        Python-friendly filter names are mapped back to the FHIR names the fhir-server expects
        (`id` → `_id`, `group_identifier` → `group-identifier`, `authored_on` → `authored-on`,
        `last_updated` → `_lastUpdated`, ...). The dict is unpacked into the client so special
        keys survive as-is.

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
            "group-identifier": filters.group_identifier,
            "status": filters.status,
            "intent": filters.intent,
            "priority": filters.priority,
            "code": filters.code,
            "business-status": filters.business_status,
            "subject": filters.subject,
            "patient": filters.patient,
            "focus": filters.focus,
            "encounter": filters.encounter,
            "owner": filters.owner,
            "requester": filters.requester,
            "performer": filters.performer,
            "based-on": filters.based_on,
            "part-of": filters.part_of,
            "authored-on": filters.authored_on,
            "modified": filters.modified,
            "period": filters.period,
            "_lastUpdated": filters.last_updated,
            "user_id": filters.user_id,
            "org_id": filters.org_id,
            "limit": filters.limit,
            "offset": filters.offset,
        }
        return await self._client.list(accept=accept, **params)

    async def update(self, resource_id: int, dto: TaskPatchSchema, actor: AuthUser, accept: str | None = None) -> dict:
        """
        Partially update a Task (scalar/reference fields and/or replace child lists).

        Rejects with 422 if the patch body is empty. Because `None` fields are dropped from the
        payload, an optional reference can be changed through this gateway but not cleared, and
        a child list is cleared by sending `[]`.

        Args:
            resource_id: The public integer task_id.
            dto:         Validated patch input; at least one field must be non-None.
            actor:       Authenticated caller — FhirClient stamps updated_by.
            accept:      Content-type preference forwarded to the fhir-server.

        Returns:
            The updated Task resource dict.

        Raises:
            HTTPException(422): If the patch body is empty.
        """
        payload = dto.model_dump(exclude_none=True, mode="json", by_alias=True)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least one field must be provided for update.",
            )
        return await self._client.patch(resource_id, payload, actor, accept=accept)

    async def delete(self, resource_id: int, actor: AuthUser) -> None:
        """
        Permanently delete a Task and its child records.

        Args:
            resource_id: The public integer task_id to delete.
            actor:       Authenticated caller (kept for RBAC consistency).
        """
        await self._client.delete(resource_id)
