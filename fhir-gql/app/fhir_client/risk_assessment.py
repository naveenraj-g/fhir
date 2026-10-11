"""
FHIR client for RiskAssessment resources.

Thin wrapper around the shared FhirClient that knows the fhir-server path for
RiskAssessments. No business logic lives here — all validation and rules belong
in RiskAssessmentService.

A RiskAssessment is an assessment of the likely outcome(s) for a patient or
group: the method used, when it was made, who performed it, the basis for it,
and one or more predictions (outcome, probability, qualitative risk, timeframe,
rationale) plus suggested mitigation.

Reference: https://www.hl7.org/fhir/R4/riskassessment.html
"""

from app.auth.models import AuthUser
from app.fhir_client.client import FhirClient

# Confirmed in fhir-server routers prefix (app/routers/__init__.py: "/risk-assessments").
_PATH = "/risk-assessments"


class RiskAssessmentClient:
    """
    Domain-specific HTTP client for RiskAssessment resources.

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
        POST /risk-assessments — record a new RiskAssessment.

        All child arrays (identifier, reasonCode, reasonReference, basis,
        prediction, note) travel in the single payload.

        Args:
            data:   Serialised RiskAssessmentCreateSchema (exclude_none=True, mode="json").
            actor:  Authenticated caller — FhirClient stamps created_by from actor.sub.
            accept: Content-type preference forwarded to the fhir-server.

        Returns:
            The newly created RiskAssessment as a dict (plain JSON or FHIR R4).
        """
        return await self._fhir.post(_PATH, data, actor, accept=accept)

    async def get_by_id(self, resource_id: int, accept: str | None = None) -> dict:
        """
        GET /risk-assessments/{resource_id} — fetch one by public ID.

        Args:
            resource_id: The public integer risk_assessment_id.
            accept:      Content-type preference forwarded to the fhir-server.

        Returns:
            The RiskAssessment dict with all child arrays populated.
        """
        return await self._fhir.get(f"{_PATH}/{resource_id}", accept=accept)

    async def list(self, accept: str | None = None, **params) -> dict:
        """
        GET /risk-assessments — search with the FHIR R4 search parameters.

        Strips None values (and empty lists) from **params before forwarding.
        Underscore-prefixed names (`_id`, `_lastUpdated`) are passed through
        verbatim by unpacking a dict (`**{"_id": "380000"}`). List values (`date`,
        `probability`, `_lastUpdated`) are sent as repeated query keys, which the
        fhir-server treats as AND.

        Supported params: _id, identifier, status, method, subject, patient,
        encounter, condition, performer, date, probability, risk, _lastUpdated,
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
        PATCH /risk-assessments/{resource_id} — partially update scalar/reference fields.

        Child arrays are NOT patchable — delete and re-create to change those.

        Args:
            resource_id: The public integer risk_assessment_id.
            data:        Serialised RiskAssessmentPatchSchema (exclude_none=True, mode="json").
            actor:       Authenticated caller — FhirClient stamps updated_by.
            accept:      Content-type preference forwarded to the fhir-server.

        Returns:
            The updated RiskAssessment resource dict.
        """
        return await self._fhir.patch(f"{_PATH}/{resource_id}", data, actor, accept=accept)

    async def delete(self, resource_id: int) -> None:
        """
        DELETE /risk-assessments/{resource_id} — permanently remove a RiskAssessment.

        The fhir-server cascades the delete to every child row.

        Args:
            resource_id: The public integer risk_assessment_id to delete.
        """
        await self._fhir.delete(f"{_PATH}/{resource_id}")
