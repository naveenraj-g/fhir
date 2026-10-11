"""
Dependency-injection sub-container for the RiskAssessment domain.

Wires RiskAssessmentClient and RiskAssessmentService as Factory providers so each request
receives a fresh, stateless instance.
"""

from dependency_injector import containers, providers

from app.fhir_client.risk_assessment import RiskAssessmentClient
from app.services.risk_assessment_service import RiskAssessmentService


class RiskAssessmentContainer(containers.DeclarativeContainer):
    """
    DI sub-container for RiskAssessment resources.

    `core` is a DependenciesContainer placeholder replaced by the root Container
    at wiring time, giving access to `core.fhir_client`.
    """

    # Placeholder resolved by the root Container when this sub-container is mounted.
    core = providers.DependenciesContainer()

    # Domain-specific HTTP client for RiskAssessment endpoints on the fhir-server.
    risk_assessment_client = providers.Factory(
        RiskAssessmentClient,
        fhir=core.fhir_client,
    )

    # Business logic service — sits between the router and RiskAssessmentClient.
    risk_assessment_service = providers.Factory(
        RiskAssessmentService,
        client=risk_assessment_client,
    )
