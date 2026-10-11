from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Tuple

from fastapi import HTTPException, status as http_status
from sqlalchemy import func, or_
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker  # noqa: F401
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.search_params import (
    enum_token_values,
    instant_clause,
    parse_date_param,
    parse_open_reference_param,
    parse_reference_param,
    reference_clause,
    split_or,
    token_clause,
)
from app.models.enums import EncounterReferenceType
from app.models.questionnaire_response.enums import (
    QRBasedOnReferenceType,
    QRPartOfReferenceType,
    QuestionnaireResponseAuthorReferenceType,
    QuestionnaireResponseSourceReferenceType,
    QuestionnaireResponseStatus,
)
from app.models.questionnaire_response.questionnaire_response import (
    QuestionnaireResponseAnswerModel,
    QuestionnaireResponseBasedOn,
    QuestionnaireResponseItemModel,
    QuestionnaireResponseModel,
    QuestionnaireResponsePartOf,
)
from app.schemas.questionnaire_response import (
    AnswerInput,
    ItemInput,
    QuestionnaireResponseCreateSchema,
    QuestionnaireResponsePatchSchema,
)


@dataclass
class QRSearch:
    """FHIR R4 QuestionnaireResponse search parameters (https://www.hl7.org/fhir/R4/questionnaireresponse.html#search)."""

    id: Optional[str] = None                      # _id
    identifier: Optional[str] = None
    questionnaire: Optional[str] = None
    q_status: Optional[str] = None
    subject: Optional[str] = None
    patient: Optional[str] = None
    encounter: Optional[str] = None
    author: Optional[str] = None
    source: Optional[str] = None
    based_on: Optional[str] = None
    part_of: Optional[str] = None
    authored: List[str] = field(default_factory=list)
    last_updated: List[str] = field(default_factory=list)   # _lastUpdated
    authored_from: Optional[datetime] = None      # legacy range helpers
    authored_to: Optional[datetime] = None


class _PatientOnly(str, Enum):
    Patient = "Patient"


def _with_relationships(stmt):
    """Eager-load the encounter, basedOn/partOf and EVERY item (all depths) with its answers."""
    return stmt.options(
        selectinload(QuestionnaireResponseModel.based_ons),
        selectinload(QuestionnaireResponseModel.part_ofs),
        selectinload(QuestionnaireResponseModel.items).selectinload(QuestionnaireResponseItemModel.answers),
    )


def _unprocessable(detail: str) -> HTTPException:
    return HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


def _parse_ref(ref: str, enum_cls, field_name: str):
    """
    Parse 'Type/id' (format check only — existence is never verified).

    With enum_cls the type must be one of the allowed values; with None
    (Reference(Any)) any resource type string is accepted.
    """
    parts = ref.split("/", 1)
    if len(parts) != 2 or not parts[0]:
        raise _unprocessable(f"Invalid reference format '{ref}' for {field_name}. Expected 'ResourceType/id'.")
    try:
        ref_id = int(parts[1])
    except ValueError:
        raise _unprocessable(f"Invalid reference id in '{ref}' for {field_name}. Id must be an integer.")
    if enum_cls is None:
        return parts[0], ref_id
    try:
        return enum_cls(parts[0]), ref_id
    except ValueError:
        raise _unprocessable(
            f"Invalid reference type '{parts[0]}' for {field_name}. Allowed: {[e.value for e in enum_cls]}."
        )


def _optional_ref(ref: Optional[str], enum_cls, field_name: str):
    return _parse_ref(ref, enum_cls, field_name) if ref else (None, None)


def _parse_encounter_ref(ref: str) -> int:
    """'Encounter/20001' -> 20001 (format check; a bare number is also accepted)."""
    parts = ref.split("/")
    if len(parts) == 2 and parts[0] == "Encounter":
        raw = parts[1]
    elif len(parts) == 1:
        raw = parts[0]
    else:
        raise _unprocessable(f"Invalid encounter reference '{ref}'. Expected 'Encounter/<id>'.")
    try:
        return int(raw)
    except ValueError:
        raise _unprocessable(f"Invalid encounter reference '{ref}'. Id must be an integer.")


