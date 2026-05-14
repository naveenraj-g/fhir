from typing import Optional

from app.models.patient import PatientModel
from app.repository.patient_repository import PatientRepository
from app.schemas.resources import (
    PatientCreateSchema,
    PatientPatchSchema,
    IdentifierCreate,
    TelecomCreate,
    AddressCreate,
)
from app.fhir.mappers.patient import to_fhir_patient, to_plain_patient


class PatientService:
    def __init__(self, repository: PatientRepository):
        self.repository = repository

    # ── Formatters (called by route layer after content negotiation) ──────

    def _to_fhir(self, patient: PatientModel) -> dict:
        return to_fhir_patient(patient)

    def _to_plain(self, patient: PatientModel) -> dict:
        return to_plain_patient(patient)

    # ── Read ──────────────────────────────────────────────────────────────

    async def get_raw_by_patient_id(self, patient_id: int) -> Optional[PatientModel]:
        """Raw ORM model — used by the auth ownership dependency."""
        return await self.repository.get_by_patient_id(patient_id)

    async def get_raw_by_user_id(self, user_id: str) -> Optional[PatientModel]:
        return await self.repository.get_by_user_id(user_id)

    async def get_patient(self, patient_id: int) -> Optional[PatientModel]:
        return await self.repository.get_by_patient_id(patient_id)

    async def get_patient_in_org(
        self, patient_id: int, user_id: str, org_id: str
    ) -> Optional[PatientModel]:
        return await self.repository.get_by_patient_id_in_org(patient_id, user_id, org_id)

    async def get_me(self, user_id: str, org_id: str) -> Optional[PatientModel]:
        return await self.repository.get_me(user_id, org_id)

    async def list_patients(self) -> list[PatientModel]:
        return await self.repository.list()

    # ── Write ─────────────────────────────────────────────────────────────

    async def create_patient(
        self, payload: PatientCreateSchema, user_id: str, org_id: Optional[str] = None
    ) -> PatientModel:
        return await self.repository.create(payload, user_id, org_id)

    async def patch_patient(
        self, patient_id: int, payload: PatientPatchSchema
    ) -> Optional[PatientModel]:
        return await self.repository.patch(patient_id, payload)

    async def delete_patient(self, patient_id: int) -> bool:
        return await self.repository.delete(patient_id)

    # ── Sub-resources ─────────────────────────────────────────────────────

    async def add_identifier(
        self, patient_id: int, payload: IdentifierCreate
    ) -> Optional[PatientModel]:
        return await self.repository.add_identifier(patient_id, payload)

    async def add_telecom(
        self, patient_id: int, payload: TelecomCreate
    ) -> Optional[PatientModel]:
        return await self.repository.add_telecom(patient_id, payload)

    async def add_address(
        self, patient_id: int, payload: AddressCreate
    ) -> Optional[PatientModel]:
        return await self.repository.add_address(patient_id, payload)
