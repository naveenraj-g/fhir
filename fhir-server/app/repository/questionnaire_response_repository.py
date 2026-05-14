from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker  # noqa: F401
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.questionnaire_response.questionnaire_response import (
    QuestionnaireResponseModel,
    QuestionnaireResponseItemModel,
    QuestionnaireResponseAnswerModel,
)
from app.models.questionnaire_response.enums import (
    QuestionnaireResponseAuthorReferenceType,
    QuestionnaireResponseSourceReferenceType,
)
from app.models.encounter.encounter import EncounterModel
from app.models.enums import SubjectReferenceType
from app.schemas.questionnaire_response import (
    QuestionnaireResponseCreateSchema,
    QuestionnaireResponsePatchSchema,
    ItemInput,
    AnswerInput,
)


def _with_relationships(stmt):
    """Attach eager-load options for encounter + items (2 levels deep) with answers."""
    return stmt.options(
        selectinload(QuestionnaireResponseModel.encounter),
        selectinload(QuestionnaireResponseModel.items).selectinload(
            QuestionnaireResponseItemModel.answers
        ),
        selectinload(QuestionnaireResponseModel.items)
        .selectinload(QuestionnaireResponseItemModel.sub_items)
        .selectinload(QuestionnaireResponseItemModel.answers),
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


def _parse_author(author_str: Optional[str]):
    """Parse 'Practitioner/30001' → (QuestionnaireResponseAuthorReferenceType, 30001)."""
    if not author_str:
        return None, None
    parts = author_str.split("/")
    if len(parts) != 2:
        return None, None
    try:
        return QuestionnaireResponseAuthorReferenceType(parts[0]), int(parts[1])
    except (ValueError, KeyError):
        return None, None


def _parse_source(source_str: Optional[str]):
    """Parse 'Patient/10001' → (QuestionnaireResponseSourceReferenceType, 10001)."""
    if not source_str:
        return None, None
    parts = source_str.split("/")
    if len(parts) != 2:
        return None, None
    try:
        return QuestionnaireResponseSourceReferenceType(parts[0]), int(parts[1])
    except (ValueError, KeyError):
        return None, None


def _parse_encounter_ref(encounter_str: Optional[str]) -> Optional[int]:
    """Parse 'Encounter/20001' → public encounter_id 20001."""
    if not encounter_str:
        return None
    parts = encounter_str.split("/")
    if len(parts) != 2 or parts[0] != "Encounter":
        return None
    try:
        return int(parts[1])
    except ValueError:
        return None


def _build_answer(answer: AnswerInput) -> QuestionnaireResponseAnswerModel:
    db = QuestionnaireResponseAnswerModel(value_type="unknown")

    if answer.value_boolean is not None:
        db.value_type = "boolean"
        db.value_boolean = answer.value_boolean
    elif answer.value_decimal is not None:
        db.value_type = "decimal"
        db.value_decimal = answer.value_decimal
    elif answer.value_integer is not None:
        db.value_type = "integer"
        db.value_integer = answer.value_integer
    elif answer.value_date is not None:
        db.value_type = "date"
        db.value_string = answer.value_date
    elif answer.value_datetime is not None:
        db.value_type = "dateTime"
        db.value_datetime = answer.value_datetime
    elif answer.value_time is not None:
        db.value_type = "time"
        db.value_string = answer.value_time
    elif answer.value_string is not None:
        db.value_type = "string"
        db.value_string = answer.value_string
    elif answer.value_uri is not None:
        db.value_type = "uri"
        db.value_string = answer.value_uri
    elif answer.value_coding is not None:
        db.value_type = "coding"
        db.value_coding_system = answer.value_coding.system
        db.value_coding_code = answer.value_coding.code
        db.value_coding_display = answer.value_coding.display
    elif answer.value_quantity is not None:
        db.value_type = "quantity"
        db.value_quantity_value = answer.value_quantity.value
        db.value_quantity_unit = answer.value_quantity.unit
        db.value_quantity_system = answer.value_quantity.system
        db.value_quantity_code = answer.value_quantity.code
    elif answer.value_reference is not None:
        db.value_type = "reference"
        db.value_reference = answer.value_reference

    return db


def _build_item(item: ItemInput, response_id: int) -> QuestionnaireResponseItemModel:
    db_item = QuestionnaireResponseItemModel(
        response_id=response_id,
        link_id=item.link_id,
        text=item.text,
        definition=item.definition,
    )
    if item.answer:
        for a in item.answer:
            db_item.answers.append(_build_answer(a))
    if item.item:
        for sub in item.item:
            db_item.sub_items.append(_build_item(sub, response_id))
    return db_item


class QuestionnaireResponseRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    # ── Read ──────────────────────────────────────────────────────────────

    async def get_by_qr_id(
        self, questionnaire_response_id: int
    ) -> Optional[QuestionnaireResponseModel]:
        """Fetch by public questionnaire_response_id with all items loaded."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(QuestionnaireResponseModel).where(
                    QuestionnaireResponseModel.questionnaire_response_id
                    == questionnaire_response_id
                )
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_me(
        self, user_id: str, org_id: str
    ) -> List[QuestionnaireResponseModel]:
        """Fetch all QuestionnaireResponses owned by user_id within org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(QuestionnaireResponseModel).where(
                    QuestionnaireResponseModel.user_id == user_id,
                    QuestionnaireResponseModel.org_id == org_id,
                )
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def list(
        self,
        patient_id: Optional[int] = None,
        encounter_id: Optional[int] = None,
    ) -> List[QuestionnaireResponseModel]:
        """List responses, optionally filtered by public patient_id or encounter_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(select(QuestionnaireResponseModel))

            if patient_id is not None:
                stmt = stmt.where(
                    QuestionnaireResponseModel.subject_type == SubjectReferenceType.PATIENT,
                    QuestionnaireResponseModel.subject_id == patient_id,
                )

            if encounter_id is not None:
                enc_result = await session.execute(
                    select(EncounterModel.id).where(
                        EncounterModel.encounter_id == encounter_id
                    )
                )
                internal_enc_id = enc_result.scalar_one_or_none()
                if internal_enc_id is not None:
                    stmt = stmt.where(
                        QuestionnaireResponseModel.encounter_id == internal_enc_id
                    )
                else:
                    return []

            result = await session.execute(stmt)
            return list(result.scalars().all())

    # ── Write ─────────────────────────────────────────────────────────────

    async def create(
        self,
        payload: QuestionnaireResponseCreateSchema,
        user_id: str,
        org_id: Optional[str] = None,
    ) -> QuestionnaireResponseModel:
        subject_type, subject_id = _parse_subject(payload.subject)
        author_type, author_id = _parse_author(payload.author)
        source_type, source_id = _parse_source(payload.source)
        public_encounter_id = _parse_encounter_ref(payload.encounter)

        async with self.session_factory() as session:
            # Resolve public encounter_id → internal encounter PK
            internal_encounter_id: Optional[int] = None
            if public_encounter_id is not None:
                enc_result = await session.execute(
                    select(EncounterModel.id).where(
                        EncounterModel.encounter_id == public_encounter_id
                    )
                )
                internal_encounter_id = enc_result.scalar_one_or_none()

            qr = QuestionnaireResponseModel(
                user_id=user_id,
                org_id=org_id,
                questionnaire=payload.questionnaire,
                status=payload.status,
                subject_type=subject_type,
                subject_id=subject_id,
                subject_display=payload.subject_display,
                encounter_id=internal_encounter_id,
                authored=payload.authored,
                author_reference_type=author_type,
                author_reference_id=author_id,
                author_reference_display=payload.author_display,
                source_reference_type=source_type,
                source_reference_id=source_id,
                source_reference_display=payload.source_display,
            )

            try:
                session.add(qr)
                await session.flush()  # inserts qr row alone → qr.id is now set

                if payload.item:
                    for item in payload.item:
                        session.add(_build_item(item, qr.id))

                await session.commit()
                await session.refresh(qr)
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_qr_id(qr.questionnaire_response_id)

    async def patch(
        self,
        questionnaire_response_id: int,
        payload: QuestionnaireResponsePatchSchema,
    ) -> Optional[QuestionnaireResponseModel]:
        """Partial update — only status and authored are patchable."""
        async with self.session_factory() as session:
            stmt = select(QuestionnaireResponseModel).where(
                QuestionnaireResponseModel.questionnaire_response_id
                == questionnaire_response_id
            )
            result = await session.execute(stmt)
            qr = result.scalars().first()

            if not qr:
                return None

            update_data = payload.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(qr, field, value)

            try:
                await session.commit()
                await session.refresh(qr)
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_qr_id(questionnaire_response_id)

    async def delete(self, questionnaire_response_id: int) -> bool:
        async with self.session_factory() as session:
            stmt = select(QuestionnaireResponseModel).where(
                QuestionnaireResponseModel.questionnaire_response_id
                == questionnaire_response_id
            )
            result = await session.execute(stmt)
            qr = result.scalars().first()

            if not qr:
                return False

            try:
                await session.delete(qr)
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                raise
