from typing import List, Optional, Tuple

from app.fhir.mappers.care_team import to_fhir_care_team, to_plain_care_team
from app.models.care_team.care_team import CareTeamModel
from app.repository.care_team_repository import CareTeamRepository, CareTeamSearch
from app.schemas.care_team import CareTeamCreateSchema, CareTeamPatchSchema


class CareTeamService:
    def __init__(self, repository: CareTeamRepository):
        self.repository = repository

    def _to_fhir(self, care_team: CareTeamModel) -> dict:
        return to_fhir_care_team(care_team)

    def _to_plain(self, care_team: CareTeamModel) -> dict:
        return to_plain_care_team(care_team)

    async def get_raw_by_care_team_id(self, care_team_id: int) -> Optional[CareTeamModel]:
        return await self.repository.get_by_care_team_id(care_team_id)

    async def get_me(
        self, user_id: str, org_id: str, search: Optional[CareTeamSearch] = None, limit: int = 50, offset: int = 0
    ) -> Tuple[List[CareTeamModel], int]:
        return await self.repository.get_me(user_id, org_id, search=search, limit=limit, offset=offset)

    async def list_care_teams(
        self, user_id: Optional[str] = None, org_id: Optional[str] = None,
        search: Optional[CareTeamSearch] = None, limit: int = 50, offset: int = 0,
    ) -> Tuple[List[CareTeamModel], int]:
        return await self.repository.list(user_id=user_id, org_id=org_id, search=search, limit=limit, offset=offset)

    async def create_care_team(
        self, payload: CareTeamCreateSchema, user_id: Optional[str], org_id: Optional[str], created_by: Optional[str]
    ) -> CareTeamModel:
        return await self.repository.create(payload, user_id, org_id, created_by)

    async def patch_care_team(
        self, care_team_id: int, payload: CareTeamPatchSchema, updated_by: Optional[str]
    ) -> Optional[CareTeamModel]:
        return await self.repository.patch(care_team_id, payload, updated_by)

    async def delete_care_team(self, care_team_id: int) -> None:
        await self.repository.delete(care_team_id)
