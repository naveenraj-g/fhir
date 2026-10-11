from typing import List, Optional, Tuple

from app.fhir.mappers.activity_definition import to_fhir_activity_definition, to_plain_activity_definition
from app.models.activity_definition.activity_definition import ActivityDefinitionModel
from app.repository.activity_definition_repository import ActivityDefinitionRepository, ActivityDefinitionSearch
from app.schemas.activity_definition import ActivityDefinitionCreateSchema, ActivityDefinitionPatchSchema


class ActivityDefinitionService:
    def __init__(self, repository: ActivityDefinitionRepository):
        self.repository = repository

    def _to_fhir(self, activity_definition: ActivityDefinitionModel) -> dict:
        return to_fhir_activity_definition(activity_definition)

    def _to_plain(self, activity_definition: ActivityDefinitionModel) -> dict:
        return to_plain_activity_definition(activity_definition)

    async def get_raw_by_activity_definition_id(self, activity_definition_id: int) -> Optional[ActivityDefinitionModel]:
        return await self.repository.get_by_activity_definition_id(activity_definition_id)

    async def get_me(
        self, user_id: str, org_id: str, search: Optional[ActivityDefinitionSearch] = None, limit: int = 50, offset: int = 0
    ) -> Tuple[List[ActivityDefinitionModel], int]:
        return await self.repository.get_me(user_id, org_id, search=search, limit=limit, offset=offset)

    async def list_activity_definitions(
        self, user_id: Optional[str] = None, org_id: Optional[str] = None,
        search: Optional[ActivityDefinitionSearch] = None, limit: int = 50, offset: int = 0,
    ) -> Tuple[List[ActivityDefinitionModel], int]:
        return await self.repository.list(user_id=user_id, org_id=org_id, search=search, limit=limit, offset=offset)

    async def create_activity_definition(
        self, payload: ActivityDefinitionCreateSchema, user_id: Optional[str], org_id: Optional[str], created_by: Optional[str]
    ) -> ActivityDefinitionModel:
        return await self.repository.create(payload, user_id, org_id, created_by)

    async def patch_activity_definition(
        self, activity_definition_id: int, payload: ActivityDefinitionPatchSchema, updated_by: Optional[str]
    ) -> Optional[ActivityDefinitionModel]:
        return await self.repository.patch(activity_definition_id, payload, updated_by)

    async def delete_activity_definition(self, activity_definition_id: int) -> None:
        await self.repository.delete(activity_definition_id)
