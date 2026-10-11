from fastapi import Depends, HTTPException, Path, status

from app.di.dependencies.questionnaire import get_questionnaire_service
from app.models.questionnaire.questionnaire import QuestionnaireModel
from app.services.questionnaire_service import QuestionnaireService


async def resolve_questionnaire(
    questionnaire_id: int = Path(..., ge=1, description="Public questionnaire identifier."),
    questionnaire_service: QuestionnaireService = Depends(get_questionnaire_service),
) -> QuestionnaireModel:
    """Load questionnaire by public id or raise 404."""
    q = await questionnaire_service.get_raw_by_questionnaire_id(questionnaire_id)
    if not q:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Questionnaire not found")
    return q
