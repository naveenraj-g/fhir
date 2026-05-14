from typing import List, Optional, Tuple

from app.models.patient.patient import PatientModel
from app.repository.patient_repository import PatientRepository
from app.schemas.resources import (
    AddressCreate,
    CommunicationCreate,
    ContactCreate,
    GeneralPractitionerCreate,
    IdentifierCreate,
    LinkCreate,
    NameCreate,
    PatientCreateSchema,
    PatientPatchSchema,
    PhotoCreate,
    TelecomCreate,
)
from app.fhir.mappers.patient import to_fhir_patient, to_plain_patient


class PatientService:
    def __init__(self, repository: PatientRepository):
        self.repository = repository

    # ── Formatters ────────────────────────────────────────────────────────────

    def _to_fhir(self, patient: PatientModel) -> dict:
        return to_fhir_patient(patient)

    def _to_plain(self, patient: PatientModel) -> dict:
        return to_plain_patient(patient)

    # ── Read ──────────────────────────────────────────────────────────────────

    async def get_raw_by_patient_id(self, patient_id: int) -> Optional[PatientModel]:
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

    async def list_patients(
        self,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        family_name: Optional[str] = None,
        given_name: Optional[str] = None,
        gender: Optional[str] = None,
        active: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[PatientModel], int]:
        return await self.repository.list(
            user_id=user_id, org_id=org_id, family_name=family_name,
            given_name=given_name, gender=gender, active=active,
            limit=limit, offset=offset,
        )

    # ── Write ─────────────────────────────────────────────────────────────────

    async def create_patient(
        self,
        payload: PatientCreateSchema,
        user_id: Optional[str],
        org_id: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> PatientModel:
        return await self.repository.create(payload, user_id, org_id, created_by)

    async def patch_patient(
        self, patient_id: int, payload: PatientPatchSchema, updated_by: Optional[str] = None
    ) -> Optional[PatientModel]:
        return await self.repository.patch(patient_id, payload, updated_by)

    async def delete_patient(self, patient_id: int) -> bool:
        return await self.repository.delete(patient_id)

    # ── Sub-resources ─────────────────────────────────────────────────────────

    async def add_name(self, patient_id: int, payload: NameCreate) -> Optional[PatientModel]:
        return await self.repository.add_name(patient_id, payload)

    async def add_identifier(self, patient_id: int, payload: IdentifierCreate) -> Optional[PatientModel]:
        return await self.repository.add_identifier(patient_id, payload)

    async def add_telecom(self, patient_id: int, payload: TelecomCreate) -> Optional[PatientModel]:
        return await self.repository.add_telecom(patient_id, payload)

    async def add_address(self, patient_id: int, payload: AddressCreate) -> Optional[PatientModel]:
        return await self.repository.add_address(patient_id, payload)

    async def add_photo(self, patient_id: int, payload: PhotoCreate) -> Optional[PatientModel]:
        return await self.repository.add_photo(patient_id, payload)

    async def add_contact(self, patient_id: int, payload: ContactCreate) -> Optional[PatientModel]:
        return await self.repository.add_contact(patient_id, payload)

    async def add_communication(
        self, patient_id: int, payload: CommunicationCreate
    ) -> Optional[PatientModel]:
        return await self.repository.add_communication(patient_id, payload)

    async def add_general_practitioner(
        self, patient_id: int, payload: GeneralPractitionerCreate
    ) -> Optional[PatientModel]:
        return await self.repository.add_general_practitioner(patient_id, payload)

    async def add_link(self, patient_id: int, payload: LinkCreate) -> Optional[PatientModel]:
        return await self.repository.add_link(patient_id, payload)
