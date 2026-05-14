from typing import List, Optional, Tuple

from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker  # noqa: F401
from sqlalchemy.orm import selectinload

from app.models.patient.patient import (
    PatientModel,
    PatientAddress,
    PatientCommunication,
    PatientContact,
    PatientContactRelationship,
    PatientContactTelecom,
    PatientGeneralPractitioner,
    PatientIdentifier,
    PatientLink,
    PatientName,
    PatientPhoto,
    PatientTelecom,
)
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


def _with_relationships(stmt):
    return stmt.options(
        selectinload(PatientModel.names),
        selectinload(PatientModel.identifiers),
        selectinload(PatientModel.telecoms),
        selectinload(PatientModel.addresses),
        selectinload(PatientModel.photos),
        selectinload(PatientModel.contacts).selectinload(PatientContact.relationships),
        selectinload(PatientModel.contacts).selectinload(PatientContact.telecoms),
        selectinload(PatientModel.communications),
        selectinload(PatientModel.general_practitioners),
        selectinload(PatientModel.links),
    )


class PatientRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    # ── Read ──────────────────────────────────────────────────────────────────

    async def get_by_patient_id(self, patient_id: int) -> Optional[PatientModel]:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(PatientModel).where(PatientModel.patient_id == patient_id)
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_by_patient_id_in_org(
        self, patient_id: int, user_id: str, org_id: str
    ) -> Optional[PatientModel]:
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
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(PatientModel).where(PatientModel.user_id == user_id)
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_me(self, user_id: str, org_id: str) -> Optional[PatientModel]:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(PatientModel).where(
                    PatientModel.user_id == user_id,
                    PatientModel.org_id == org_id,
                )
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    def _apply_list_filters(self, stmt, user_id, org_id, family_name, given_name, gender, active):
        if user_id:
            stmt = stmt.where(PatientModel.user_id == user_id)
        if org_id:
            stmt = stmt.where(PatientModel.org_id == org_id)
        if family_name:
            stmt = stmt.where(
                exists(
                    select(PatientName.id).where(
                        PatientName.patient_id == PatientModel.id,
                        PatientName.family.ilike(f"%{family_name}%"),
                    )
                )
            )
        if given_name:
            stmt = stmt.where(
                exists(
                    select(PatientName.id).where(
                        PatientName.patient_id == PatientModel.id,
                        PatientName.given.ilike(f"%{given_name}%"),
                    )
                )
            )
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

    # ── Write ─────────────────────────────────────────────────────────────────

    async def create(
        self,
        payload: PatientCreateSchema,
        user_id: Optional[str],
        org_id: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> PatientModel:
        async with self.session_factory() as session:
            patient = PatientModel(
                user_id=user_id,
                org_id=org_id,
                active=payload.active,
                gender=payload.gender,
                birth_date=payload.birth_date,
                deceased_boolean=payload.deceased_boolean,
                deceased_datetime=payload.deceased_datetime,
                marital_status_system=payload.marital_status_system,
                marital_status_code=payload.marital_status_code,
                marital_status_display=payload.marital_status_display,
                marital_status_text=payload.marital_status_text,
                multiple_birth_boolean=payload.multiple_birth_boolean,
                multiple_birth_integer=payload.multiple_birth_integer,
                managing_organization_id=payload.managing_organization_id,
                managing_organization_display=payload.managing_organization_display,
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

    async def patch(
        self,
        patient_id: int,
        payload: PatientPatchSchema,
        updated_by: Optional[str] = None,
    ) -> Optional[PatientModel]:
        async with self.session_factory() as session:
            stmt = select(PatientModel).where(PatientModel.patient_id == patient_id)
            result = await session.execute(stmt)
            patient = result.scalars().first()

            if not patient:
                return None

            for field, value in payload.model_dump(exclude_unset=True).items():
                setattr(patient, field, value)
            if updated_by is not None:
                patient.updated_by = updated_by

            try:
                await session.commit()
                await session.refresh(patient)
            except Exception:
                await session.rollback()
                raise

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

    # ── Sub-resource mutations ─────────────────────────────────────────────────

    async def _get_internal(self, session, patient_id: int) -> Optional[PatientModel]:
        """Fetch by public patient_id — internal PK only, no relationships loaded."""
        result = await session.execute(
            select(PatientModel).where(PatientModel.patient_id == patient_id)
        )
        return result.scalars().first()

    async def add_name(self, patient_id: int, payload: NameCreate) -> Optional[PatientModel]:
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return None

            name = PatientName(
                patient_id=patient.id,
                org_id=patient.org_id,
                use=payload.use,
                text=payload.text,
                family=payload.family,
                given=", ".join(payload.given) if payload.given else None,
                prefix=", ".join(payload.prefix) if payload.prefix else None,
                suffix=", ".join(payload.suffix) if payload.suffix else None,
                period_start=payload.period_start,
                period_end=payload.period_end,
            )
            try:
                session.add(name)
                await session.commit()
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_patient_id(patient_id)

    async def add_identifier(self, patient_id: int, payload: IdentifierCreate) -> Optional[PatientModel]:
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return None

            ident = PatientIdentifier(
                patient_id=patient.id,
                org_id=patient.org_id,
                use=payload.use,
                type_system=payload.type_system,
                type_code=payload.type_code,
                type_display=payload.type_display,
                system=payload.system,
                value=payload.value,
                period_start=payload.period_start,
                period_end=payload.period_end,
                assigner=payload.assigner,
            )
            try:
                session.add(ident)
                await session.commit()
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_patient_id(patient_id)

    async def add_telecom(self, patient_id: int, payload: TelecomCreate) -> Optional[PatientModel]:
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return None

            telecom = PatientTelecom(
                patient_id=patient.id,
                org_id=patient.org_id,
                system=payload.system,
                value=payload.value,
                use=payload.use,
                rank=payload.rank,
                period_start=payload.period_start,
                period_end=payload.period_end,
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
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return None

            address = PatientAddress(
                patient_id=patient.id,
                org_id=patient.org_id,
                use=payload.use,
                type=payload.type,
                text=payload.text,
                line=", ".join(payload.line) if payload.line else None,
                city=payload.city,
                district=payload.district,
                state=payload.state,
                postal_code=payload.postal_code,
                country=payload.country,
                period_start=payload.period_start,
                period_end=payload.period_end,
            )
            try:
                session.add(address)
                await session.commit()
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_patient_id(patient_id)

    async def add_photo(self, patient_id: int, payload: PhotoCreate) -> Optional[PatientModel]:
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return None

            photo = PatientPhoto(
                patient_id=patient.id,
                org_id=patient.org_id,
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
                session.add(photo)
                await session.commit()
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_patient_id(patient_id)

    async def add_contact(self, patient_id: int, payload: ContactCreate) -> Optional[PatientModel]:
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return None

            contact = PatientContact(
                patient_id=patient.id,
                org_id=patient.org_id,
                name_use=payload.name_use,
                name_text=payload.name_text,
                name_family=payload.name_family,
                name_given=", ".join(payload.name_given) if payload.name_given else None,
                name_prefix=", ".join(payload.name_prefix) if payload.name_prefix else None,
                name_suffix=", ".join(payload.name_suffix) if payload.name_suffix else None,
                address_use=payload.address_use,
                address_type=payload.address_type,
                address_text=payload.address_text,
                address_line=", ".join(payload.address_line) if payload.address_line else None,
                address_city=payload.address_city,
                address_district=payload.address_district,
                address_state=payload.address_state,
                address_postal_code=payload.address_postal_code,
                address_country=payload.address_country,
                address_period_start=payload.address_period_start,
                address_period_end=payload.address_period_end,
                gender=payload.gender,
                organization_id=payload.organization_id,
                organization_display=payload.organization_display,
                period_start=payload.period_start,
                period_end=payload.period_end,
            )
            session.add(contact)
            await session.flush()  # get contact.id before adding grandchildren

            if payload.relationship:
                for r in payload.relationship:
                    session.add(PatientContactRelationship(
                        contact_id=contact.id,
                        org_id=patient.org_id,
                        coding_system=r.coding_system,
                        coding_code=r.coding_code,
                        coding_display=r.coding_display,
                        text=r.text,
                    ))

            if payload.telecom:
                for t in payload.telecom:
                    session.add(PatientContactTelecom(
                        contact_id=contact.id,
                        org_id=patient.org_id,
                        system=t.system,
                        value=t.value,
                        use=t.use,
                        rank=t.rank,
                        period_start=t.period_start,
                        period_end=t.period_end,
                    ))

            try:
                await session.commit()
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_patient_id(patient_id)

    async def add_communication(
        self, patient_id: int, payload: CommunicationCreate
    ) -> Optional[PatientModel]:
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return None

            comm = PatientCommunication(
                patient_id=patient.id,
                org_id=patient.org_id,
                language_system=payload.language_system,
                language_code=payload.language_code,
                language_display=payload.language_display,
                language_text=payload.language_text,
                preferred=payload.preferred,
            )
            try:
                session.add(comm)
                await session.commit()
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_patient_id(patient_id)

    async def add_general_practitioner(
        self, patient_id: int, payload: GeneralPractitionerCreate
    ) -> Optional[PatientModel]:
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return None

            gp = PatientGeneralPractitioner(
                patient_id=patient.id,
                org_id=patient.org_id,
                reference_type=payload.reference_type,
                reference_id=payload.reference_id,
                reference_display=payload.reference_display,
            )
            try:
                session.add(gp)
                await session.commit()
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_patient_id(patient_id)

    async def add_link(self, patient_id: int, payload: LinkCreate) -> Optional[PatientModel]:
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return None

            link = PatientLink(
                patient_id=patient.id,
                org_id=patient.org_id,
                other_type=payload.other_type,
                other_id=payload.other_id,
                other_display=payload.other_display,
                type=payload.type,
            )
            try:
                session.add(link)
                await session.commit()
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_patient_id(patient_id)
