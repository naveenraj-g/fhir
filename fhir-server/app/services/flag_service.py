from typing import List, Optional, Tuple

from app.fhir.mappers.flag import to_fhir_flag, to_plain_flag
from app.models.flag.flag import FlagModel
from app.repository.flag_repository import FlagRepository, FlagSearch
from app.schemas.flag import FlagCreateSchema, FlagPatchSchema


class FlagService:
    def __init__(self, repository: FlagRepository):
        self.repository = repository

    def _to_fhir(self, flag: FlagModel) -> dict:
        return to_fhir_flag(flag)

    def _to_plain(self, flag: FlagModel) -> dict:
        return to_plain_flag(flag)

    async def get_raw_by_flag_id(self, flag_id: int) -> Optional[FlagModel]:
        return await self.repository.get_by_flag_id(flag_id)

    async def get_me(
        self, user_id: str, org_id: str, search: Optional[FlagSearch] = None, limit: int = 50, offset: int = 0
    ) -> Tuple[List[FlagModel], int]:
        return await self.repository.get_me(user_id, org_id, search=search, limit=limit, offset=offset)

    async def list_flags(
        self, user_id: Optional[str] = None, org_id: Optional[str] = None,
        search: Optional[FlagSearch] = None, limit: int = 50, offset: int = 0,
    ) -> Tuple[List[FlagModel], int]:
        return await self.repository.list(user_id=user_id, org_id=org_id, search=search, limit=limit, offset=offset)

    async def create_flag(
        self, payload: FlagCreateSchema, user_id: Optional[str], org_id: Optional[str], created_by: Optional[str]
    ) -> FlagModel:
        return await self.repository.create(payload, user_id, org_id, created_by)

    async def patch_flag(
        self, flag_id: int, payload: FlagPatchSchema, updated_by: Optional[str]
    ) -> Optional[FlagModel]:
        return await self.repository.patch(flag_id, payload, updated_by)

    async def delete_flag(self, flag_id: int) -> None:
        await self.repository.delete(flag_id)
