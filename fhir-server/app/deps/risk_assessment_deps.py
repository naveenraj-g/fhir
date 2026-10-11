from fastapi import Depends, HTTPException, Path, status

from app.di.dependencies.risk_assessment import get_risk_assessment_service
from app.models.risk_assessment.risk_assessment import RiskAssessmentModel
from app.services.risk_assessment_service import RiskAssessmentService


async def resolve_risk_assessment(
    risk_assessment_id: int = Path(..., ge=1, description="Public risk_assessment identifier."),
    risk_assessment_service: RiskAssessmentService = Depends(get_risk_assessment_service),
) -> RiskAssessmentModel:
    """Load risk_assessment by public id or raise 404."""
    q = await risk_assessment_service.get_raw_by_risk_assessment_id(risk_assessment_id)
    if not q:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RiskAssessment not found")
    return q
