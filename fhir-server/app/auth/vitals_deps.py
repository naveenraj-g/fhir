from fastapi import Depends, HTTPException, Path, Request, status

from app.di.dependencies.vitals import get_vitals_service
from app.models.vitals.vitals import VitalsModel
from app.services.vitals_service import VitalsService


async def get_authorized_vitals(
    vitals_id: int = Path(..., ge=1, description="Public vitals identifier."),
    request: Request = ...,
    vitals_service: VitalsService = Depends(get_vitals_service),
) -> VitalsModel:
    user_id: str = request.state.user.get("sub")

    vitals = await vitals_service.get_raw_by_vitals_id(vitals_id)
    if not vitals:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vitals not found")

    if vitals.user_id and vitals.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return vitals
