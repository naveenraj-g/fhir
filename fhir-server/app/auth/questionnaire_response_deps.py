"""
QuestionnaireResponse ownership dependency.

get_authorized_questionnaire_response — reusable FastAPI dependency that:
  1. Resolves the public questionnaire_response_id from the URL path.
  2. Fetches the QuestionnaireResponseModel from the database.
  3. Verifies that qr.user_id matches the authenticated user's sub claim.
  4. Returns the loaded model so route handlers don't need another DB hit.
"""

from fastapi import Depends, HTTPException, Request, Path, status

from app.models.questionnaire_response.questionnaire_response import (
    QuestionnaireResponseModel,
)
from app.services.questionnaire_response_service import QuestionnaireResponseService
from app.di.dependencies.questionnaire_response import (
    get_questionnaire_response_service,
)


async def get_authorized_questionnaire_response(
    questionnaire_response_id: int = Path(
        ..., ge=1, description="Public questionnaire response identifier."
    ),
    request: Request = ...,
    qr_service: QuestionnaireResponseService = Depends(
        get_questionnaire_response_service
    ),
) -> QuestionnaireResponseModel:
    """
    Dependency that resolves and ownership-validates a QuestionnaireResponse.

    Raises:
        404 — response not found.
        403 — authenticated user does not own this response.
    """
    user_id: str = request.state.user.get("sub")

    qr = await qr_service.get_raw_by_qr_id(questionnaire_response_id)
    if not qr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="QuestionnaireResponse not found",
        )

    if qr.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    return qr
