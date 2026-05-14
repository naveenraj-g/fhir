from typing import Optional, List

from app.models.appointment.appointment import AppointmentModel
from app.repository.appointment_repository import AppointmentRepository
from app.schemas.appointment import AppointmentCreateSchema, AppointmentPatchSchema
from app.fhir.mappers.appointment import to_fhir_appointment, to_plain_appointment


class AppointmentService:
    def __init__(self, repository: AppointmentRepository):
        self.repository = repository

    # ── Formatters (called by route layer after content negotiation) ──────

    def _to_fhir(self, appointment: AppointmentModel) -> dict:
        return to_fhir_appointment(appointment)

    def _to_plain(self, appointment: AppointmentModel) -> dict:
        return to_plain_appointment(appointment)

    # ── Read ──────────────────────────────────────────────────────────────

    async def get_raw_by_appointment_id(
        self, appointment_id: int
    ) -> Optional[AppointmentModel]:
        """Raw ORM model — used by the auth ownership dependency."""
        return await self.repository.get_by_appointment_id(appointment_id)

    async def get_appointment(self, appointment_id: int) -> Optional[AppointmentModel]:
        return await self.repository.get_by_appointment_id(appointment_id)

    async def get_me(self, user_id: str, org_id: str) -> List[AppointmentModel]:
        return await self.repository.get_me(user_id, org_id)

    async def list_appointments(
        self,
        patient_id: Optional[int] = None,
        encounter_id: Optional[int] = None,
    ) -> List[AppointmentModel]:
        return await self.repository.list(patient_id=patient_id, encounter_id=encounter_id)

    # ── Write ─────────────────────────────────────────────────────────────

    async def create_appointment(
        self,
        payload: AppointmentCreateSchema,
        user_id: str,
        org_id: Optional[str] = None,
    ) -> AppointmentModel:
        return await self.repository.create(payload, user_id, org_id)

    async def patch_appointment(
        self, appointment_id: int, payload: AppointmentPatchSchema
    ) -> Optional[AppointmentModel]:
        return await self.repository.patch(appointment_id, payload)

    async def delete_appointment(self, appointment_id: int) -> bool:
        return await self.repository.delete(appointment_id)
