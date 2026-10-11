from typing import List, Optional, Tuple

from app.fhir.mappers.questionnaire import to_fhir_questionnaire, to_plain_questionnaire
from app.models.questionnaire.questionnaire import QuestionnaireModel
from app.repository.questionnaire_repository import QuestionnaireRepository, QuestionnaireSearch
from app.schemas.questionnaire import QuestionnaireCreateSchema, QuestionnairePatchSchema


class QuestionnaireService:
    def __init__(self, repository: QuestionnaireRepository):
        self.repository = repository

    def _to_fhir(self, q: QuestionnaireModel) -> dict:
        return to_fhir_questionnaire(q)

    def _to_plain(self, q: QuestionnaireModel) -> dict:
        return to_plain_questionnaire(q)

    async def get_raw_by_questionnaire_id(self, questionnaire_id: int) -> Optional[QuestionnaireModel]:
        return await self.repository.get_by_questionnaire_id(questionnaire_id)

    async def get_me(
        self, user_id: str, org_id: str, search: Optional[QuestionnaireSearch] = None,
        limit: int = 50, offset: int = 0,
    ) -> Tuple[List[QuestionnaireModel], int]:
        return await self.repository.get_me(user_id, org_id, search=search, limit=limit, offset=offset)

    async def list_questionnaires(
        self, user_id: Optional[str] = None, org_id: Optional[str] = None,
        search: Optional[QuestionnaireSearch] = None, limit: int = 50, offset: int = 0,
    ) -> Tuple[List[QuestionnaireModel], int]:
        return await self.repository.list(user_id=user_id, org_id=org_id, search=search, limit=limit, offset=offset)

    async def create_questionnaire(
        self, payload: QuestionnaireCreateSchema, user_id: Optional[str],
        org_id: Optional[str], created_by: Optional[str],
    ) -> QuestionnaireModel:
        return await self.repository.create(payload, user_id, org_id, created_by)

    async def patch_questionnaire(
        self, questionnaire_id: int, payload: QuestionnairePatchSchema, updated_by: Optional[str]
    ) -> Optional[QuestionnaireModel]:
        return await self.repository.patch(questionnaire_id, payload, updated_by)

    async def delete_questionnaire(self, questionnaire_id: int) -> None:
        await self.repository.delete(questionnaire_id)
