from typing import Optional

from app.models.practitioner import PractitionerModel
from app.repository.practitioner_repository import PractitionerRepository
from app.schemas.practitioner import (
    PractitionerCreateSchema,
    PractitionerPatchSchema,
    PractitionerIdentifierCreate,
    PractitionerTelecomCreate,
    PractitionerAddressCreate,
    PractitionerQualificationCreate,
)
from app.fhir.mappers.practitioner import to_fhir_practitioner, to_plain_practitioner


class PractitionerService:
    def __init__(self, repository: PractitionerRepository):
        self.repository = repository

    # ── Formatters (called by route layer after content negotiation) ──────

    def _to_fhir(self, practitioner: PractitionerModel) -> dict:
        return to_fhir_practitioner(practitioner)

    def _to_plain(self, practitioner: PractitionerModel) -> dict:
        return to_plain_practitioner(practitioner)

    # ── Read ──────────────────────────────────────────────────────────────

    async def get_raw_by_practitioner_id(self, practitioner_id: int) -> Optional[PractitionerModel]:
        """Raw ORM model — used by the auth ownership dependency."""
        return await self.repository.get_by_practitioner_id(practitioner_id)

    async def get_raw_by_user_id(self, user_id: str) -> Optional[PractitionerModel]:
        return await self.repository.get_by_user_id(user_id)

    async def get_practitioner(self, practitioner_id: int) -> Optional[PractitionerModel]:
        return await self.repository.get_by_practitioner_id(practitioner_id)

    async def get_me(self, user_id: str, org_id: str) -> Optional[PractitionerModel]:
        return await self.repository.get_me(user_id, org_id)

    async def list_practitioners(self) -> list[PractitionerModel]:
        return await self.repository.list()

    # ── Write ─────────────────────────────────────────────────────────────

    async def create_practitioner(
        self, payload: PractitionerCreateSchema, user_id: str, org_id: Optional[str] = None
    ) -> PractitionerModel:
        return await self.repository.create(payload, user_id, org_id)

    async def patch_practitioner(
        self, practitioner_id: int, payload: PractitionerPatchSchema
    ) -> Optional[PractitionerModel]:
        return await self.repository.patch(practitioner_id, payload)

    async def delete_practitioner(self, practitioner_id: int) -> bool:
        return await self.repository.delete(practitioner_id)

    # ── Sub-resources ─────────────────────────────────────────────────────

    async def add_identifier(
        self, practitioner_id: int, payload: PractitionerIdentifierCreate
    ) -> Optional[PractitionerModel]:
        return await self.repository.add_identifier(practitioner_id, payload)

    async def add_telecom(
        self, practitioner_id: int, payload: PractitionerTelecomCreate
    ) -> Optional[PractitionerModel]:
        return await self.repository.add_telecom(practitioner_id, payload)

    async def add_address(
        self, practitioner_id: int, payload: PractitionerAddressCreate
    ) -> Optional[PractitionerModel]:
        return await self.repository.add_address(practitioner_id, payload)

    async def add_qualification(
        self, practitioner_id: int, payload: PractitionerQualificationCreate
    ) -> Optional[PractitionerModel]:
        return await self.repository.add_qualification(practitioner_id, payload)
