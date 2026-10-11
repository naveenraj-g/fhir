from fastapi import Depends, HTTPException, Path, status

from app.di.dependencies.plan_definition import get_plan_definition_service
from app.models.plan_definition.plan_definition import PlanDefinitionModel
from app.services.plan_definition_service import PlanDefinitionService


async def resolve_plan_definition(
    plan_definition_id: int = Path(..., ge=1, description="Public plan definition identifier."),
    plan_definition_service: PlanDefinitionService = Depends(get_plan_definition_service),
) -> PlanDefinitionModel:
    """Load plan definition by public id or raise 404."""
    q = await plan_definition_service.get_raw_by_plan_definition_id(plan_definition_id)
    if not q:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PlanDefinition not found")
    return q
