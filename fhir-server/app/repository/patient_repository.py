from typing import List, Optional, Tuple
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker  # noqa: F401
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.patient import PatientModel, PatientIdentifier, PatientTelecom, PatientAddress
from app.models.datatypes import CodeableConcept as CodeableConceptModel, Coding as CodingModel
from app.schemas.resources import PatientCreateSchema, PatientPatchSchema, IdentifierCreate, TelecomCreate, AddressCreate


def _with_relationships(stmt):
    """Attach eager-load options for all patient sub-resources."""
    return stmt.options(
        selectinload(PatientModel.identifiers)
            .selectinload(PatientIdentifier.type)
            .selectinload(CodeableConceptModel.codings),
        selectinload(PatientModel.telecoms),
        selectinload(PatientModel.addresses),
    )


class PatientRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    # ── Read ─────────────────────────────────────────────────────────────

    async def get_by_patient_id(self, patient_id: int) -> Optional[PatientModel]:
        """Fetch by public patient_id with all sub-resources loaded."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(PatientModel).where(PatientModel.patient_id == patient_id)
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_by_patient_id_in_org(
        self, patient_id: int, user_id: str, org_id: str
    ) -> Optional[PatientModel]:
        """Fetch by public patient_id scoped to the owning user and organisation."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(PatientModel).where(
                    PatientModel.patient_id == patient_id,
                    PatientModel.user_id == user_id,
                    PatientModel.org_id == org_id,
                )
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_by_user_id(self, user_id: str) -> Optional[PatientModel]:
        """Fetch by user_id with all sub-resources loaded."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(PatientModel).where(PatientModel.user_id == user_id)
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    def _apply_list_filters(self, stmt, user_id, org_id, family_name, given_name, gender, active):
        if user_id:
            stmt = stmt.where(PatientModel.user_id == user_id)
        if org_id:
            stmt = stmt.where(PatientModel.org_id == org_id)
        if family_name:
            stmt = stmt.where(PatientModel.family_name.ilike(f"%{family_name}%"))
        if given_name:
            stmt = stmt.where(PatientModel.given_name.ilike(f"%{given_name}%"))
        if gender is not None:
            stmt = stmt.where(PatientModel.gender == gender)
        if active is not None:
            stmt = stmt.where(PatientModel.active == active)
        return stmt

    async def list(
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
        async with self.session_factory() as session:
            base = self._apply_list_filters(
                _with_relationships(select(PatientModel)),
                user_id, org_id, family_name, given_name, gender, active,
            )
            count_base = self._apply_list_filters(
                select(func.count()).select_from(PatientModel),
                user_id, org_id, family_name, given_name, gender, active,
            )
            total = (await session.execute(count_base)).scalar_one()
            rows = list((await session.execute(
                base.order_by(PatientModel.patient_id.desc()).offset(offset).limit(limit)
            )).scalars().all())
        return rows, total

    # ── Write ────────────────────────────────────────────────────────────

    async def get_me(self, user_id: str, org_id: str) -> Optional[PatientModel]:
        """Fetch the patient profile that belongs to user_id within org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(PatientModel).where(
                    PatientModel.user_id == user_id,
                    PatientModel.org_id == org_id,
                )
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    async def create(self, payload: PatientCreateSchema, user_id: Optional[str], org_id: Optional[str] = None, created_by: Optional[str] = None) -> PatientModel:
        async with self.session_factory() as session:
            patient = PatientModel(
                user_id=user_id,
                org_id=org_id,
                given_name=payload.given_name,
                family_name=payload.family_name,
                gender=payload.gender,
                birth_date=payload.birth_date,
                active=payload.active,
                created_by=created_by,
            )
            try:
                session.add(patient)
                await session.commit()
                await session.refresh(patient)
            except Exception:
                await session.rollback()
                raise

            return await self.get_by_patient_id(patient.patient_id)

    async def patch(self, patient_id: int, payload: PatientPatchSchema, updated_by: Optional[str] = None) -> Optional[PatientModel]:
        """Partial update — only fields explicitly set in payload are written."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(PatientModel).where(PatientModel.patient_id == patient_id)
            )
            result = await session.execute(stmt)
            patient = result.scalars().first()

            if not patient:
                return None

            update_data = payload.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(patient, field, value)
            if updated_by is not None:
                patient.updated_by = updated_by

            try:
                await session.commit()
                await session.refresh(patient)
            except Exception:
                await session.rollback()
                raise

        # Re-fetch with relationships in a fresh session
        return await self.get_by_patient_id(patient_id)

    async def delete(self, patient_id: int) -> bool:
        async with self.session_factory() as session:
            stmt = select(PatientModel).where(PatientModel.patient_id == patient_id)
            result = await session.execute(stmt)
            patient = result.scalars().first()

            if not patient:
                return False

            try:
                await session.delete(patient)
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                raise

    # ── Sub-resource mutations ────────────────────────────────────────────

    async def add_identifier(self, patient_id: int, payload: IdentifierCreate) -> Optional[PatientModel]:
        async with self.session_factory() as session:
            stmt = select(PatientModel).where(PatientModel.patient_id == patient_id)
            result = await session.execute(stmt)
            patient = result.scalars().first()

            if not patient:
                return None

            ident = PatientIdentifier(
                patient_id=patient.id,
                use=payload.use.value if payload.use else None,
                system=payload.system,
                value=payload.value,
                period_start=payload.period_start,
                period_end=payload.period_end,
                assigner=payload.assigner,
            )
            if payload.type:
                cc = CodeableConceptModel(text=payload.type.text)
                if payload.type.coding:
                    cc.codings = [
                        CodingModel(
                            system=c.system,
                            version=c.version,
                            code=c.code,
                            display=c.display,
                            user_selected=c.userSelected,
                        )
                        for c in payload.type.coding
                    ]
                ident.type = cc

            try:
                session.add(ident)
                await session.commit()
            except Exception:
                await session.rollback()
                raise

            return await self.get_by_patient_id(patient_id)

    async def add_telecom(self, patient_id: int, payload: TelecomCreate) -> Optional[PatientModel]:
        async with self.session_factory() as session:
            stmt = select(PatientModel).where(PatientModel.patient_id == patient_id)
            result = await session.execute(stmt)
            patient = result.scalars().first()

            if not patient:
                return None

            telecom = PatientTelecom(
                patient_id=patient.id,
                system=payload.system,
                value=payload.value,
                use=payload.use,
            )
            try:
                session.add(telecom)
                await session.commit()
            except Exception:
                await session.rollback()
                raise

            return await self.get_by_patient_id(patient_id)

    async def add_address(self, patient_id: int, payload: AddressCreate) -> Optional[PatientModel]:
        async with self.session_factory() as session:
            stmt = select(PatientModel).where(PatientModel.patient_id == patient_id)
            result = await session.execute(stmt)
            patient = result.scalars().first()

            if not patient:
                return None

            address = PatientAddress(
                patient_id=patient.id,
                line=payload.line,
                city=payload.city,
                state=payload.state,
                postal_code=payload.postal_code,
                country=payload.country,
            )
            try:
                session.add(address)
                await session.commit()
            except Exception:
                await session.rollback()
                raise

            return await self.get_by_patient_id(patient_id)
