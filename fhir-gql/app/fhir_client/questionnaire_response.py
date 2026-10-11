"""
FHIR client for QuestionnaireResponse resources.

Thin wrapper around the shared FhirClient that knows the fhir-server path for
QuestionnaireResponses. No business logic lives here — all validation and rules
belong in QuestionnaireResponseService.

A QuestionnaireResponse records the answers given to a Questionnaire: a
recursive tree of items, each with zero or more answers (typed value[x]) and
optionally nested items, plus who answered (author/source), for whom (subject),
when (authored) and in which encounter.

Reference: https://www.hl7.org/fhir/R4/questionnaireresponse.html
"""

from app.auth.models import AuthUser
from app.fhir_client.client import FhirClient

# Confirmed in fhir-server routers prefix (app/routers/__init__.py: "/questionnaire-responses").
_PATH = "/questionnaire-responses"


class QuestionnaireResponseClient:
    """
    Domain-specific HTTP client for QuestionnaireResponse resources.

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
        POST /questionnaire-responses — record a new QuestionnaireResponse with its item tree.

        basedOn, partOf and the whole recursive `item` tree (answers and items
        nested under answers) travel in the single payload.

        Args:
            data:   Serialised QuestionnaireResponseCreateSchema (exclude_none=True, mode="json").
            actor:  Authenticated caller — FhirClient stamps created_by from actor.sub.
            accept: Content-type preference forwarded to the fhir-server.

        Returns:
            The newly created QuestionnaireResponse as a dict (plain JSON or FHIR R4).
        """
        return await self._fhir.post(_PATH, data, actor, accept=accept)

    async def get_by_id(self, resource_id: int, accept: str | None = None) -> dict:
        """
        GET /questionnaire-responses/{resource_id} — fetch one by public ID.

        Args:
            resource_id: The public integer questionnaire_response_id.
            accept:      Content-type preference forwarded to the fhir-server.

        Returns:
            The QuestionnaireResponse dict with the whole item tree.
        """
        return await self._fhir.get(f"{_PATH}/{resource_id}", accept=accept)

    async def list(self, accept: str | None = None, **params) -> dict:
        """
        GET /questionnaire-responses — search with the FHIR R4 search parameters.

        Strips None values (and empty lists) from **params before forwarding.
        Hyphenated and underscore-prefixed names (`based-on`, `part-of`, `_id`,
        `_lastUpdated`) are passed through verbatim by unpacking a dict
        (`**{"based-on": "ServiceRequest/1"}`). List values (`authored`,
        `_lastUpdated`) are sent as repeated query keys, which the fhir-server
        treats as AND.

        Supported params: _id, identifier, questionnaire, status, subject, patient,
        encounter, author, source, based-on, part-of, authored, _lastUpdated,
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
        PATCH /questionnaire-responses/{resource_id} — partially update scalar/reference fields.

        Items and answers are NOT patchable — delete and re-create to change those.

        Args:
            resource_id: The public integer questionnaire_response_id.
            data:        Serialised QuestionnaireResponsePatchSchema (exclude_none=True, mode="json").
            actor:       Authenticated caller — FhirClient stamps updated_by.
            accept:      Content-type preference forwarded to the fhir-server.

        Returns:
            The updated QuestionnaireResponse resource dict.
        """
        return await self._fhir.patch(f"{_PATH}/{resource_id}", data, actor, accept=accept)

    async def delete(self, resource_id: int) -> None:
        """
        DELETE /questionnaire-responses/{resource_id} — permanently remove a response.

        The fhir-server cascades the delete to basedOn, partOf and every item/answer row.

        Args:
            resource_id: The public integer questionnaire_response_id to delete.
        """
        await self._fhir.delete(f"{_PATH}/{resource_id}")
