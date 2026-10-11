from dependency_injector.wiring import inject, Provide
from fastapi import Depends

from app.di.container import Container
from app.services.risk_assessment_service import RiskAssessmentService


@inject
def get_risk_assessment_service(
    service: RiskAssessmentService = Depends(Provide[Container.risk_assessment.risk_assessment_service]),
) -> RiskAssessmentService:
    return service
