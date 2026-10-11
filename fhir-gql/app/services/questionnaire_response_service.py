"""
Business logic layer for the QuestionnaireResponse resource.

QuestionnaireResponseService sits between the router and
QuestionnaireResponseClient. It owns empty-patch rejection, datetime/date
serialisation, and translating the gateway's search schema into FHIR R4 search
parameter names.
"""

from fastapi import HTTPException, status

from app.auth.models import AuthUser
from app.fhir_client.questionnaire_response import QuestionnaireResponseClient
from app.schemas.questionnaire_response.input import (
    ListQuestionnaireResponsesSchema,
    QuestionnaireResponseCreateSchema,
    QuestionnaireResponsePatchSchema,
)


class QuestionnaireResponseService:
    """
    Service layer for QuestionnaireResponse CRUD + search operations.

    Mediates between the FastAPI router and QuestionnaireResponseClient.
    """

    def __init__(self, client: QuestionnaireResponseClient) -> None:
        """
        Initialise with a QuestionnaireResponseClient injected by the DI container.

        Args:
            client: The domain-specific HTTP client for QuestionnaireResponse operations.
        """
        self._client = client

    async def create(
        self,
        dto: QuestionnaireResponseCreateSchema,
        actor: AuthUser,
        accept: str | None = None,
    ) -> dict:
        """
        Record a new QuestionnaireResponse (with its whole item tree) on the fhir-server.

        `mode="json"` serialises datetimes/dates to ISO 8601 strings and enums
        (status, identifier use) to their FHIR codes. `exclude_none=True` drops
        unset fields at every nesting level.

        Args:
            dto:    Validated create input from the router.
            actor:  Authenticated caller — FhirClient stamps created_by.
            accept: Content-type preference forwarded to the fhir-server.

        Returns:
            The newly created QuestionnaireResponse dict (plain JSON or FHIR R4).
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
        Fetch a single QuestionnaireResponse by public ID.

        Args:
            resource_id: The public integer questionnaire_response_id.
            actor:       Authenticated caller (kept for RBAC consistency).
            accept:      Content-type preference forwarded to the fhir-server.

        Returns:
            The QuestionnaireResponse resource dict with the whole item tree.
        """
        return await self._client.get_by_id(resource_id, accept=accept)

    async def list(
        self,
        filters: ListQuestionnaireResponsesSchema,
        actor: AuthUser,
        accept: str | None = None,
    ) -> dict:
        """
        Search QuestionnaireResponses using the FHIR R4 search parameters.

        Python-friendly filter names are mapped back to the FHIR names the
        fhir-server expects (`id` → `_id`, `based_on` → `based-on`,
        `last_updated` → `_lastUpdated`, ...). The dict is unpacked into the
        client so special keys survive as-is.

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
            "questionnaire": filters.questionnaire,
            "status": filters.status,
            "subject": filters.subject,
            "patient": filters.patient,
            "encounter": filters.encounter,
            "author": filters.author,
            "source": filters.source,
            "based-on": filters.based_on,
            "part-of": filters.part_of,
            "authored": filters.authored,
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
        dto: QuestionnaireResponsePatchSchema,
        actor: AuthUser,
        accept: str | None = None,
    ) -> dict:
        """
        Partially update scalar and reference fields on a QuestionnaireResponse.

        Rejects with 422 if the patch body is empty. Because `None` fields are
        dropped from the payload, optional references can be changed through
        this gateway but not cleared.

        Args:
            resource_id: The public integer questionnaire_response_id.
            dto:         Validated patch input; at least one field must be non-None.
            actor:       Authenticated caller — FhirClient stamps updated_by.
            accept:      Content-type preference forwarded to the fhir-server.

        Returns:
            The updated QuestionnaireResponse resource dict.

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
        Permanently delete a QuestionnaireResponse and its whole item tree.

        Args:
            resource_id: The public integer questionnaire_response_id to delete.
            actor:       Authenticated caller (kept for RBAC consistency).
        """
        await self._client.delete(resource_id)
