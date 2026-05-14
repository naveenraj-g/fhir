from typing import Optional, List

from app.core.references import parse_reference, resolve_subject
from app.models.encounter.encounter import EncounterModel
from app.models.enums import SubjectReferenceType
from app.repository.encounter_repository import EncounterRepository
from app.schemas.encounter import EncounterCreateSchema, EncounterPatchSchema
from app.fhir.mappers.encounter import to_fhir_encounter, to_plain_encounter
from app.services.patient_service import PatientService


class EncounterService:
    def __init__(self, repository: EncounterRepository, patient_service: PatientService):
        self.repository = repository
        self.patient_service = patient_service

    # ── Formatters (called by route layer after content negotiation) ──────

    def _to_fhir(self, encounter: EncounterModel) -> dict:
        return to_fhir_encounter(encounter)

    def _to_plain(self, encounter: EncounterModel) -> dict:
        return to_plain_encounter(encounter)

    # ── Read ──────────────────────────────────────────────────────────────

    async def get_raw_by_encounter_id(
        self, encounter_id: int
    ) -> Optional[EncounterModel]:
        """Raw ORM model — used by the auth ownership dependency."""
        return await self.repository.get_by_encounter_id(encounter_id)

    async def get_encounter(self, encounter_id: int) -> Optional[EncounterModel]:
        return await self.repository.get_by_encounter_id(encounter_id)

    async def get_me(self, user_id: str, org_id: str) -> List[EncounterModel]:
        return await self.repository.get_me(user_id, org_id)

    async def list_encounters(
        self, patient_id: Optional[int] = None
    ) -> List[EncounterModel]:
        return await self.repository.list(patient_id=patient_id)

    # ── Write ─────────────────────────────────────────────────────────────

    async def create_encounter(
        self,
        payload: EncounterCreateSchema,
        user_id: str,
        org_id: Optional[str] = None,
    ) -> EncounterModel:
        subject_display: Optional[str] = None
        if payload.subject:
            subject_type, subject_id = parse_reference(payload.subject, SubjectReferenceType)
            subject_display = await resolve_subject(
                subject_type, subject_id, user_id, org_id, patient_service=self.patient_service
            )
        return await self.repository.create(payload, user_id, org_id, subject_display)

    async def patch_encounter(
        self, encounter_id: int, payload: EncounterPatchSchema
    ) -> Optional[EncounterModel]:
        return await self.repository.patch(encounter_id, payload)

    async def delete_encounter(self, encounter_id: int) -> bool:
        return await self.repository.delete(encounter_id)
