"""
Dependency-injection sub-container for the QuestionnaireResponse domain.

Wires QuestionnaireResponseClient and QuestionnaireResponseService as Factory providers so each request
receives a fresh, stateless instance.
"""

from dependency_injector import containers, providers

from app.fhir_client.questionnaire_response import QuestionnaireResponseClient
from app.services.questionnaire_response_service import QuestionnaireResponseService


class QuestionnaireResponseContainer(containers.DeclarativeContainer):
    """
    DI sub-container for QuestionnaireResponse resources.

    `core` is a DependenciesContainer placeholder replaced by the root Container
    at wiring time, giving access to `core.fhir_client`.
    """

    # Placeholder resolved by the root Container when this sub-container is mounted.
    core = providers.DependenciesContainer()

    # Domain-specific HTTP client for QuestionnaireResponse endpoints on the fhir-server.
    questionnaire_response_client = providers.Factory(
        QuestionnaireResponseClient,
        fhir=core.fhir_client,
    )

    # Business logic service — sits between the router and QuestionnaireResponseClient.
    questionnaire_response_service = providers.Factory(
        QuestionnaireResponseService,
        client=questionnaire_response_client,
    )
