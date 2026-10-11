"""
Business logic layer for the Questionnaire resource.

QuestionnaireService sits between the router and QuestionnaireClient. It owns
empty-patch rejection, datetime serialisation, and translating the gateway's
search schema into FHIR R4 search parameter names.
"""

from fastapi import HTTPException, status

from app.auth.models import AuthUser
from app.fhir_client.questionnaire import QuestionnaireClient
from app.schemas.questionnaire.input import (
    ListQuestionnairesSchema,
    QuestionnaireCreateSchema,
    QuestionnairePatchSchema,
)


class QuestionnaireService:
    """
    Service layer for Questionnaire CRUD + search operations.

    Mediates between the FastAPI router and QuestionnaireClient.
    """

    def __init__(self, client: QuestionnaireClient) -> None:
        """
        Initialise with a QuestionnaireClient injected by the DI container.

        Args:
            client: The domain-specific HTTP client for Questionnaire operations.
        """
        self._client = client

    async def create(
        self,
        dto: QuestionnaireCreateSchema,
        actor: AuthUser,
        accept: str | None = None,
    ) -> dict:
        """
        Create a new Questionnaire (with its whole item tree) on the fhir-server.

        `mode="json"` serialises datetimes/dates to ISO 8601 strings and enums
        (status, item type, enableWhen operator, ...) to their FHIR codes.
        `exclude_none=True` drops unset fields at every nesting level.

        Args:
            dto:    Validated create input from the router.
            actor:  Authenticated caller — FhirClient stamps created_by.
            accept: Content-type preference forwarded to the fhir-server.

        Returns:
            The newly created Questionnaire dict (plain JSON or FHIR R4).
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
        Fetch a single Questionnaire by public questionnaire_id.

        Args:
            resource_id: The questionnaire's public integer ID on the fhir-server.
            actor:       Authenticated caller (kept for RBAC consistency).
            accept:      Content-type preference forwarded to the fhir-server.

        Returns:
            The Questionnaire resource dict with the whole item tree.
        """
        return await self._client.get_by_id(resource_id, accept=accept)

    async def list(
        self,
        filters: ListQuestionnairesSchema,
        actor: AuthUser,
        accept: str | None = None,
    ) -> dict:
        """
        Search Questionnaires using the FHIR R4 search parameters.

        Python-friendly filter names are mapped back to the FHIR parameter names
        the fhir-server expects (`id` → `_id`, `subject_type` → `subject-type`,
        `name_contains` → `name:contains`, `last_updated` → `_lastUpdated`, ...).
        The dict is unpacked into the client so special keys survive as-is.

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
            "url": filters.url,
            "version": filters.version,
            "status": filters.status,
            "name": filters.name,
            "name:contains": filters.name_contains,
            "name:exact": filters.name_exact,
            "title": filters.title,
            "title:contains": filters.title_contains,
            "title:exact": filters.title_exact,
            "publisher": filters.publisher,
            "publisher:contains": filters.publisher_contains,
            "publisher:exact": filters.publisher_exact,
            "description": filters.description,
            "description:contains": filters.description_contains,
            "description:exact": filters.description_exact,
            "date": filters.date,
            "effective": filters.effective,
            "jurisdiction": filters.jurisdiction,
            "code": filters.code,
            "definition": filters.definition,
            "subject-type": filters.subject_type,
            "context": filters.context,
            "context-type": filters.context_type,
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
        dto: QuestionnairePatchSchema,
        actor: AuthUser,
        accept: str | None = None,
    ) -> dict:
        """
        Partially update scalar fields on a Questionnaire.

        Rejects with 422 if the patch body is empty. `mode="json"` serialises
        datetimes/dates and the status enum.

        Args:
            resource_id: The questionnaire's public integer ID.
            dto:         Validated patch input; at least one field must be non-None.
            actor:       Authenticated caller — FhirClient stamps updated_by.
            accept:      Content-type preference forwarded to the fhir-server.

        Returns:
            The updated Questionnaire resource dict.

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
        Permanently delete a Questionnaire and its whole item tree.

        Args:
            resource_id: The questionnaire's public integer ID to delete.
            actor:       Authenticated caller (kept for RBAC consistency).
        """
        await self._client.delete(resource_id)
