from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker  # noqa: F401
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.appointment.appointment import (
    AppointmentModel,
    AppointmentParticipant,
    AppointmentReasonCode,
    AppointmentRecurrenceTemplate,
)
from app.models.appointment.enums import AppointmentParticipantActorType
from app.models.encounter.encounter import EncounterModel
from app.models.enums import SubjectReferenceType
from app.schemas.appointment import AppointmentCreateSchema, AppointmentPatchSchema


def _with_relationships(stmt):
    """Attach eager-load options for all appointment sub-resources."""
    return stmt.options(
        selectinload(AppointmentModel.encounter),
        selectinload(AppointmentModel.participants),
        selectinload(AppointmentModel.reason_codes),
        selectinload(AppointmentModel.recurrence_template),
    )


def _parse_subject(subject_str: Optional[str]):
    """Parse 'Patient/10001' → (SubjectReferenceType.PATIENT, 10001)."""
    if not subject_str:
        return None, None
    parts = subject_str.split("/")
    if len(parts) != 2:
        return None, None
    try:
        return SubjectReferenceType(parts[0]), int(parts[1])
    except (ValueError, KeyError):
        return None, None


def _parse_actor(actor_str: Optional[str]):
    """Parse 'Practitioner/30001' → (AppointmentParticipantActorType.PRACTITIONER, 30001)."""
    if not actor_str:
        return None, None
    parts = actor_str.split("/")
    if len(parts) != 2:
        return None, None
    try:
        return AppointmentParticipantActorType(parts[0]), int(parts[1])
    except (ValueError, KeyError):
        return None, None


class AppointmentRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    # ── Read ──────────────────────────────────────────────────────────────

    async def get_by_appointment_id(
        self, appointment_id: int
    ) -> Optional[AppointmentModel]:
        """Fetch by public appointment_id with all sub-resources loaded."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(AppointmentModel).where(
                    AppointmentModel.appointment_id == appointment_id
                )
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_me(self, user_id: str, org_id: str) -> List[AppointmentModel]:
        """Fetch all appointments owned by user_id within org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(AppointmentModel).where(
                    AppointmentModel.user_id == user_id,
                    AppointmentModel.org_id == org_id,
                )
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def list(
        self,
        patient_id: Optional[int] = None,
        encounter_id: Optional[int] = None,
    ) -> List[AppointmentModel]:
        """List appointments, optionally filtered by public patient_id or encounter_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(select(AppointmentModel))

            if patient_id is not None:
                stmt = stmt.where(
                    AppointmentModel.subject_type == SubjectReferenceType.PATIENT,
                    AppointmentModel.subject_id == patient_id,
                )

            if encounter_id is not None:
                # Resolve public encounter_id → internal encounter PK
                enc_result = await session.execute(
                    select(EncounterModel.id).where(
                        EncounterModel.encounter_id == encounter_id
                    )
                )
                internal_enc_id = enc_result.scalar_one_or_none()
                if internal_enc_id is not None:
                    stmt = stmt.where(AppointmentModel.encounter_id == internal_enc_id)
                else:
                    return []

            result = await session.execute(stmt)
            return list(result.scalars().all())

    # ── Write ─────────────────────────────────────────────────────────────

    async def create(
        self,
        payload: AppointmentCreateSchema,
        user_id: str,
        org_id: Optional[str] = None,
    ) -> AppointmentModel:
        subject_type, subject_id = _parse_subject(payload.subject)

        async with self.session_factory() as session:
            # Resolve public encounter_id → internal encounter PK
            internal_encounter_id: Optional[int] = None
            if payload.encounter_id is not None:
                enc_result = await session.execute(
                    select(EncounterModel.id).where(
                        EncounterModel.encounter_id == payload.encounter_id
                    )
                )
                internal_encounter_id = enc_result.scalar_one_or_none()

            appointment = AppointmentModel(
                user_id=user_id,
                org_id=org_id,
                status=payload.status,
                subject_type=subject_type,
                subject_id=subject_id,
                subject_display=payload.subject_display,
                encounter_id=internal_encounter_id,
                start=payload.start,
                end=payload.end,
                minutes_duration=payload.minutes_duration,
                created=payload.created,
                description=payload.description,
                comment=payload.comment,
                patient_instruction=payload.patient_instruction,
                priority_value=payload.priority_value,
                service_category_code=payload.service_category_code,
                service_category_display=payload.service_category_display,
                service_type_code=payload.service_type_code,
                service_type_display=payload.service_type_display,
                specialty_code=payload.specialty_code,
                specialty_display=payload.specialty_display,
                appointment_type_code=payload.appointment_type_code,
                appointment_type_display=payload.appointment_type_display,
                cancellation_reason=payload.cancellation_reason,
                cancellation_date=payload.cancellation_date,
                recurrence_id=payload.recurrence_id,
                occurrence_changed=payload.occurrence_changed,
            )

            # reason codes
            if payload.reason_codes:
                for r in payload.reason_codes:
                    appointment.reason_codes.append(
                        AppointmentReasonCode(
                            coding_system=r.coding_system,
                            coding_code=r.coding_code,
                            coding_display=r.coding_display,
                            text=r.text,
                        )
                    )

            # participants
            for p in payload.participant:
                actor_type, actor_id = _parse_actor(p.actor)
                appointment.participants.append(
                    AppointmentParticipant(
                        actor_reference_type=actor_type,
                        actor_reference_id=actor_id,
                        actor_display=p.actor_display,
                        type_code=p.type_code,
                        type_display=p.type_display,
                        type_text=p.type_text,
                        required=p.required,
                        status=p.status,
                        period_start=p.period_start,
                        period_end=p.period_end,
                    )
                )

            # recurrenceTemplate
            if payload.recurrence_template:
                rt = payload.recurrence_template
                appointment.recurrence_template = AppointmentRecurrenceTemplate(
                    recurrence_type_code=rt.recurrence_type_code,
                    recurrence_type_display=rt.recurrence_type_display,
                    recurrence_type_system=rt.recurrence_type_system,
                    timezone_code=rt.timezone_code,
                    timezone_display=rt.timezone_display,
                    last_occurrence_date=rt.last_occurrence_date,
                    occurrence_count=rt.occurrence_count,
                    occurrence_dates=",".join(str(d) for d in rt.occurrence_dates) if rt.occurrence_dates else None,
                    excluding_dates=",".join(str(d) for d in rt.excluding_dates) if rt.excluding_dates else None,
                    excluding_recurrence_ids=",".join(str(i) for i in rt.excluding_recurrence_ids) if rt.excluding_recurrence_ids else None,
                    weekly_monday=rt.weekly_template.monday if rt.weekly_template else None,
                    weekly_tuesday=rt.weekly_template.tuesday if rt.weekly_template else None,
                    weekly_wednesday=rt.weekly_template.wednesday if rt.weekly_template else None,
                    weekly_thursday=rt.weekly_template.thursday if rt.weekly_template else None,
                    weekly_friday=rt.weekly_template.friday if rt.weekly_template else None,
                    weekly_saturday=rt.weekly_template.saturday if rt.weekly_template else None,
                    weekly_sunday=rt.weekly_template.sunday if rt.weekly_template else None,
                    weekly_week_interval=rt.weekly_template.week_interval if rt.weekly_template else None,
                    monthly_day_of_month=rt.monthly_template.day_of_month if rt.monthly_template else None,
                    monthly_nth_week_code=rt.monthly_template.nth_week_code if rt.monthly_template else None,
                    monthly_nth_week_display=rt.monthly_template.nth_week_display if rt.monthly_template else None,
                    monthly_day_of_week_code=rt.monthly_template.day_of_week_code if rt.monthly_template else None,
                    monthly_day_of_week_display=rt.monthly_template.day_of_week_display if rt.monthly_template else None,
                    monthly_month_interval=rt.monthly_template.month_interval if rt.monthly_template else None,
                    yearly_year_interval=rt.yearly_template.year_interval if rt.yearly_template else None,
                )

            try:
                session.add(appointment)
                await session.commit()
                await session.refresh(appointment)
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_appointment_id(appointment.appointment_id)

    async def patch(
        self, appointment_id: int, payload: AppointmentPatchSchema
    ) -> Optional[AppointmentModel]:
        """Partial update — only fields explicitly set in payload are written."""
        async with self.session_factory() as session:
            stmt = select(AppointmentModel).where(
                AppointmentModel.appointment_id == appointment_id
            )
            result = await session.execute(stmt)
            appointment = result.scalars().first()

            if not appointment:
                return None

            update_data = payload.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(appointment, field, value)

            try:
                await session.commit()
                await session.refresh(appointment)
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_appointment_id(appointment_id)

    async def delete(self, appointment_id: int) -> bool:
        async with self.session_factory() as session:
            stmt = select(AppointmentModel).where(
                AppointmentModel.appointment_id == appointment_id
            )
            result = await session.execute(stmt)
            appointment = result.scalars().first()

            if not appointment:
                return False

            try:
                await session.delete(appointment)
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                raise
