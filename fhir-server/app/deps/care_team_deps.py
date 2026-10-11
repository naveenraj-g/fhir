from fastapi import Depends, HTTPException, Path, status

from app.di.dependencies.care_team import get_care_team_service
from app.models.care_team.care_team import CareTeamModel
from app.services.care_team_service import CareTeamService


async def resolve_care_team(
    care_team_id: int = Path(..., ge=1, description="Public care team identifier."),
    care_team_service: CareTeamService = Depends(get_care_team_service),
) -> CareTeamModel:
    """Load care team by public id or raise 404."""
    q = await care_team_service.get_raw_by_care_team_id(care_team_id)
    if not q:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CareTeam not found")
    return q
