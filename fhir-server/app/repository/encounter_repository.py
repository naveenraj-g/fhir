from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker  # noqa: F401
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.encounter.encounter import (
    EncounterModel,
    EncounterType,
    BasedOn,
    EncounterParticipant,
    EncounterDiagnosis,
    EncounterLocation,
    EncounterReasonCode,
)
from app.models.encounter.enums import (
    EncounterParticipantReferenceType,
    EncounterBasedOnReferenceType,
)
from app.models.enums import SubjectReferenceType
from app.schemas.encounter import EncounterCreateSchema, EncounterPatchSchema


def _with_relationships(stmt):
    """Attach eager-load options for all encounter sub-resources."""
    return stmt.options(
        selectinload(EncounterModel.based_ons),
        selectinload(EncounterModel.types),
        selectinload(EncounterModel.participants),
        selectinload(EncounterModel.diagnoses),
        selectinload(EncounterModel.locations),
        selectinload(EncounterModel.reason_codes),
    )


def _parse_subject(subject_str: Optional[str]):
    """Parse 'Patient/10001' → (SubjectReferenceType.PATIENT, 10001)."""
    if not subject_str:
        return None, None
    parts = subject_str.split("/")
    if len(parts) != 2:
        return None, None
    resource_type, resource_id = parts
    try:
        return SubjectReferenceType(resource_type), int(resource_id)
    except (ValueError, KeyError):
        return None, None


def _parse_individual(individual_str: Optional[str]):
    """Parse 'Practitioner/30001' → (EncounterParticipantReferenceType.PRACTITIONER, 30001)."""
    if not individual_str:
        return None, None
    parts = individual_str.split("/")
    if len(parts) != 2:
        return None, None
    resource_type, resource_id = parts
    try:
        return EncounterParticipantReferenceType(resource_type), int(resource_id)
    except (ValueError, KeyError):
        return None, None


def _parse_based_on(ref_str: str):
    """Parse 'ServiceRequest/1234' → (EncounterBasedOnReferenceType.SERVICE_REQUEST, 1234)."""
    parts = ref_str.split("/")
    if len(parts) != 2:
        return None, None
    resource_type, resource_id = parts
    try:
        return EncounterBasedOnReferenceType(resource_type), int(resource_id)
    except (ValueError, KeyError):
        return None, None


class EncounterRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    # ── Read ──────────────────────────────────────────────────────────────

    async def get_by_encounter_id(self, encounter_id: int) -> Optional[EncounterModel]:
        """Fetch by public encounter_id with all sub-resources loaded."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(EncounterModel).where(
                    EncounterModel.encounter_id == encounter_id
                )
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_me(self, user_id: str, org_id: str) -> List[EncounterModel]:
        """Fetch all encounters owned by user_id within org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(EncounterModel).where(
                    EncounterModel.user_id == user_id,
                    EncounterModel.org_id == org_id,
                )
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def list(self, patient_id: Optional[int] = None) -> List[EncounterModel]:
        """List encounters, optionally filtered by public patient_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(select(EncounterModel))
            if patient_id is not None:
                stmt = stmt.where(
                    EncounterModel.subject_type == SubjectReferenceType.PATIENT,
                    EncounterModel.subject_id == patient_id,
                )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    # ── Write ─────────────────────────────────────────────────────────────

    async def create(
        self,
        payload: EncounterCreateSchema,
        user_id: str,
        org_id: Optional[str] = None,
        subject_display: Optional[str] = None,
    ) -> EncounterModel:
        subject_type, subject_id = _parse_subject(payload.subject)

        async with self.session_factory() as session:
            encounter = EncounterModel(
                user_id=user_id,
                org_id=org_id,
                status=payload.status,
                class_code=payload.class_code,
                priority=payload.priority,
                subject_type=subject_type,
                subject_id=subject_id,
                subject_display=subject_display,
                period_start=payload.period_start,
                period_end=payload.period_end,
            )

            # based_on
            if payload.based_on:
                for b in payload.based_on:
                    ref_type, ref_id = _parse_based_on(b.reference)
                    encounter.based_ons.append(
                        BasedOn(
                            reference_type=ref_type,
                            reference_id=ref_id,
                            reference_display=b.display,
                        )
                    )

            # types
            if payload.type:
                for t in payload.type:
                    encounter.types.append(
                        EncounterType(
                            coding_system=t.coding_system,
                            coding_code=t.coding_code,
                            coding_display=t.coding_display,
                            text=t.text,
                        )
                    )

            # participants
            if payload.participant:
                for p in payload.participant:
                    ref_type, ref_id = _parse_individual(p.individual)
                    encounter.participants.append(
                        EncounterParticipant(
                            type_text=p.type_text,
                            reference_type=ref_type,
                            individual_reference=ref_id,
                            period_start=p.period_start,
                            period_end=p.period_end,
                        )
                    )

            # reason codes
            if payload.reason_codes:
                for r in payload.reason_codes:
                    encounter.reason_codes.append(
                        EncounterReasonCode(
                            coding_system=r.coding_system,
                            coding_code=r.coding_code,
                            coding_display=r.coding_display,
                            text=r.text,
                        )
                    )

            # diagnoses
            if payload.diagnoses:
                for d in payload.diagnoses:
                    encounter.diagnoses.append(
                        EncounterDiagnosis(
                            condition_reference=d.condition_reference,
                            use_text=d.use_text,
                            rank=str(d.rank) if d.rank is not None else None,
                        )
                    )

            # locations
            if payload.locations:
                for loc in payload.locations:
                    encounter.locations.append(
                        EncounterLocation(
                            location_reference=loc.location_reference,
                            status=loc.status,
                            period_start=loc.period_start,
                            period_end=loc.period_end,
                        )
                    )

            try:
                session.add(encounter)
                await session.commit()
                await session.refresh(encounter)
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_encounter_id(encounter.encounter_id)

    async def patch(
        self, encounter_id: int, payload: EncounterPatchSchema
    ) -> Optional[EncounterModel]:
        """Partial update — only fields explicitly set in payload are written."""
        async with self.session_factory() as session:
            stmt = select(EncounterModel).where(
                EncounterModel.encounter_id == encounter_id
            )
            result = await session.execute(stmt)
            encounter = result.scalars().first()

            if not encounter:
                return None

            update_data = payload.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(encounter, field, value)

            try:
                await session.commit()
                await session.refresh(encounter)
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_encounter_id(encounter_id)

    async def delete(self, encounter_id: int) -> bool:
        async with self.session_factory() as session:
            stmt = select(EncounterModel).where(
                EncounterModel.encounter_id == encounter_id
            )
            result = await session.execute(stmt)
            encounter = result.scalars().first()

            if not encounter:
                return False

            try:
                await session.delete(encounter)
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                raise
