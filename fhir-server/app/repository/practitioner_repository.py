from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker  # noqa: F401
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.practitioner import (
    PractitionerModel,
    PractitionerIdentifier,
    PractitionerTelecom,
    PractitionerAddress,
    PractitionerQualification,
)
from app.models.datatypes import CodeableConcept as CodeableConceptModel, Coding as CodingModel
from app.schemas.practitioner import (
    PractitionerCreateSchema,
    PractitionerPatchSchema,
    PractitionerIdentifierCreate,
    PractitionerTelecomCreate,
    PractitionerAddressCreate,
    PractitionerQualificationCreate,
)


def _with_relationships(stmt):
    """Attach eager-load options for all practitioner sub-resources."""
    return stmt.options(
        selectinload(PractitionerModel.identifiers)
            .selectinload(PractitionerIdentifier.type)
            .selectinload(CodeableConceptModel.codings),
        selectinload(PractitionerModel.telecoms),
        selectinload(PractitionerModel.addresses),
        selectinload(PractitionerModel.qualifications),
    )


class PractitionerRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    # ── Read ──────────────────────────────────────────────────────────────

    async def get_by_practitioner_id(self, practitioner_id: int) -> Optional[PractitionerModel]:
        """Fetch by public practitioner_id with all sub-resources loaded."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(PractitionerModel).where(PractitionerModel.practitioner_id == practitioner_id)
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_by_user_id(self, user_id: str) -> Optional[PractitionerModel]:
        """Fetch by user_id with all sub-resources loaded."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(PractitionerModel).where(PractitionerModel.user_id == user_id)
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    async def list(self) -> List[PractitionerModel]:
        async with self.session_factory() as session:
            stmt = _with_relationships(select(PractitionerModel))
            result = await session.execute(stmt)
            return list(result.scalars().all())

    # ── Write ─────────────────────────────────────────────────────────────

    async def get_me(self, user_id: str, org_id: str) -> Optional[PractitionerModel]:
        """Fetch the practitioner profile that belongs to user_id within org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(PractitionerModel).where(
                    PractitionerModel.user_id == user_id,
                    PractitionerModel.org_id == org_id,
                )
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    async def create(self, payload: PractitionerCreateSchema, user_id: Optional[str], org_id: Optional[str] = None, created_by: Optional[str] = None) -> PractitionerModel:
        async with self.session_factory() as session:
            practitioner = PractitionerModel(
                user_id=user_id,
                org_id=org_id,
                given_name=payload.given_name,
                family_name=payload.family_name,
                active=payload.active,
                gender=payload.gender,
                birth_date=payload.birth_date,
                created_by=created_by,
            )
            try:
                session.add(practitioner)
                await session.commit()
                await session.refresh(practitioner)
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_practitioner_id(practitioner.practitioner_id)

    async def patch(self, practitioner_id: int, payload: PractitionerPatchSchema, updated_by: Optional[str] = None) -> Optional[PractitionerModel]:
        """Partial update — only fields explicitly set in payload are written."""
        async with self.session_factory() as session:
            stmt = select(PractitionerModel).where(PractitionerModel.practitioner_id == practitioner_id)
            result = await session.execute(stmt)
            practitioner = result.scalars().first()

            if not practitioner:
                return None

            update_data = payload.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(practitioner, field, value)
            if updated_by is not None:
                practitioner.updated_by = updated_by

            try:
                await session.commit()
                await session.refresh(practitioner)
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_practitioner_id(practitioner_id)

    async def delete(self, practitioner_id: int) -> bool:
        async with self.session_factory() as session:
            stmt = select(PractitionerModel).where(PractitionerModel.practitioner_id == practitioner_id)
            result = await session.execute(stmt)
            practitioner = result.scalars().first()

            if not practitioner:
                return False

            try:
                await session.delete(practitioner)
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                raise

    # ── Sub-resource mutations ────────────────────────────────────────────

    async def add_identifier(
        self, practitioner_id: int, payload: PractitionerIdentifierCreate
    ) -> Optional[PractitionerModel]:
        async with self.session_factory() as session:
            stmt = select(PractitionerModel).where(PractitionerModel.practitioner_id == practitioner_id)
            result = await session.execute(stmt)
            practitioner = result.scalars().first()

            if not practitioner:
                return None

            row = PractitionerIdentifier(
                practitioner_id=practitioner.id,
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
                row.type = cc

            try:
                session.add(row)
                await session.commit()
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_practitioner_id(practitioner_id)

    async def add_telecom(
        self, practitioner_id: int, payload: PractitionerTelecomCreate
    ) -> Optional[PractitionerModel]:
        async with self.session_factory() as session:
            stmt = select(PractitionerModel).where(PractitionerModel.practitioner_id == practitioner_id)
            result = await session.execute(stmt)
            practitioner = result.scalars().first()

            if not practitioner:
                return None

            row = PractitionerTelecom(
                practitioner_id=practitioner.id,
                system=payload.system,
                value=payload.value,
                use=payload.use,
                rank=payload.rank,
            )
            try:
                session.add(row)
                await session.commit()
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_practitioner_id(practitioner_id)

    async def add_address(
        self, practitioner_id: int, payload: PractitionerAddressCreate
    ) -> Optional[PractitionerModel]:
        async with self.session_factory() as session:
            stmt = select(PractitionerModel).where(PractitionerModel.practitioner_id == practitioner_id)
            result = await session.execute(stmt)
            practitioner = result.scalars().first()

            if not practitioner:
                return None

            row = PractitionerAddress(
                practitioner_id=practitioner.id,
                use=payload.use,
                type=payload.type,
                text=payload.text,
                line=payload.line,
                city=payload.city,
                district=payload.district,
                state=payload.state,
                postal_code=payload.postal_code,
                country=payload.country,
            )
            try:
                session.add(row)
                await session.commit()
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_practitioner_id(practitioner_id)

    async def add_qualification(
        self, practitioner_id: int, payload: PractitionerQualificationCreate
    ) -> Optional[PractitionerModel]:
        async with self.session_factory() as session:
            stmt = select(PractitionerModel).where(PractitionerModel.practitioner_id == practitioner_id)
            result = await session.execute(stmt)
            practitioner = result.scalars().first()

            if not practitioner:
                return None

            row = PractitionerQualification(
                practitioner_id=practitioner.id,
                identifier_system=payload.identifier_system,
                identifier_value=payload.identifier_value,
                code_text=payload.code_text,
                issuer=payload.issuer,
            )
            try:
                session.add(row)
                await session.commit()
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_practitioner_id(practitioner_id)
