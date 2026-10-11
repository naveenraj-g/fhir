"""
FHIR client for Questionnaire resources.

Thin wrapper around the shared FhirClient that knows the fhir-server path for
Questionnaires. No business logic lives here — all validation and rules belong
in QuestionnaireService.

A Questionnaire is a structured set of questions (a form definition): a
recursive tree of groups, questions and display items with answer options,
initial values and enableWhen logic, plus publication metadata (url, version,
status, publisher, jurisdiction, useContext, ...).

Reference: https://www.hl7.org/fhir/R4/questionnaire.html
"""

from app.auth.models import AuthUser
from app.fhir_client.client import FhirClient

# Confirmed in fhir-server routers prefix (app/routers/__init__.py: "/questionnaires").
_PATH = "/questionnaires"


class QuestionnaireClient:
    """
    Domain-specific HTTP client for Questionnaire resources.

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
        POST /questionnaires — create a new Questionnaire with its full item tree.

        All child arrays (identifier, subject_type, contact, use_context,
        jurisdiction, code) and the recursive `item` tree (with code,
        enable_when, answer_option, initial) travel in the single payload — no
        separate sub-resource routes exist.

        Args:
            data:   Serialised QuestionnaireCreateSchema (exclude_none=True, mode="json").
            actor:  Authenticated caller — FhirClient stamps created_by from actor.sub.
            accept: Content-type preference forwarded to the fhir-server.

        Returns:
            The newly created Questionnaire as a dict (plain JSON or FHIR R4).
        """
        return await self._fhir.post(_PATH, data, actor, accept=accept)

    async def get_by_id(self, resource_id: int, accept: str | None = None) -> dict:
        """
        GET /questionnaires/{resource_id} — fetch one Questionnaire by public ID.

        Args:
            resource_id: The questionnaire's public integer questionnaire_id.
            accept:      Content-type preference forwarded to the fhir-server.

        Returns:
            The Questionnaire dict with the whole item tree populated.
        """
        return await self._fhir.get(f"{_PATH}/{resource_id}", accept=accept)

    async def list(self, accept: str | None = None, **params) -> dict:
        """
        GET /questionnaires — search Questionnaires with the FHIR R4 search parameters.

        Strips None values (and empty lists) from **params before forwarding.
        Hyphenated, underscore-prefixed and modifier parameter names
        (`subject-type`, `context-type`, `_id`, `_lastUpdated`, `name:contains`,
        `title:exact`, ...) are passed through verbatim by unpacking a dict
        (`**{"name:contains": "phq"}`). List values (`date`, `effective`,
        `_lastUpdated`) are sent as repeated query keys, which the fhir-server
        treats as AND.

        Supported params: _id, identifier, url, version, status, name[:contains|:exact],
        title[:...], publisher[:...], description[:...], date, effective, jurisdiction,
        code, definition, subject-type, context, context-type, _lastUpdated,
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
        PATCH /questionnaires/{resource_id} — partially update scalar fields.

        The item tree and child arrays are NOT patchable — delete and
        re-create (or publish a new version) to change those.

        Args:
            resource_id: The questionnaire's public integer questionnaire_id.
            data:        Serialised QuestionnairePatchSchema (exclude_none=True, mode="json").
            actor:       Authenticated caller — FhirClient stamps updated_by.
            accept:      Content-type preference forwarded to the fhir-server.

        Returns:
            The updated Questionnaire resource dict.
        """
        return await self._fhir.patch(f"{_PATH}/{resource_id}", data, actor, accept=accept)

    async def delete(self, resource_id: int) -> None:
        """
        DELETE /questionnaires/{resource_id} — permanently remove a Questionnaire.

        The fhir-server cascades the delete to every child row, including the
        whole item tree.

        Args:
            resource_id: The questionnaire's public integer questionnaire_id to delete.
        """
        await self._fhir.delete(f"{_PATH}/{resource_id}")
