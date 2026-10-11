from fastapi import Depends, HTTPException, Path, status

from app.di.dependencies.flag import get_flag_service
from app.models.flag.flag import FlagModel
from app.services.flag_service import FlagService


async def resolve_flag(
    flag_id: int = Path(..., ge=1, description="Public flag identifier."),
    flag_service: FlagService = Depends(get_flag_service),
) -> FlagModel:
    """Load flag by public id or raise 404."""
    q = await flag_service.get_raw_by_flag_id(flag_id)
    if not q:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flag not found")
    return q
