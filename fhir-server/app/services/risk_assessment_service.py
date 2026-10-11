from typing import List, Optional, Tuple

from app.fhir.mappers.risk_assessment import to_fhir_risk_assessment, to_plain_risk_assessment
from app.models.risk_assessment.risk_assessment import RiskAssessmentModel
from app.repository.risk_assessment_repository import RiskAssessmentRepository, RiskAssessmentSearch
from app.schemas.risk_assessment import RiskAssessmentCreateSchema, RiskAssessmentPatchSchema


class RiskAssessmentService:
    def __init__(self, repository: RiskAssessmentRepository):
        self.repository = repository

    def _to_fhir(self, ra: RiskAssessmentModel) -> dict:
        return to_fhir_risk_assessment(ra)

    def _to_plain(self, ra: RiskAssessmentModel) -> dict:
        return to_plain_risk_assessment(ra)

    async def get_raw_by_risk_assessment_id(self, risk_assessment_id: int) -> Optional[RiskAssessmentModel]:
        return await self.repository.get_by_risk_assessment_id(risk_assessment_id)

    async def get_me(
        self, user_id: str, org_id: str, search: Optional[RiskAssessmentSearch] = None,
        limit: int = 50, offset: int = 0,
    ) -> Tuple[List[RiskAssessmentModel], int]:
        return await self.repository.get_me(user_id, org_id, search=search, limit=limit, offset=offset)

    async def list_risk_assessments(
        self, user_id: Optional[str] = None, org_id: Optional[str] = None,
        search: Optional[RiskAssessmentSearch] = None, limit: int = 50, offset: int = 0,
    ) -> Tuple[List[RiskAssessmentModel], int]:
        return await self.repository.list(user_id=user_id, org_id=org_id, search=search, limit=limit, offset=offset)

    async def create_risk_assessment(
        self, payload: RiskAssessmentCreateSchema, user_id: Optional[str],
        org_id: Optional[str], created_by: Optional[str],
    ) -> RiskAssessmentModel:
        return await self.repository.create(payload, user_id, org_id, created_by)

    async def patch_risk_assessment(
        self, risk_assessment_id: int, payload: RiskAssessmentPatchSchema, updated_by: Optional[str]
    ) -> Optional[RiskAssessmentModel]:
        return await self.repository.patch(risk_assessment_id, payload, updated_by)

    async def delete_risk_assessment(self, risk_assessment_id: int) -> None:
        await self.repository.delete(risk_assessment_id)
