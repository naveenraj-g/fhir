from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from fastapi import HTTPException

from app.fhir.mappers.slot import to_fhir_slot, to_plain_slot
from app.models.schedule.enums import ScheduleActorReferenceType
from app.models.slot.slot import SlotModel
from app.repository.practitioner_role_repository import PractitionerRoleRepository
from app.repository.schedule_repository import ScheduleRepository
from app.repository.slot_repository import SlotRepository
from app.schemas.slot import (
    SlotCreateSchema,
    SlotGenerateSchema,
    SlotGenerateResponse,
    SlotPatchSchema,
    SlotServiceCategoryInput,
    SlotServiceTypeInput,
    SlotSpecialtyInput,
)


class SlotService:
    def __init__(
        self,
        repository: SlotRepository,
        schedule_repository: ScheduleRepository,
        practitioner_role_repository: PractitionerRoleRepository,
    ):
        self.repository = repository
        self.schedule_repository = schedule_repository
        self.practitioner_role_repository = practitioner_role_repository

    def _to_fhir(self, slot: SlotModel) -> dict:
        return to_fhir_slot(slot)

    def _to_plain(self, slot: SlotModel) -> dict:
        return to_plain_slot(slot)

    async def get_raw_by_slot_id(self, slot_id: int) -> Optional[SlotModel]:
        return await self.repository.get_by_slot_id(slot_id)

    async def get_me(
        self,
        user_id: str,
        org_id: str,
        slot_status: Optional[str] = None,
        schedule_id: Optional[int] = None,
        practitioner_role_id: Optional[int] = None,
        date: Optional[str] = None,
        start_from: Optional[str] = None,
        start_to: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[SlotModel], int]:
        return await self.repository.get_me(
            user_id, org_id,
            slot_status=slot_status, schedule_id=schedule_id,
            practitioner_role_id=practitioner_role_id,
            date=date, start_from=start_from, start_to=start_to,
            limit=limit, offset=offset,
        )

    async def list_slots(
        self,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        slot_status: Optional[str] = None,
        schedule_id: Optional[int] = None,
        practitioner_role_id: Optional[int] = None,
        date: Optional[str] = None,
        start_from: Optional[str] = None,
        start_to: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[SlotModel], int]:
        return await self.repository.list(
            user_id=user_id, org_id=org_id,
            slot_status=slot_status, schedule_id=schedule_id,
            practitioner_role_id=practitioner_role_id,
            date=date, start_from=start_from, start_to=start_to,
            limit=limit, offset=offset,
        )

    async def create_slot(
        self,
        payload: SlotCreateSchema,
        user_id: Optional[str],
        org_id: Optional[str],
        created_by: Optional[str],
    ) -> SlotModel:
        return await self.repository.create(payload, user_id, org_id, created_by)

    async def patch_slot(
        self,
        slot_id: int,
        payload: SlotPatchSchema,
        updated_by: Optional[str],
    ) -> Optional[SlotModel]:
        return await self.repository.patch(slot_id, payload, updated_by)

    async def delete_slot(self, slot_id: int) -> None:
        await self.repository.delete(slot_id)

    async def generate(self, dto: SlotGenerateSchema) -> SlotGenerateResponse:
        schedule = await self.schedule_repository.get_by_schedule_id(dto.schedule_id)
        if schedule is None:
            raise HTTPException(status_code=404, detail=f"Schedule '{dto.schedule_id}' not found.")

        # generation_start/generation_end are treated as calendar dates only —
        # the daily time-of-day window comes from the Schedule's own
        # planningHorizon start/end time, applied to every day in the range.
        horizon_start = schedule.planning_horizon_start
        horizon_end = schedule.planning_horizon_end
        if horizon_start is None or horizon_end is None:
            raise HTTPException(
                status_code=422,
                detail="Schedule has no planningHorizon start/end time configured.",
            )

        start_date = dto.generation_start.date()
        # generation_end is exclusive, so the last calendar day actually
        # generated is one day before it.
        last_date = dto.generation_end.date() - timedelta(days=1)

        if start_date < horizon_start.date():
            raise HTTPException(
                status_code=422,
                detail="generation_start is before the schedule's planningHorizon start",
            )
        if last_date > horizon_end.date():
            last_date = horizon_end.date()
        if last_date < start_date:
            raise HTTPException(
                status_code=422,
                detail="No slots can be generated: the requested window contains no valid days.",
            )

        daily_start_time = horizon_start.time()
        daily_end_time = horizon_end.time()

        service_category = dto.service_category or [
            SlotServiceCategoryInput(
                coding_system=sc.coding_system,
                coding_code=sc.coding_code,
                coding_display=sc.coding_display,
                text=sc.text,
            )
            for sc in (schedule.service_categories or [])
        ]
        service_type = dto.service_type or [
            SlotServiceTypeInput(
                coding_system=st.coding_system,
                coding_code=st.coding_code,
                coding_display=st.coding_display,
                text=st.text,
            )
            for st in (schedule.service_types or [])
        ]
        specialty = dto.specialty or [
            SlotSpecialtyInput(
                coding_system=sp.coding_system,
                coding_code=sp.coding_code,
                coding_display=sp.coding_display,
                text=sp.text,
            )
            for sp in (schedule.specialties or [])
        ]
        if not specialty:
            pr_actor = next(
                (
                    a for a in (schedule.actors or [])
                    if a.reference_type == ScheduleActorReferenceType.PractitionerRole
                ),
                None,
            )
            if pr_actor is not None and pr_actor.reference_id is not None:
                pr = await self.practitioner_role_repository.get_by_practitioner_role_id(pr_actor.reference_id)
                if pr is not None:
                    specialty = [
                        SlotSpecialtyInput(
                            coding_system=sp.coding_system,
                            coding_code=sp.coding_code,
                            coding_display=sp.coding_display,
                            text=sp.text,
                        )
                        for sp in (pr.specialties or [])
                    ]

        duration = timedelta(minutes=dto.slot_duration_minutes)
        windows = []
        d = start_date
        while d <= last_date:
            day_start = datetime.combine(d, daily_start_time, tzinfo=horizon_start.tzinfo)
            day_end = datetime.combine(d, daily_end_time, tzinfo=horizon_end.tzinfo)
            cursor = day_start
            while cursor + duration <= day_end:
                windows.append((cursor, cursor + duration))
                cursor += duration
            d += timedelta(days=1)

        if not windows:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"No slots can be generated: the schedule's daily window "
                    f"({daily_start_time} to {daily_end_time}) is shorter than "
                    f"slot_duration_minutes ({dto.slot_duration_minutes} min)"
                ),
            )

        slot_ids = await self.repository.bulk_create(
            schedule_fk_id=schedule.id,
            windows=windows,
            status="free",
            overbooked=dto.overbooked,
            comment=dto.comment or None,
            appointment_type_system=dto.appointment_type_system or None,
            appointment_type_code=dto.appointment_type_code or None,
            appointment_type_display=dto.appointment_type_display or None,
            appointment_type_text=dto.appointment_type_text or None,
            service_category=service_category,
            service_type=service_type,
            specialty=specialty,
            user_id=dto.user_id,
            org_id=dto.org_id,
            created_by=dto.created_by,
        )

        return SlotGenerateResponse(
            schedule_id=dto.schedule_id,
            generated_count=len(slot_ids),
            slot_ids=slot_ids,
            generation_start=windows[0][0],
            generation_end=windows[-1][1],
            slot_duration_minutes=dto.slot_duration_minutes,
        )
