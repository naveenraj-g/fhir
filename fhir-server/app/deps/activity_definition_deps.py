from fastapi import Depends, HTTPException, Path, status

from app.di.dependencies.activity_definition import get_activity_definition_service
from app.models.activity_definition.activity_definition import ActivityDefinitionModel
from app.services.activity_definition_service import ActivityDefinitionService


async def resolve_activity_definition(
    activity_definition_id: int = Path(..., ge=1, description="Public activity definition identifier."),
    activity_definition_service: ActivityDefinitionService = Depends(get_activity_definition_service),
) -> ActivityDefinitionModel:
    """Load activity definition by public id or raise 404."""
    q = await activity_definition_service.get_raw_by_activity_definition_id(activity_definition_id)
    if not q:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ActivityDefinition not found")
    return q
