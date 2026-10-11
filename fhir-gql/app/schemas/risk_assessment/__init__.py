"""
RiskAssessment schema package — re-exports public input schemas.
"""

from app.schemas.risk_assessment.input import (
    ListRiskAssessmentsSchema,
    RiskAssessmentCreateSchema,
    RiskAssessmentPatchSchema,
)

__all__ = [
    "ListRiskAssessmentsSchema",
    "RiskAssessmentCreateSchema",
    "RiskAssessmentPatchSchema",
]
