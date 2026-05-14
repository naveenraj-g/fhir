from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker  # noqa: F401
from sqlalchemy.orm import selectinload

from app.models.encounter.encounter import (
    EncounterModel,
    EncounterIdentifier,
    EncounterStatusHistory,
    EncounterClassHistory,
    EncounterType,
    EncounterEpisodeOfCare,
    EncounterBasedOn,
    EncounterParticipant,
    EncounterParticipantType,
    EncounterAppointmentRef,
    EncounterReasonCode,
    EncounterReasonReference,
    EncounterDiagnosis,
    EncounterAccount,
    EncounterHospDietPreference,
    EncounterHospSpecialArrangement,
    EncounterHospSpecialCourtesy,
    EncounterLocation,
)
from app.models.encounter.enums import (
    EncounterBasedOnReferenceType,
    EncounterDiagnosisConditionType,
    EncounterParticipantReferenceType,
)
from app.models.enums import SubjectReferenceType
from app.schemas.encounter import EncounterCreateSchema, EncounterPatchSchema


def _with_relationships(stmt):
    """Attach eager-load options for all encounter sub-resources."""
    return stmt.options(
        selectinload(EncounterModel.identifiers),
        selectinload(EncounterModel.status_history),
        selectinload(EncounterModel.class_history),
        selectinload(EncounterModel.types),
        selectinload(EncounterModel.episode_of_cares),
        selectinload(EncounterModel.based_ons),
        selectinload(EncounterModel.participants).selectinload(EncounterParticipant.types),
        selectinload(EncounterModel.appointment_refs),
        selectinload(EncounterModel.reason_codes),
        selectinload(EncounterModel.reason_references),
        selectinload(EncounterModel.diagnoses),
        selectinload(EncounterModel.accounts),
        selectinload(EncounterModel.hosp_diet_preferences),
        selectinload(EncounterModel.hosp_special_arrangements),
        selectinload(EncounterModel.hosp_special_courtesies),
        selectinload(EncounterModel.locations),
    )


def _parse_subject(subject_str: Optional[str]):
    if not subject_str:
        return None, None
    parts = subject_str.split("/")
    if len(parts) != 2:
        return None, None
    try:
        return SubjectReferenceType(parts[0]), int(parts[1])
    except (ValueError, KeyError):
        return None, None


def _parse_individual(individual_str: Optional[str]):
    if not individual_str:
        return None, None
    parts = individual_str.split("/")
    if len(parts) != 2:
        return None, None
    try:
        return EncounterParticipantReferenceType(parts[0]), int(parts[1])
    except (ValueError, KeyError):
        return None, None


def _parse_based_on(ref_str: str):
    parts = ref_str.split("/")
    if len(parts) != 2:
        return None, None
    try:
        return EncounterBasedOnReferenceType(parts[0]), int(parts[1])
    except (ValueError, KeyError):
        return None, None


def _parse_diagnosis_condition(ref_str: str):
    parts = ref_str.split("/")
    if len(parts) != 2:
        return None, None
    try:
        return EncounterDiagnosisConditionType(parts[0]), int(parts[1])
    except (ValueError, KeyError):
        return None, None


def _parse_reason_reference(ref_str: str):
    parts = ref_str.split("/")
    if len(parts) != 2:
        return None, None
    return parts[0], int(parts[1]) if parts[1].isdigit() else None


def _parse_location_ref(ref_str: str):
    parts = ref_str.split("/")
    if len(parts) == 2 and parts[1].isdigit():
        return int(parts[1])
    return None


def _parse_hosp_origin(ref_str: Optional[str]):
    if not ref_str:
        return None, None
    parts = ref_str.split("/")
    if len(parts) != 2:
        return None, None
    return parts[0], int(parts[1]) if parts[1].isdigit() else None


class EncounterRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    # ── Read ──────────────────────────────────────────────────────────────

    async def get_by_encounter_id(self, encounter_id: int) -> Optional[EncounterModel]:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(EncounterModel).where(EncounterModel.encounter_id == encounter_id)
            )
            return (await session.execute(stmt)).scalars().first()

    def _apply_list_filters(self, stmt, user_id, org_id, status, patient_id, class_code, period_start_from, period_start_to):
        if user_id:
            stmt = stmt.where(EncounterModel.user_id == user_id)
        if org_id:
            stmt = stmt.where(EncounterModel.org_id == org_id)
        if status:
            stmt = stmt.where(EncounterModel.status == status)
        if patient_id is not None:
            stmt = stmt.where(
                EncounterModel.subject_type == SubjectReferenceType.PATIENT,
                EncounterModel.subject_id == patient_id,
            )
        if class_code:
            stmt = stmt.where(EncounterModel.class_code == class_code)
        if period_start_from is not None:
            stmt = stmt.where(EncounterModel.period_start >= period_start_from)
        if period_start_to is not None:
            stmt = stmt.where(EncounterModel.period_start <= period_start_to)
        return stmt

    async def get_me(
        self,
        user_id: str,
        org_id: str,
        status: Optional[str] = None,
        patient_id: Optional[int] = None,
        class_code: Optional[str] = None,
        period_start_from: Optional[datetime] = None,
        period_start_to: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[EncounterModel], int]:
        async with self.session_factory() as session:
            base = self._apply_list_filters(
                _with_relationships(select(EncounterModel)),
                user_id, org_id, status, patient_id, class_code, period_start_from, period_start_to,
            )
            count_base = self._apply_list_filters(
                select(func.count()).select_from(EncounterModel),
                user_id, org_id, status, patient_id, class_code, period_start_from, period_start_to,
            )
            total = (await session.execute(count_base)).scalar_one()
            rows = list((await session.execute(
                base.order_by(EncounterModel.period_start.desc()).offset(offset).limit(limit)
            )).scalars().all())
        return rows, total

    async def list(
        self,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        status: Optional[str] = None,
        patient_id: Optional[int] = None,
        class_code: Optional[str] = None,
        period_start_from: Optional[datetime] = None,
        period_start_to: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[EncounterModel], int]:
        async with self.session_factory() as session:
            base = self._apply_list_filters(
                _with_relationships(select(EncounterModel)),
                user_id, org_id, status, patient_id, class_code, period_start_from, period_start_to,
            )
            count_base = self._apply_list_filters(
                select(func.count()).select_from(EncounterModel),
                user_id, org_id, status, patient_id, class_code, period_start_from, period_start_to,
            )
            total = (await session.execute(count_base)).scalar_one()
            rows = list((await session.execute(
                base.order_by(EncounterModel.period_start.desc()).offset(offset).limit(limit)
            )).scalars().all())
        return rows, total

    # ── Write ─────────────────────────────────────────────────────────────

    async def create(
        self,
        payload: EncounterCreateSchema,
        user_id: Optional[str],
        org_id: Optional[str] = None,
        subject_display: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> EncounterModel:
        subject_type, subject_id = _parse_subject(payload.subject)

        encounter = EncounterModel(
            user_id=user_id,
            org_id=org_id,
            status=payload.status,
            class_system=payload.class_system,
            class_version=payload.class_version,
            class_code=payload.class_code,
            class_display=payload.class_display,
            service_type_system=payload.service_type_system,
            service_type_code=payload.service_type_code,
            service_type_display=payload.service_type_display,
            service_type_text=payload.service_type_text,
            priority_system=payload.priority_system,
            priority_code=payload.priority_code,
            priority_display=payload.priority_display,
            priority_text=payload.priority_text,
            subject_type=subject_type,
            subject_id=subject_id,
            subject_display=subject_display,
            period_start=payload.period_start,
            period_end=payload.period_end,
            length_value=payload.length_value,
            length_comparator=payload.length_comparator,
            length_unit=payload.length_unit,
            length_system=payload.length_system,
            length_code=payload.length_code,
            service_provider_id=payload.service_provider_id,
            service_provider_display=payload.service_provider_display,
            part_of_id=payload.part_of_id,
            created_by=created_by,
        )

        # identifier
        if payload.identifier:
            for inp in payload.identifier:
                encounter.identifiers.append(EncounterIdentifier(
                    org_id=org_id,
                    use=inp.use,
                    type_system=inp.type_system,
                    type_code=inp.type_code,
                    type_display=inp.type_display,
                    type_text=inp.type_text,
                    system=inp.system,
                    value=inp.value,
                    period_start=inp.period_start,
                    period_end=inp.period_end,
                    assigner=inp.assigner,
                ))

        # statusHistory
        if payload.status_history:
            for sh in payload.status_history:
                encounter.status_history.append(EncounterStatusHistory(
                    org_id=org_id,
                    status=sh.status,
                    period_start=sh.period_start,
                    period_end=sh.period_end,
                ))

        # classHistory
        if payload.class_history:
            for ch in payload.class_history:
                encounter.class_history.append(EncounterClassHistory(
                    org_id=org_id,
                    class_system=ch.class_system,
                    class_version=ch.class_version,
                    class_code=ch.class_code,
                    class_display=ch.class_display,
                    period_start=ch.period_start,
                    period_end=ch.period_end,
                ))

        # type
        if payload.type:
            for t in payload.type:
                encounter.types.append(EncounterType(
                    org_id=org_id,
                    coding_system=t.coding_system,
                    coding_code=t.coding_code,
                    coding_display=t.coding_display,
                    text=t.text,
                ))

        # episodeOfCare
        if payload.episode_of_care:
            for e in payload.episode_of_care:
                encounter.episode_of_cares.append(EncounterEpisodeOfCare(
                    org_id=org_id,
                    episode_of_care_id=e.episode_of_care_id,
                    display=e.display,
                ))

        # basedOn
        if payload.based_on:
            for b in payload.based_on:
                ref_type, ref_id = _parse_based_on(b.reference)
                encounter.based_ons.append(EncounterBasedOn(
                    org_id=org_id,
                    reference_type=ref_type,
                    reference_id=ref_id,
                    reference_display=b.display,
                ))

        # participant
        if payload.participant:
            for p in payload.participant:
                ind_type, ind_id = _parse_individual(p.individual)
                participant = EncounterParticipant(
                    org_id=org_id,
                    individual_type=ind_type,
                    individual_id=ind_id,
                    period_start=p.period_start,
                    period_end=p.period_end,
                )
                if p.type:
                    for pt in p.type:
                        participant.types.append(EncounterParticipantType(
                            org_id=org_id,
                            coding_system=pt.coding_system,
                            coding_code=pt.coding_code,
                            coding_display=pt.coding_display,
                            text=pt.text,
                        ))
                encounter.participants.append(participant)

        # appointment
        if payload.appointment:
            for a in payload.appointment:
                encounter.appointment_refs.append(EncounterAppointmentRef(
                    org_id=org_id,
                    appointment_id=a.appointment_id,
                    appointment_display=a.display,
                ))

        # reasonCode
        if payload.reason_code:
            for r in payload.reason_code:
                encounter.reason_codes.append(EncounterReasonCode(
                    org_id=org_id,
                    coding_system=r.coding_system,
                    coding_code=r.coding_code,
                    coding_display=r.coding_display,
                    text=r.text,
                ))

        # reasonReference
        if payload.reason_reference:
            for rr in payload.reason_reference:
                rr_type, rr_id = _parse_reason_reference(rr.reference)
                encounter.reason_references.append(EncounterReasonReference(
                    org_id=org_id,
                    reference_type=rr_type,
                    reference_id=rr_id,
                    reference_display=rr.display,
                ))

        # diagnosis
        if payload.diagnosis:
            for d in payload.diagnosis:
                cond_type, cond_id = _parse_diagnosis_condition(d.condition)
                encounter.diagnoses.append(EncounterDiagnosis(
                    org_id=org_id,
                    condition_type=cond_type,
                    condition_id=cond_id,
                    condition_display=d.condition_display,
                    use_system=d.use_system,
                    use_code=d.use_code,
                    use_display=d.use_display,
                    use_text=d.use_text,
                    rank=d.rank,
                ))

        # account
        if payload.account:
            for a in payload.account:
                encounter.accounts.append(EncounterAccount(
                    org_id=org_id,
                    account_id=a.account_id,
                    account_display=a.display,
                ))

        # hospitalization
        if payload.hospitalization:
            h = payload.hospitalization
            origin_type, origin_id = _parse_hosp_origin(h.origin)
            dest_type, dest_id = _parse_hosp_origin(h.destination)
            encounter.hosp_pre_admission_identifier_system = h.pre_admission_identifier_system
            encounter.hosp_pre_admission_identifier_value = h.pre_admission_identifier_value
            encounter.hosp_origin_type = origin_type
            encounter.hosp_origin_id = origin_id
            encounter.hosp_origin_display = h.origin_display
            encounter.hosp_admit_source_system = h.admit_source_system
            encounter.hosp_admit_source_code = h.admit_source_code
            encounter.hosp_admit_source_display = h.admit_source_display
            encounter.hosp_admit_source_text = h.admit_source_text
            encounter.hosp_re_admission_system = h.re_admission_system
            encounter.hosp_re_admission_code = h.re_admission_code
            encounter.hosp_re_admission_display = h.re_admission_display
            encounter.hosp_re_admission_text = h.re_admission_text
            encounter.hosp_destination_type = dest_type
            encounter.hosp_destination_id = dest_id
            encounter.hosp_destination_display = h.destination_display
            encounter.hosp_discharge_disposition_system = h.discharge_disposition_system
            encounter.hosp_discharge_disposition_code = h.discharge_disposition_code
            encounter.hosp_discharge_disposition_display = h.discharge_disposition_display
            encounter.hosp_discharge_disposition_text = h.discharge_disposition_text

            if h.diet_preference:
                for dp in h.diet_preference:
                    encounter.hosp_diet_preferences.append(EncounterHospDietPreference(
                        org_id=org_id,
                        coding_system=dp.coding_system,
                        coding_code=dp.coding_code,
                        coding_display=dp.coding_display,
                        text=dp.text,
                    ))
            if h.special_arrangement:
                for sa in h.special_arrangement:
                    encounter.hosp_special_arrangements.append(EncounterHospSpecialArrangement(
                        org_id=org_id,
                        coding_system=sa.coding_system,
                        coding_code=sa.coding_code,
                        coding_display=sa.coding_display,
                        text=sa.text,
                    ))
            if h.special_courtesy:
                for sc in h.special_courtesy:
                    encounter.hosp_special_courtesies.append(EncounterHospSpecialCourtesy(
                        org_id=org_id,
                        coding_system=sc.coding_system,
                        coding_code=sc.coding_code,
                        coding_display=sc.coding_display,
                        text=sc.text,
                    ))

        # location
        if payload.location:
            for loc in payload.location:
                loc_id = _parse_location_ref(loc.location)
                encounter.locations.append(EncounterLocation(
                    org_id=org_id,
                    location_id=loc_id,
                    location_display=loc.location_display,
                    status=loc.status,
                    physical_type_system=loc.physical_type_system,
                    physical_type_code=loc.physical_type_code,
                    physical_type_display=loc.physical_type_display,
                    physical_type_text=loc.physical_type_text,
                    period_start=loc.period_start,
                    period_end=loc.period_end,
                ))

        async with self.session_factory() as session:
            try:
                session.add(encounter)
                await session.commit()
                await session.refresh(encounter)
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_encounter_id(encounter.encounter_id)

    async def patch(
        self,
        encounter_id: int,
        payload: EncounterPatchSchema,
        updated_by: Optional[str] = None,
    ) -> Optional[EncounterModel]:
        async with self.session_factory() as session:
            stmt = select(EncounterModel).where(EncounterModel.encounter_id == encounter_id)
            encounter = (await session.execute(stmt)).scalars().first()
            if not encounter:
                return None

            update_data = payload.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(encounter, field, value)
            if updated_by is not None:
                encounter.updated_by = updated_by

            try:
                await session.commit()
                await session.refresh(encounter)
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_encounter_id(encounter_id)

    async def delete(self, encounter_id: int) -> bool:
        async with self.session_factory() as session:
            stmt = select(EncounterModel).where(EncounterModel.encounter_id == encounter_id)
            encounter = (await session.execute(stmt)).scalars().first()
            if not encounter:
                return False
            try:
                await session.delete(encounter)
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                raise
