from typing import List, Optional, Tuple

from app.fhir.mappers.practitioner_role import to_fhir_practitioner_role, to_plain_practitioner_role
from app.models.practitioner_role.practitioner_role import PractitionerRoleModel
from app.repository.practitioner_role_repository import PractitionerRoleRepository
from app.schemas.practitioner_role import PractitionerRoleCreateSchema, PractitionerRolePatchSchema


class PractitionerRoleService:
    def __init__(self, repository: PractitionerRoleRepository):
        self.repository = repository

    def _to_fhir(self, pr: PractitionerRoleModel) -> dict:
        return to_fhir_practitioner_role(pr)

    def _to_plain(self, pr: PractitionerRoleModel) -> dict:
        return to_plain_practitioner_role(pr)

    async def get_raw_by_practitioner_role_id(
        self, practitioner_role_id: int
    ) -> Optional[PractitionerRoleModel]:
        return await self.repository.get_by_practitioner_role_id(practitioner_role_id)

    async def get_me(
        self,
        user_id: str,
        org_id: str,
        active: Optional[bool] = None,
        practitioner_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[PractitionerRoleModel], int]:
        return await self.repository.get_me(
            user_id, org_id,
            active=active, practitioner_id=practitioner_id,
            limit=limit, offset=offset,
        )

    async def list_practitioner_roles(
        self,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        active: Optional[bool] = None,
        practitioner_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[PractitionerRoleModel], int]:
        return await self.repository.list(
            user_id=user_id, org_id=org_id,
            active=active, practitioner_id=practitioner_id,
            limit=limit, offset=offset,
        )

    async def create_practitioner_role(
        self,
        payload: PractitionerRoleCreateSchema,
        user_id: Optional[str],
        org_id: Optional[str],
        created_by: Optional[str],
    ) -> PractitionerRoleModel:
        return await self.repository.create(payload, user_id, org_id, created_by)

    async def patch_practitioner_role(
        self,
        practitioner_role_id: int,
        payload: PractitionerRolePatchSchema,
        updated_by: Optional[str],
    ) -> Optional[PractitionerRoleModel]:
        return await self.repository.patch(practitioner_role_id, payload, updated_by)

    async def delete_practitioner_role(self, practitioner_role_id: int) -> None:
        await self.repository.delete(practitioner_role_id)
