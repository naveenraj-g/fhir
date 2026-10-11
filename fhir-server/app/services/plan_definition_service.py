from typing import List, Optional, Tuple

from app.fhir.mappers.plan_definition import to_fhir_plan_definition, to_plain_plan_definition
from app.models.plan_definition.plan_definition import PlanDefinitionModel
from app.repository.plan_definition_repository import PlanDefinitionRepository, PlanDefinitionSearch
from app.schemas.plan_definition import PlanDefinitionCreateSchema, PlanDefinitionPatchSchema


class PlanDefinitionService:
    def __init__(self, repository: PlanDefinitionRepository):
        self.repository = repository

    def _to_fhir(self, plan_definition: PlanDefinitionModel) -> dict:
        return to_fhir_plan_definition(plan_definition)

    def _to_plain(self, plan_definition: PlanDefinitionModel) -> dict:
        return to_plain_plan_definition(plan_definition)

    async def get_raw_by_plan_definition_id(self, plan_definition_id: int) -> Optional[PlanDefinitionModel]:
        return await self.repository.get_by_plan_definition_id(plan_definition_id)

    async def get_me(
        self, user_id: str, org_id: str, search: Optional[PlanDefinitionSearch] = None, limit: int = 50, offset: int = 0
    ) -> Tuple[List[PlanDefinitionModel], int]:
        return await self.repository.get_me(user_id, org_id, search=search, limit=limit, offset=offset)

    async def list_plan_definitions(
        self, user_id: Optional[str] = None, org_id: Optional[str] = None,
        search: Optional[PlanDefinitionSearch] = None, limit: int = 50, offset: int = 0,
    ) -> Tuple[List[PlanDefinitionModel], int]:
        return await self.repository.list(user_id=user_id, org_id=org_id, search=search, limit=limit, offset=offset)

    async def create_plan_definition(
        self, payload: PlanDefinitionCreateSchema, user_id: Optional[str], org_id: Optional[str], created_by: Optional[str]
    ) -> PlanDefinitionModel:
        return await self.repository.create(payload, user_id, org_id, created_by)

    async def patch_plan_definition(
        self, plan_definition_id: int, payload: PlanDefinitionPatchSchema, updated_by: Optional[str]
    ) -> Optional[PlanDefinitionModel]:
        return await self.repository.patch(plan_definition_id, payload, updated_by)

    async def delete_plan_definition(self, plan_definition_id: int) -> None:
        await self.repository.delete(plan_definition_id)
