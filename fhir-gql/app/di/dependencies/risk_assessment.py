"""
FastAPI dependency bridge for RiskAssessmentService.

Translates the dependency-injector provider into a FastAPI Depends()-compatible
callable so route handlers can declare:
    service: RiskAssessmentService = Depends(get_risk_assessment_service)
"""

from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.di.container import Container
from app.services.risk_assessment_service import RiskAssessmentService


@inject
def get_risk_assessment_service(
    service: RiskAssessmentService = Depends(Provide[Container.risk_assessment.risk_assessment_service]),
) -> RiskAssessmentService:
    """
    Resolve RiskAssessmentService from the DI container for use in route handlers.

    dependency-injector handles instantiation and wires the RiskAssessmentClient
    (and its underlying FhirClient) automatically.
    """
    return service
