from typing import List, Optional, Tuple
from sqlalchemy import exists, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker  # noqa: F401
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.practitioner import (
    PractitionerModel,
    PractitionerName,
    PractitionerIdentifier,
    PractitionerTelecom,
    PractitionerAddress,
    PractitionerPhoto,
    PractitionerQualification,
    PractitionerQualificationIdentifier,
    PractitionerCommunication,
)
from app.models.enums import OrganizationReferenceType
from app.schemas.practitioner import (
    PractitionerCreateSchema,
    PractitionerPatchSchema,
    PractitionerNameCreate,
    PractitionerIdentifierCreate,
    PractitionerTelecomCreate,
    PractitionerAddressCreate,
    PractitionerPhotoCreate,
    QualificationIdentifierCreate,
    PractitionerQualificationCreate,
    PractitionerCommunicationCreate,
)


def _parse_org_ref(ref: str) -> tuple:
    """Parse 'Organization/123' → (OrganizationReferenceType.ORGANIZATION, 123)."""
    from fastapi import HTTPException
    parts = ref.split("/", 1)
    if len(parts) != 2:
        raise HTTPException(status_code=422, detail=f"Invalid reference format: '{ref}'.")
    try:
        ref_id = int(parts[1])
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid reference id in: '{ref}'.")
    try:
        ref_type = OrganizationReferenceType(parts[0])
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid reference type '{parts[0]}'. Allowed: ['Organization'].")
    return ref_type, ref_id


def _with_relationships(stmt):
    """Eager-load all practitioner sub-resources to avoid N+1 and async lazy-load failures."""
    return stmt.options(
        selectinload(PractitionerModel.names),
        selectinload(PractitionerModel.identifiers),
        selectinload(PractitionerModel.telecoms),
        selectinload(PractitionerModel.addresses),
        selectinload(PractitionerModel.photos),
        selectinload(PractitionerModel.qualifications).selectinload(PractitionerQualification.identifiers),
        selectinload(PractitionerModel.communications),
    )


class PractitionerRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    # ── Read ──────────────────────────────────────────────────────────────

    async def get_by_practitioner_id(self, practitioner_id: int) -> Optional[PractitionerModel]:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(PractitionerModel).where(PractitionerModel.practitioner_id == practitioner_id)
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_user_id(self, user_id: str) -> Optional[PractitionerModel]:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(PractitionerModel).where(PractitionerModel.user_id == user_id)
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_me(self, user_id: str, org_id: str) -> Optional[PractitionerModel]:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(PractitionerModel).where(
                    PractitionerModel.user_id == user_id,
                    PractitionerModel.org_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    def _apply_list_filters(self, stmt, user_id, org_id, family_name, given_name, active):
        if user_id:
            stmt = stmt.where(PractitionerModel.user_id == user_id)
        if org_id:
            stmt = stmt.where(PractitionerModel.org_id == org_id)
        if family_name:
            stmt = stmt.where(
                exists(
                    select(PractitionerName.id).where(
                        PractitionerName.practitioner_id == PractitionerModel.id,
                        PractitionerName.family.ilike(f"%{family_name}%"),
                    )
                )
            )
        if given_name:
            stmt = stmt.where(
                exists(
                    select(PractitionerName.id).where(
                        PractitionerName.practitioner_id == PractitionerModel.id,
                        PractitionerName.given.ilike(f"%{given_name}%"),
                    )
                )
            )
        if active is not None:
            stmt = stmt.where(PractitionerModel.active == active)
        return stmt

    async def list(
        self,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        family_name: Optional[str] = None,
        given_name: Optional[str] = None,
        active: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[PractitionerModel], int]:
        async with self.session_factory() as session:
            base = self._apply_list_filters(
                _with_relationships(select(PractitionerModel)),
                user_id, org_id, family_name, given_name, active,
            )
            count_base = self._apply_list_filters(
                select(func.count()).select_from(PractitionerModel),
                user_id, org_id, family_name, given_name, active,
            )
            total = (await session.execute(count_base)).scalar_one()
            rows = list((await session.execute(
                base.order_by(PractitionerModel.practitioner_id.desc()).offset(offset).limit(limit)
            )).scalars().all())
        return rows, total

    # ── Write ─────────────────────────────────────────────────────────────

    async def create(
        self,
        payload: PractitionerCreateSchema,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> PractitionerModel:
        async with self.session_factory() as session:
            practitioner = PractitionerModel(
                user_id=user_id,
                org_id=org_id,
                active=payload.active,
                gender=payload.gender,
                birth_date=payload.birth_date,
                deceased_boolean=payload.deceased_boolean,
                deceased_datetime=payload.deceased_datetime,
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

    async def patch(
        self,
        practitioner_id: int,
        payload: PractitionerPatchSchema,
        updated_by: Optional[str] = None,
    ) -> Optional[PractitionerModel]:
        async with self.session_factory() as session:
            stmt = select(PractitionerModel).where(PractitionerModel.practitioner_id == practitioner_id)
            practitioner = (await session.execute(stmt)).scalars().first()
            if not practitioner:
                return None
            for field, value in payload.model_dump(exclude_unset=True).items():
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
            practitioner = (await session.execute(stmt)).scalars().first()
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

    async def add_name(
        self, practitioner_id: int, payload: PractitionerNameCreate
    ) -> Optional[PractitionerModel]:
        async with self.session_factory() as session:
            stmt = select(PractitionerModel).where(PractitionerModel.practitioner_id == practitioner_id)
            practitioner = (await session.execute(stmt)).scalars().first()
            if not practitioner:
                return None
            row = PractitionerName(
                practitioner_id=practitioner.id,
                org_id=practitioner.org_id,
                use=payload.use,
                text=payload.text,
                family=payload.family,
                given=",".join(payload.given) if payload.given else None,
                prefix=",".join(payload.prefix) if payload.prefix else None,
                suffix=",".join(payload.suffix) if payload.suffix else None,
                period_start=payload.period_start,
                period_end=payload.period_end,
            )
            try:
                session.add(row)
                await session.commit()
            except Exception:
                await session.rollback()
                raise
        return await self.get_by_practitioner_id(practitioner_id)

    async def add_identifier(
        self, practitioner_id: int, payload: PractitionerIdentifierCreate
    ) -> Optional[PractitionerModel]:
        async with self.session_factory() as session:
            stmt = select(PractitionerModel).where(PractitionerModel.practitioner_id == practitioner_id)
            practitioner = (await session.execute(stmt)).scalars().first()
            if not practitioner:
                return None
            row = PractitionerIdentifier(
                practitioner_id=practitioner.id,
                org_id=practitioner.org_id,
                use=payload.use,
                type_system=payload.type_system,
                type_code=payload.type_code,
                type_display=payload.type_display,
                type_text=payload.type_text,
                system=payload.system,
                value=payload.value,
                period_start=payload.period_start,
                period_end=payload.period_end,
                assigner=payload.assigner,
            )
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
            practitioner = (await session.execute(stmt)).scalars().first()
            if not practitioner:
                return None
            row = PractitionerTelecom(
                practitioner_id=practitioner.id,
                org_id=practitioner.org_id,
                system=payload.system,
                value=payload.value,
                use=payload.use,
                rank=payload.rank,
                period_start=payload.period_start,
                period_end=payload.period_end,
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
            practitioner = (await session.execute(stmt)).scalars().first()
            if not practitioner:
                return None
            row = PractitionerAddress(
                practitioner_id=practitioner.id,
                org_id=practitioner.org_id,
                use=payload.use,
                type=payload.type,
                text=payload.text,
                line=",".join(payload.line) if payload.line else None,
                city=payload.city,
                district=payload.district,
                state=payload.state,
                postal_code=payload.postal_code,
                country=payload.country,
                period_start=payload.period_start,
                period_end=payload.period_end,
            )
            try:
                session.add(row)
                await session.commit()
            except Exception:
                await session.rollback()
                raise
        return await self.get_by_practitioner_id(practitioner_id)

    async def add_photo(
        self, practitioner_id: int, payload: PractitionerPhotoCreate
    ) -> Optional[PractitionerModel]:
        async with self.session_factory() as session:
            stmt = select(PractitionerModel).where(PractitionerModel.practitioner_id == practitioner_id)
            practitioner = (await session.execute(stmt)).scalars().first()
            if not practitioner:
                return None
            row = PractitionerPhoto(
                practitioner_id=practitioner.id,
                org_id=practitioner.org_id,
                content_type=payload.content_type,
                language=payload.language,
                data=payload.data,
                url=payload.url,
                size=payload.size,
                hash=payload.hash,
                title=payload.title,
                creation=payload.creation,
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
            practitioner = (await session.execute(stmt)).scalars().first()
            if not practitioner:
                return None
            qualification = PractitionerQualification(
                practitioner_id=practitioner.id,
                org_id=practitioner.org_id,
                code_system=payload.code_system,
                code_code=payload.code_code,
                code_display=payload.code_display,
                code_text=payload.code_text,
                status_system=payload.status_system,
                status_code=payload.status_code,
                status_display=payload.status_display,
                status_text=payload.status_text,
                period_start=payload.period_start,
                period_end=payload.period_end,
                issuer_type=(_parse_org_ref(payload.issuer)[0] if payload.issuer else None),
                issuer_id=(_parse_org_ref(payload.issuer)[1] if payload.issuer else None),
                issuer_display=payload.issuer_display,
            )
            session.add(qualification)
            await session.flush()  # get qualification.id before adding grandchildren

            if payload.identifier:
                for qi in payload.identifier:
                    session.add(PractitionerQualificationIdentifier(
                        qualification_id=qualification.id,
                        org_id=practitioner.org_id,
                        use=qi.use,
                        type_system=qi.type_system,
                        type_code=qi.type_code,
                        type_display=qi.type_display,
                        type_text=qi.type_text,
                        system=qi.system,
                        value=qi.value,
                        period_start=qi.period_start,
                        period_end=qi.period_end,
                        assigner=qi.assigner,
                    ))

            try:
                await session.commit()
            except Exception:
                await session.rollback()
                raise
        return await self.get_by_practitioner_id(practitioner_id)

    async def add_communication(
        self, practitioner_id: int, payload: PractitionerCommunicationCreate
    ) -> Optional[PractitionerModel]:
        async with self.session_factory() as session:
            stmt = select(PractitionerModel).where(PractitionerModel.practitioner_id == practitioner_id)
            practitioner = (await session.execute(stmt)).scalars().first()
            if not practitioner:
                return None
            row = PractitionerCommunication(
                practitioner_id=practitioner.id,
                org_id=practitioner.org_id,
                language_system=payload.language_system,
                language_code=payload.language_code,
                language_display=payload.language_display,
                language_text=payload.language_text,
                preferred=payload.preferred,
            )
            try:
                session.add(row)
                await session.commit()
            except Exception:
                await session.rollback()
                raise
        return await self.get_by_practitioner_id(practitioner_id)
