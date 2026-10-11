"""
Dependency-injection sub-container for the Questionnaire domain.

Wires QuestionnaireClient and QuestionnaireService as Factory providers so each request
receives a fresh, stateless instance.
"""

from dependency_injector import containers, providers

from app.fhir_client.questionnaire import QuestionnaireClient
from app.services.questionnaire_service import QuestionnaireService


class QuestionnaireContainer(containers.DeclarativeContainer):
    """
    DI sub-container for Questionnaire resources.

    `core` is a DependenciesContainer placeholder replaced by the root Container
    at wiring time, giving access to `core.fhir_client`.
    """

    # Placeholder resolved by the root Container when this sub-container is mounted.
    core = providers.DependenciesContainer()

    # Domain-specific HTTP client for Questionnaire endpoints on the fhir-server.
    questionnaire_client = providers.Factory(
        QuestionnaireClient,
        fhir=core.fhir_client,
    )

    # Business logic service — sits between the router and QuestionnaireClient.
    questionnaire_service = providers.Factory(
        QuestionnaireService,
        client=questionnaire_client,
    )