def _fill_answer(db: QuestionnaireResponseAnswerModel, answer: AnswerInput) -> None:
    """Copy the single populated value[x] variant onto the typed columns and set the discriminator."""
    if answer.value_boolean is not None:
        db.value_type, db.value_boolean = "boolean", answer.value_boolean
    elif answer.value_decimal is not None:
        db.value_type, db.value_decimal = "decimal", answer.value_decimal
    elif answer.value_integer is not None:
        db.value_type, db.value_integer = "integer", answer.value_integer
    elif answer.value_date is not None:
        db.value_type, db.value_date = "date", answer.value_date
    elif answer.value_datetime is not None:
        db.value_type, db.value_datetime = "dateTime", answer.value_datetime
    elif answer.value_time is not None:
        db.value_type, db.value_time = "time", answer.value_time
    elif answer.value_string is not None:
        db.value_type, db.value_string = "string", answer.value_string
    elif answer.value_uri is not None:
        db.value_type, db.value_uri = "uri", answer.value_uri
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
        _parse_ref(answer.value_reference, None, "answer.value_reference")  # format check only
        db.value_type = "reference"
        db.value_reference = answer.value_reference
        db.value_reference_display = answer.value_reference_display
    elif answer.value_attachment is not None:
        db.value_type = "attachment"
        att = answer.value_attachment
        db.value_attachment_content_type = att.content_type
        db.value_attachment_language = att.language
        db.value_attachment_data = att.data
        db.value_attachment_url = att.url
        db.value_attachment_size = att.size
        db.value_attachment_hash = att.hash
        db.value_attachment_title = att.title
        db.value_attachment_creation = att.creation


def _build_items(
    qr: QuestionnaireResponseModel,
    items: Optional[List[ItemInput]],
    parent_item: Optional[QuestionnaireResponseItemModel],
    parent_answer: Optional[QuestionnaireResponseAnswerModel],
    org_id: Optional[str],
    counter: List[int],
    session,
) -> None:
    """
    Depth-first creation of the item tree. Every row belongs to the response (so the whole
    tree loads in one query); `counter` assigns a global sibling-order position.
    """
    for node in items or []:
        counter[0] += 1
        db_item = QuestionnaireResponseItemModel(
            response=qr, org_id=org_id, position=counter[0],
            link_id=node.link_id, text=node.text, definition=node.definition,
        )
        if parent_item is not None:
            parent_item.sub_items.append(db_item)
        if parent_answer is not None:
            parent_answer.answer_items.append(db_item)
        session.add(db_item)

        for a in node.answer or []:
            db_answer = QuestionnaireResponseAnswerModel(item=db_item, org_id=org_id)
            _fill_answer(db_answer, a)
            session.add(db_answer)
            _build_items(qr, a.item, None, db_answer, org_id, counter, session)

        _build_items(qr, node.item, db_item, None, org_id, counter, session)


# Child-list fields shared by create and patch: payload field -> QuestionnaireResponseModel relationship name.
CHILD_FIELDS = {"based_on": "based_ons", "part_of": "part_ofs", "item": "items"}


class _OnlyFields:
    """View of a payload exposing only the listed fields; every other attribute reads as None."""

    def __init__(self, payload, fields):
        self._payload = payload
        self._fields = set(fields)

    def __getattr__(self, name):
        return getattr(self._payload, name) if name in self._fields else None


def _add_children(session, qr, payload, org_id) -> None:
    """Create basedOn / partOf rows and the whole item/answer tree for each list present on `payload`."""
    for b in payload.based_on or []:
        ref_type, ref_id = _parse_ref(b.reference, QRBasedOnReferenceType, "basedOn.reference")
        qr.based_ons.append(QuestionnaireResponseBasedOn(
            org_id=org_id, reference_type=ref_type, reference_id=ref_id,
            reference_display=b.reference_display))
    for p in payload.part_of or []:
        ref_type, ref_id = _parse_ref(p.reference, QRPartOfReferenceType, "partOf.reference")
        qr.part_ofs.append(QuestionnaireResponsePartOf(
            org_id=org_id, reference_type=ref_type, reference_id=ref_id,
            reference_display=p.reference_display))
    _build_items(qr, payload.item, None, None, org_id, [0], session)


class QuestionnaireResponseRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    # ── Read ──────────────────────────────────────────────────────────────────

    async def get_by_qr_id(self, questionnaire_response_id: int) -> Optional[QuestionnaireResponseModel]:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(QuestionnaireResponseModel).where(
                    QuestionnaireResponseModel.questionnaire_response_id == questionnaire_response_id
                )
            )
            return (await session.execute(stmt)).scalars().first()

    def _apply_list_filters(self, stmt, user_id, org_id, search: Optional[QRSearch] = None):
        """user_id/org_id are optional tenant filters; `search` carries FHIR R4 search params."""
        if user_id:
            stmt = stmt.where(QuestionnaireResponseModel.user_id == user_id)
        if org_id:
            stmt = stmt.where(QuestionnaireResponseModel.org_id == org_id)
        if search is None:
            return stmt
        M = QuestionnaireResponseModel

        if search.id:
            ids = []
            for v in split_or(search.id):
                try:
                    ids.append(int(v))
                except ValueError:
                    raise _unprocessable(f"Invalid _id '{v}'. Must be an integer.")
            stmt = stmt.where(M.questionnaire_response_id.in_(ids))

        clause = token_clause(M.identifier_system, M.identifier_value, search.identifier)
        if clause is not None:
            stmt = stmt.where(clause)

        # questionnaire — stored as canonical URL or 'Questionnaire/<id>'; also accept a bare id
        # or 'Questionnaire/<id>' against a URL ending in '/Questionnaire/<id>'.
        options = []
        for v in split_or(search.questionnaire):
            options.append(M.questionnaire == v)
            tail = v.split("/")[-1]
            if tail.isdigit():
                options.append(M.questionnaire == f"Questionnaire/{tail}")
                options.append(M.questionnaire.like(f"%/Questionnaire/{tail}"))
        if options:
            stmt = stmt.where(or_(*options))

        statuses = enum_token_values(search.q_status, QuestionnaireResponseStatus, "status")
        if statuses:
            stmt = stmt.where(M.status.in_(statuses))

        # subject (Reference(Any)) / patient (Patient only)
        if search.subject:
            stmt = stmt.where(reference_clause(
                M.subject_type, M.subject_id, parse_open_reference_param(search.subject, "subject")))
        if search.patient:
            stmt = stmt.where(reference_clause(
                M.subject_type, M.subject_id, parse_reference_param(search.patient, _PatientOnly, "patient")))

        if search.encounter:
            stmt = stmt.where(reference_clause(
                M.encounter_type, M.encounter_id,
                parse_reference_param(search.encounter, EncounterReferenceType, "encounter")))

        if search.author:
            stmt = stmt.where(reference_clause(
                M.author_type, M.author_id,
                parse_reference_param(search.author, QuestionnaireResponseAuthorReferenceType, "author")))
        if search.source:
            stmt = stmt.where(reference_clause(
                M.source_type, M.source_id,
                parse_reference_param(search.source, QuestionnaireResponseSourceReferenceType, "source")))

        for value, child, enum_cls, name in (
            (search.based_on, QuestionnaireResponseBasedOn, QRBasedOnReferenceType, "based-on"),
            (search.part_of, QuestionnaireResponsePartOf, QRPartOfReferenceType, "part-of"),
        ):
            if value:
                clause = reference_clause(
                    child.reference_type, child.reference_id, parse_reference_param(value, enum_cls, name))
                stmt = stmt.where(select(child.id).where(child.response_id == M.id, clause).exists())

        for value in search.authored or []:
            prefix, s_lo, s_hi = parse_date_param(value, "authored")
            stmt = stmt.where(instant_clause(M.authored, prefix, s_lo, s_hi))
        if search.authored_from is not None:
            stmt = stmt.where(M.authored >= search.authored_from)
        if search.authored_to is not None:
            stmt = stmt.where(M.authored <= search.authored_to)

        for value in search.last_updated or []:
            prefix, s_lo, s_hi = parse_date_param(value, "_lastUpdated")
            stmt = stmt.where(instant_clause(func.coalesce(M.updated_at, M.created_at), prefix, s_lo, s_hi))
        return stmt

    async def _search(
        self, user_id, org_id, search: Optional[QRSearch], limit: int, offset: int
    ) -> Tuple[List[QuestionnaireResponseModel], int]:
        async with self.session_factory() as session:
            base = self._apply_list_filters(
                _with_relationships(select(QuestionnaireResponseModel)), user_id, org_id, search)
            count_base = self._apply_list_filters(
                select(func.count()).select_from(QuestionnaireResponseModel), user_id, org_id, search)
            total = (await session.execute(count_base)).scalar_one()
            rows = list((await session.execute(
                base.order_by(QuestionnaireResponseModel.authored.desc().nulls_last(),
                              QuestionnaireResponseModel.id.desc())
                .offset(offset).limit(limit)
            )).scalars().all())
        return rows, total

    async def get_me(
        self, user_id: str, org_id: str, search: Optional[QRSearch] = None, limit: int = 50, offset: int = 0
    ) -> Tuple[List[QuestionnaireResponseModel], int]:
        return await self._search(user_id, org_id, search, limit, offset)

    async def list(
        self, user_id: Optional[str] = None, org_id: Optional[str] = None,
        search: Optional[QRSearch] = None, limit: int = 50, offset: int = 0,
    ) -> Tuple[List[QuestionnaireResponseModel], int]:
        return await self._search(user_id, org_id, search, limit, offset)

    # ── Write ─────────────────────────────────────────────────────────────────

    async def create(
        self,
        payload: QuestionnaireResponseCreateSchema,
        user_id: Optional[str],
        org_id: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> QuestionnaireResponseModel:
        # Format checks happen before any DB work so bad references fail fast.
        subject_type, subject_id = _optional_ref(payload.subject, None, "subject")
        author_type, author_id = _optional_ref(payload.author, QuestionnaireResponseAuthorReferenceType, "author")
        source_type, source_id = _optional_ref(payload.source, QuestionnaireResponseSourceReferenceType, "source")

        async with self.session_factory() as session:
            encounter_public_id: Optional[int] = None
            if payload.encounter:
                encounter_public_id = _parse_encounter_ref(payload.encounter)

            qr = QuestionnaireResponseModel(
                user_id=user_id, org_id=org_id, created_by=created_by,
                questionnaire=payload.questionnaire, status=payload.status,
                identifier_use=payload.identifier_use,
                identifier_type_system=payload.identifier_type_system,
                identifier_type_code=payload.identifier_type_code,
                identifier_type_display=payload.identifier_type_display,
                identifier_type_text=payload.identifier_type_text,
                identifier_system=payload.identifier_system,
                identifier_value=payload.identifier_value,
                identifier_period_start=payload.identifier_period_start,
                identifier_period_end=payload.identifier_period_end,
                identifier_assigner=payload.identifier_assigner,
                subject_type=subject_type, subject_id=subject_id, subject_display=payload.subject_display,
                encounter_type=EncounterReferenceType.Encounter if encounter_public_id else None,
                encounter_id=encounter_public_id, encounter_display=payload.encounter_display,
                authored=payload.authored,
                author_type=author_type, author_id=author_id, author_display=payload.author_display,
                source_type=source_type, source_id=source_id, source_display=payload.source_display,
            )

            session.add(qr)
            _add_children(session, qr, payload, org_id)
            await session.commit()

            stmt = _with_relationships(select(QuestionnaireResponseModel).where(QuestionnaireResponseModel.id == qr.id))
            return (await session.execute(stmt)).scalars().one()

    async def patch(
        self,
        questionnaire_response_id: int,
        payload: QuestionnaireResponsePatchSchema,
        updated_by: Optional[str] = None,
    ) -> Optional[QuestionnaireResponseModel]:
        async with self.session_factory() as session:
            stmt = _with_relationships(select(QuestionnaireResponseModel).where(
                QuestionnaireResponseModel.questionnaire_response_id == questionnaire_response_id))
            qr = (await session.execute(stmt)).scalars().first()
            if not qr:
                return None

            updates = payload.model_dump(exclude_unset=True, exclude=set(CHILD_FIELDS))

            # Reference fields arrive as 'Type/id' strings; null clears the optional ones.
            if "subject" in updates:
                ref = updates.pop("subject")
                qr.subject_type, qr.subject_id = _optional_ref(ref, None, "subject")
                if ref is None:
                    updates.setdefault("subject_display", None)
            if "encounter" in updates:
                ref = updates.pop("encounter")
                if ref is None:
                    qr.encounter_id, qr.encounter_type = None, None
                    updates.setdefault("encounter_display", None)
                else:
                    qr.encounter_id = _parse_encounter_ref(ref)
                    qr.encounter_type = EncounterReferenceType.Encounter
            for key, enum_cls in (
                ("author", QuestionnaireResponseAuthorReferenceType),
                ("source", QuestionnaireResponseSourceReferenceType),
            ):
                if key in updates:
                    ref = updates.pop(key)
                    t, i = _optional_ref(ref, enum_cls, key)
                    setattr(qr, f"{key}_type", t)
                    setattr(qr, f"{key}_id", i)
                    if ref is None:
                        updates.setdefault(f"{key}_display", None)

            for field_name, value in updates.items():
                setattr(qr, field_name, value)
            if updated_by is not None:
                qr.updated_by = updated_by

            # Child lists (basedOn, partOf and the whole item/answer tree): a list that is present REPLACES the stored one.
            replaced = [f for f in CHILD_FIELDS if f in payload.model_fields_set]
            for f in replaced:
                getattr(qr, CHILD_FIELDS[f]).clear()
            if replaced:
                await session.flush()
                _add_children(session, qr, _OnlyFields(payload, replaced), qr.org_id)

            await session.commit()
            stmt = _with_relationships(select(QuestionnaireResponseModel).where(QuestionnaireResponseModel.id == qr.id))
            return (await session.execute(stmt)).scalars().one()

    async def delete(self, questionnaire_response_id: int) -> bool:
        async with self.session_factory() as session:
            stmt = select(QuestionnaireResponseModel).where(
                QuestionnaireResponseModel.questionnaire_response_id == questionnaire_response_id)
            qr = (await session.execute(stmt)).scalars().first()
            if not qr:
                return False
            await session.delete(qr)
            await session.commit()
            return True
