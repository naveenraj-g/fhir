from dataclasses import dataclass, field
from datetime import timezone
from enum import Enum
from typing import List, Optional, Tuple

from fastapi import HTTPException, status as http_status
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker  # noqa: F401
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.search_params import (
    enum_token_values,
    instant_clause,
    parse_date_param,
    parse_reference_param,
    period_date_clause,
    reference_clause,
    split_or,
    token_clause,
)
from app.models.enums import EncounterReferenceType
from app.models.flag.enums import FlagAuthorType, FlagStatus, FlagSubjectType
from app.models.flag.flag import FlagCategory, FlagIdentifier, FlagModel
from app.schemas.flag import FlagCreateSchema, FlagPatchSchema


@dataclass
class FlagSearch:
    """
    FHIR R4 Flag search parameters (https://www.hl7.org/fhir/R4/flag.html#search):
    author, date, encounter, identifier, patient, subject — plus _id, _lastUpdated and the
    convenience filters status / category / code.
    """

    id: Optional[str] = None                      # _id
    identifier: Optional[str] = None
    flag_status: Optional[str] = None
    category: Optional[str] = None
    code: Optional[str] = None
    subject: Optional[str] = None
    patient: Optional[str] = None
    encounter: Optional[str] = None
    author: Optional[str] = None
    date: List[str] = field(default_factory=list)
    last_updated: List[str] = field(default_factory=list)   # _lastUpdated


class _PatientOnly(str, Enum):
    Patient = "Patient"


# Child-list fields shared by create and patch: payload field -> FlagModel relationship name.
CHILD_FIELDS = {"identifier": "identifiers", "category": "categories"}


class _OnlyFields:
    """View of a payload exposing only the listed fields; every other attribute reads as None."""

    def __init__(self, payload, fields):
        self._payload = payload
        self._fields = set(fields)

    def __getattr__(self, name):
        return getattr(self._payload, name) if name in self._fields else None


def _with_relationships(stmt):
    return stmt.options(
        selectinload(FlagModel.identifiers),
        selectinload(FlagModel.categories),
    )


def _unprocessable(detail: str) -> HTTPException:
    return HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


def _parse_ref(ref: str, enum_cls, field_name: str):
    """Parse 'Type/id' and check the type against `enum_cls` (format check only — existence is never verified)."""
    parts = ref.split("/", 1)
    if len(parts) != 2 or not parts[0]:
        raise _unprocessable(f"Invalid reference format '{ref}' for {field_name}. Expected 'ResourceType/id'.")
    try:
        ref_id = int(parts[1])
    except ValueError:
        raise _unprocessable(f"Invalid reference id in '{ref}' for {field_name}. Id must be an integer.")
    try:
        return enum_cls(parts[0]), ref_id
    except ValueError:
        raise _unprocessable(
            f"Invalid reference type '{parts[0]}' for {field_name}. Allowed: {[e.value for e in enum_cls]}."
        )


def _optional_ref(ref: Optional[str], enum_cls, field_name: str):
    return _parse_ref(ref, enum_cls, field_name) if ref else (None, None)


def _period_runs_backwards(start, end) -> bool:
    """True when end < start. Naive datetimes (e.g. read back from SQLite) are treated as UTC so naive and aware values compare safely."""
    if not (start and end):
        return False
    as_utc = lambda d: d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d  # noqa: E731
    return as_utc(end) < as_utc(start)


def _add_children(session, flag, payload, org_id) -> None:
    """Create the child rows for every child list present on `payload` (None / missing = none)."""
    for i in payload.identifier or []:
        session.add(FlagIdentifier(
            flag=flag, org_id=org_id, use=i.use, type_system=i.type_system, type_code=i.type_code,
            type_display=i.type_display, type_text=i.type_text, system=i.system, value=i.value,
            period_start=i.period_start, period_end=i.period_end, assigner=i.assigner))
    for c in payload.category or []:
        session.add(FlagCategory(
            flag=flag, org_id=org_id, coding_system=c.coding_system, coding_code=c.coding_code,
            coding_display=c.coding_display, text=c.text))


class FlagRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    # ── Read ──────────────────────────────────────────────────────────────────

    async def get_by_flag_id(self, flag_id: int) -> Optional[FlagModel]:
        async with self.session_factory() as session:
            stmt = _with_relationships(select(FlagModel).where(FlagModel.flag_id == flag_id))
            return (await session.execute(stmt)).scalars().first()

    def _apply_list_filters(self, stmt, user_id, org_id, search: Optional[FlagSearch] = None):
        """user_id/org_id are optional tenant filters; `search` carries FHIR R4 search params."""
        if user_id:
            stmt = stmt.where(FlagModel.user_id == user_id)
        if org_id:
            stmt = stmt.where(FlagModel.org_id == org_id)
        if search is None:
            return stmt
        M = FlagModel

        if search.id:
            ids = []
            for v in split_or(search.id):
                try:
                    ids.append(int(v))
                except ValueError:
                    raise _unprocessable(f"Invalid _id '{v}'. Must be an integer.")
            stmt = stmt.where(M.flag_id.in_(ids))

        clause = token_clause(FlagIdentifier.system, FlagIdentifier.value, search.identifier)
        if clause is not None:
            stmt = stmt.where(select(FlagIdentifier.id).where(FlagIdentifier.flag_id == M.id, clause).exists())

        statuses = enum_token_values(search.flag_status, FlagStatus, "status")
        if statuses:
            stmt = stmt.where(M.status.in_(statuses))

        clause = token_clause(FlagCategory.coding_system, FlagCategory.coding_code, search.category)
        if clause is not None:
            stmt = stmt.where(select(FlagCategory.id).where(FlagCategory.flag_id == M.id, clause).exists())

        clause = token_clause(M.code_system, M.code_code, search.code)
        if clause is not None:
            stmt = stmt.where(clause)

        for value, enum_cls, name in (
            (search.patient, _PatientOnly, "patient"),
            (search.subject, FlagSubjectType, "subject"),
        ):
            if value:
                stmt = stmt.where(reference_clause(
                    M.subject_type, M.subject_id, parse_reference_param(value, enum_cls, name)))

        if search.encounter:
            stmt = stmt.where(reference_clause(
                M.encounter_type, M.encounter_id,
                parse_reference_param(search.encounter, EncounterReferenceType, "encounter")))

        if search.author:
            stmt = stmt.where(reference_clause(
                M.author_type, M.author_id, parse_reference_param(search.author, FlagAuthorType, "author")))

        # date — Flag.period (an open end means "still active")
        for value in search.date or []:
            prefix, s_lo, s_hi = parse_date_param(value, "date")
            stmt = stmt.where(period_date_clause(M.period_start, M.period_end, prefix, s_lo, s_hi))

        for value in search.last_updated or []:
            prefix, s_lo, s_hi = parse_date_param(value, "_lastUpdated")
            stmt = stmt.where(instant_clause(func.coalesce(M.updated_at, M.created_at), prefix, s_lo, s_hi))
        return stmt

    async def _search(
        self, user_id, org_id, search: Optional[FlagSearch], limit: int, offset: int
    ) -> Tuple[List[FlagModel], int]:
        async with self.session_factory() as session:
            base = self._apply_list_filters(_with_relationships(select(FlagModel)), user_id, org_id, search)
            count_base = self._apply_list_filters(select(func.count()).select_from(FlagModel), user_id, org_id, search)
            total = (await session.execute(count_base)).scalar_one()
            rows = list((await session.execute(
                base.order_by(FlagModel.period_start.desc().nulls_last(), FlagModel.id.desc())
                .offset(offset).limit(limit)
            )).scalars().all())
        return rows, total

    async def get_me(
        self, user_id: str, org_id: str, search: Optional[FlagSearch] = None, limit: int = 50, offset: int = 0
    ) -> Tuple[List[FlagModel], int]:
        return await self._search(user_id, org_id, search, limit, offset)

    async def list(
        self, user_id: Optional[str] = None, org_id: Optional[str] = None,
        search: Optional[FlagSearch] = None, limit: int = 50, offset: int = 0,
    ) -> Tuple[List[FlagModel], int]:
        return await self._search(user_id, org_id, search, limit, offset)

    # ── Create ────────────────────────────────────────────────────────────────

    async def create(
        self, payload: FlagCreateSchema, user_id: Optional[str], org_id: Optional[str], created_by: Optional[str]
    ) -> FlagModel:
        subject_type, subject_id = _parse_ref(payload.subject, FlagSubjectType, "subject")
        author_type, author_id = _optional_ref(payload.author, FlagAuthorType, "author")

        async with self.session_factory() as session:
            encounter_public_id = None
            if payload.encounter_id is not None:
                encounter_public_id = payload.encounter_id

            flag = FlagModel(
                user_id=user_id, org_id=org_id, created_by=created_by, status=payload.status,
                code_system=payload.code_system, code_code=payload.code_code,
                code_display=payload.code_display, code_text=payload.code_text,
                subject_type=subject_type, subject_id=subject_id, subject_display=payload.subject_display,
                period_start=payload.period_start, period_end=payload.period_end,
                encounter_type=EncounterReferenceType.Encounter if encounter_public_id else None,
                encounter_id=encounter_public_id, encounter_display=payload.encounter_display,
                author_type=author_type, author_id=author_id, author_display=payload.author_display,
            )
            session.add(flag)
            _add_children(session, flag, payload, org_id)
            await session.commit()

            stmt = _with_relationships(select(FlagModel).where(FlagModel.id == flag.id))
            return (await session.execute(stmt)).scalars().one()

    # ── Patch ─────────────────────────────────────────────────────────────────

    async def patch(self, flag_id: int, payload: FlagPatchSchema, updated_by: Optional[str]) -> Optional[FlagModel]:
        async with self.session_factory() as session:
            stmt = _with_relationships(select(FlagModel).where(FlagModel.flag_id == flag_id))
            flag = (await session.execute(stmt)).scalars().first()
            if not flag:
                return None

            updates = payload.model_dump(exclude_unset=True, exclude=set(CHILD_FIELDS))

            if "subject" in updates:
                flag.subject_type, flag.subject_id = _parse_ref(updates.pop("subject"), FlagSubjectType, "subject")
            if "encounter_id" in updates:
                public_enc = updates.pop("encounter_id")
                if public_enc is None:
                    flag.encounter_id, flag.encounter_type = None, None
                    updates.setdefault("encounter_display", None)
                else:
                    flag.encounter_id = public_enc
                    flag.encounter_type = EncounterReferenceType.Encounter
            if "author" in updates:
                ref = updates.pop("author")
                flag.author_type, flag.author_id = _optional_ref(ref, FlagAuthorType, "author")
                if ref is None:
                    updates.setdefault("author_display", None)

            for field_name, value in updates.items():
                setattr(flag, field_name, value)
            flag.updated_by = updated_by

            # Child lists: a list that is present REPLACES the stored one ([] / null clears it).
            replaced = [f for f in CHILD_FIELDS if f in payload.model_fields_set]
            for f in replaced:
                getattr(flag, CHILD_FIELDS[f]).clear()
            if replaced:
                await session.flush()
                _add_children(session, flag, _OnlyFields(payload, replaced), flag.org_id)

            if _period_runs_backwards(flag.period_start, flag.period_end):
                raise _unprocessable("period_end must not be before period_start.")

            await session.commit()
            stmt = _with_relationships(select(FlagModel).where(FlagModel.id == flag.id))
            return (await session.execute(stmt)).scalars().one()

    # ── Delete ────────────────────────────────────────────────────────────────

    async def delete(self, flag_id: int) -> None:
        async with self.session_factory() as session:
            flag = (await session.execute(select(FlagModel).where(FlagModel.flag_id == flag_id))).scalars().first()
            if flag:
                await session.delete(flag)
                await session.commit()
