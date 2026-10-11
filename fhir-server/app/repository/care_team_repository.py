from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple

from fastapi import HTTPException, status as http_status
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
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
from app.models.care_team.care_team import (
    CareTeamCategory,
    CareTeamIdentifier,
    CareTeamManagingOrganization,
    CareTeamModel,
    CareTeamNote,
    CareTeamParticipant,
    CareTeamParticipantRole,
    CareTeamReasonCode,
    CareTeamReasonReference,
    CareTeamTelecom,
)
from app.models.care_team.enums import CareTeamParticipantMemberType, CareTeamReasonReferenceType, CareTeamStatus
from app.models.enums import EncounterReferenceType, OrganizationReferenceType, SubjectReferenceType
from app.schemas.care_team import CareTeamCreateSchema, CareTeamPatchSchema


@dataclass
class CareTeamSearch:
    """FHIR R4 CareTeam search parameters (https://www.hl7.org/fhir/R4/careteam.html#search)."""

    id: Optional[str] = None                      # _id
    identifier: Optional[str] = None
    ct_status: Optional[str] = None
    category: Optional[str] = None
    subject: Optional[str] = None
    patient: Optional[str] = None
    encounter: Optional[str] = None
    participant: Optional[str] = None
    date: List[str] = field(default_factory=list)
    last_updated: List[str] = field(default_factory=list)   # _lastUpdated


class _PatientOnly(str, Enum):
    Patient = "Patient"


# payload list field -> CareTeamModel relationship name (shared by create and patch)
CHILD_FIELDS = {
    "identifier": "identifiers",
    "category": "categories",
    "participant": "participants",
    "reason_code": "reason_codes",
    "reason_reference": "reason_references",
    "managing_organization": "managing_organizations",
    "telecom": "telecoms",
    "note": "notes",
}


class _OnlyFields:
    """View of a payload exposing only the listed fields; every other attribute reads as None."""

    def __init__(self, payload, fields):
        self._payload = payload
        self._fields = set(fields)

    def __getattr__(self, name):
        return getattr(self._payload, name) if name in self._fields else None


def _with_relationships(stmt):
    return stmt.options(
        selectinload(CareTeamModel.identifiers),
        selectinload(CareTeamModel.categories),
        selectinload(CareTeamModel.participants).selectinload(CareTeamParticipant.roles),
        selectinload(CareTeamModel.reason_codes),
        selectinload(CareTeamModel.reason_references),
        selectinload(CareTeamModel.managing_organizations),
        selectinload(CareTeamModel.telecoms),
        selectinload(CareTeamModel.notes),
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


def _parse_open_ref(ref: Optional[str], field_name: str):
    """Open reference (any resource type): 'Type/id' -> (type string, id)."""
    if not ref:
        return None, None
    parts = ref.split("/", 1)
    if len(parts) != 2 or not parts[0]:
        raise _unprocessable(f"Invalid reference format '{ref}' for {field_name}. Expected 'ResourceType/id'.")
    try:
        return parts[0], int(parts[1])
    except ValueError:
        raise _unprocessable(f"Invalid reference id in '{ref}' for {field_name}. Id must be an integer.")


def _add_children(session, ct, payload, org_id) -> None:
    """Create the child rows for every child list present on `payload` (None / missing = none)."""
    for i in payload.identifier or []:
        session.add(CareTeamIdentifier(
            care_team=ct, org_id=org_id, use=i.use, type_system=i.type_system, type_code=i.type_code,
            type_display=i.type_display, type_text=i.type_text, system=i.system, value=i.value,
            period_start=i.period_start, period_end=i.period_end, assigner=i.assigner))
    for c in payload.category or []:
        session.add(CareTeamCategory(
            care_team=ct, org_id=org_id, coding_system=c.coding_system, coding_code=c.coding_code,
            coding_display=c.coding_display, text=c.text))
    for p in payload.participant or []:
        m_type, m_id = _optional_ref(p.member, CareTeamParticipantMemberType, "participant.member")
        o_type, o_id = _optional_ref(p.on_behalf_of, OrganizationReferenceType, "participant.on_behalf_of")
        row = CareTeamParticipant(
            care_team=ct, org_id=org_id, member_type=m_type, member_id=m_id, member_display=p.member_display,
            on_behalf_of_type=o_type, on_behalf_of_id=o_id, on_behalf_of_display=p.on_behalf_of_display,
            period_start=p.period_start, period_end=p.period_end)
        session.add(row)
        for r in p.role or []:
            session.add(CareTeamParticipantRole(
                participant=row, org_id=org_id, coding_system=r.coding_system, coding_code=r.coding_code,
                coding_display=r.coding_display, text=r.text))
    for c in payload.reason_code or []:
        session.add(CareTeamReasonCode(
            care_team=ct, org_id=org_id, coding_system=c.coding_system, coding_code=c.coding_code,
            coding_display=c.coding_display, text=c.text))
    for r in payload.reason_reference or []:
        t, i = _parse_ref(r.reference, CareTeamReasonReferenceType, "reason_reference")
        session.add(CareTeamReasonReference(
            care_team=ct, org_id=org_id, reference_type=t, reference_id=i, reference_display=r.reference_display))
    for r in payload.managing_organization or []:
        t, i = _parse_ref(r.reference, OrganizationReferenceType, "managing_organization")
        session.add(CareTeamManagingOrganization(
            care_team=ct, org_id=org_id, reference_type=t, reference_id=i, reference_display=r.reference_display))
    for t in payload.telecom or []:
        session.add(CareTeamTelecom(
            care_team=ct, org_id=org_id, system=t.system, value=t.value, use=t.use, rank=t.rank,
            period_start=t.period_start, period_end=t.period_end))
    for n in payload.note or []:
        a_type, a_id = _parse_open_ref(n.author_reference, "note.author_reference")
        session.add(CareTeamNote(
            care_team=ct, org_id=org_id, text=n.text, time=n.time, author_string=n.author_string,
            author_reference_type=a_type, author_reference_id=a_id,
            author_reference_display=n.author_reference_display))


class CareTeamRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    # ── Read ──────────────────────────────────────────────────────────────────

    async def get_by_care_team_id(self, care_team_id: int) -> Optional[CareTeamModel]:
        async with self.session_factory() as session:
            stmt = _with_relationships(select(CareTeamModel).where(CareTeamModel.care_team_id == care_team_id))
            return (await session.execute(stmt)).scalars().first()

    def _apply_list_filters(self, stmt, user_id, org_id, search: Optional[CareTeamSearch] = None):
        """user_id/org_id are tenant filters; `search` carries the FHIR R4 search parameters."""
        if user_id:
            stmt = stmt.where(CareTeamModel.user_id == user_id)
        if org_id:
            stmt = stmt.where(CareTeamModel.org_id == org_id)
        if search is None:
            return stmt
        M = CareTeamModel

        if search.id:
            ids = []
            for v in split_or(search.id):
                try:
                    ids.append(int(v))
                except ValueError:
                    raise _unprocessable(f"Invalid _id '{v}'. Must be an integer.")
            stmt = stmt.where(M.care_team_id.in_(ids))

        clause = token_clause(CareTeamIdentifier.system, CareTeamIdentifier.value, search.identifier)
        if clause is not None:
            stmt = stmt.where(select(CareTeamIdentifier.id).where(CareTeamIdentifier.care_team_id == M.id, clause).exists())

        statuses = enum_token_values(search.ct_status, CareTeamStatus, "status")
        if statuses:
            stmt = stmt.where(M.status.in_(statuses))

        clause = token_clause(CareTeamCategory.coding_system, CareTeamCategory.coding_code, search.category)
        if clause is not None:
            stmt = stmt.where(select(CareTeamCategory.id).where(CareTeamCategory.care_team_id == M.id, clause).exists())

        for value, enum_cls, name in (
            (search.patient, _PatientOnly, "patient"),
            (search.subject, SubjectReferenceType, "subject"),
        ):
            if value:
                stmt = stmt.where(reference_clause(
                    M.subject_type, M.subject_id, parse_reference_param(value, enum_cls, name)))

        if search.encounter:
            stmt = stmt.where(reference_clause(
                M.encounter_type, M.encounter_id,
                parse_reference_param(search.encounter, EncounterReferenceType, "encounter")))

        if search.participant:
            P = CareTeamParticipant
            clause = reference_clause(
                P.member_type, P.member_id,
                parse_reference_param(search.participant, CareTeamParticipantMemberType, "participant"))
            stmt = stmt.where(select(P.id).where(P.care_team_id == M.id, clause).exists())

        # date — CareTeam.period
        for value in search.date or []:
            prefix, s_lo, s_hi = parse_date_param(value, "date")
            stmt = stmt.where(period_date_clause(M.period_start, M.period_end, prefix, s_lo, s_hi))
        for value in search.last_updated or []:
            prefix, s_lo, s_hi = parse_date_param(value, "_lastUpdated")
            stmt = stmt.where(instant_clause(func.coalesce(M.updated_at, M.created_at), prefix, s_lo, s_hi))
        return stmt

    async def _search(
        self, user_id, org_id, search: Optional[CareTeamSearch], limit: int, offset: int
    ) -> Tuple[List[CareTeamModel], int]:
        async with self.session_factory() as session:
            base = self._apply_list_filters(_with_relationships(select(CareTeamModel)), user_id, org_id, search)
            count_base = self._apply_list_filters(
                select(func.count()).select_from(CareTeamModel), user_id, org_id, search)
            total = (await session.execute(count_base)).scalar_one()
            rows = list((await session.execute(
                base.order_by(
                    func.coalesce(CareTeamModel.period_start, CareTeamModel.created_at).desc().nulls_last(),
                    CareTeamModel.id.desc(),
                ).offset(offset).limit(limit)
            )).scalars().all())
        return rows, total

    async def get_me(
        self, user_id: str, org_id: str, search: Optional[CareTeamSearch] = None, limit: int = 50, offset: int = 0
    ) -> Tuple[List[CareTeamModel], int]:
        return await self._search(user_id, org_id, search, limit, offset)

    async def list(
        self, user_id: Optional[str] = None, org_id: Optional[str] = None,
        search: Optional[CareTeamSearch] = None, limit: int = 50, offset: int = 0,
    ) -> Tuple[List[CareTeamModel], int]:
        return await self._search(user_id, org_id, search, limit, offset)

    # ── Create ────────────────────────────────────────────────────────────────

    async def create(
        self, payload: CareTeamCreateSchema, user_id: Optional[str], org_id: Optional[str], created_by: Optional[str]
    ) -> CareTeamModel:
        s_type, s_id = _optional_ref(payload.subject, SubjectReferenceType, "subject")
        e_type, e_id = _optional_ref(payload.encounter, EncounterReferenceType, "encounter")
        async with self.session_factory() as session:
            ct = CareTeamModel(
                user_id=user_id, org_id=org_id, created_by=created_by, status=payload.status, name=payload.name,
                subject_type=s_type, subject_id=s_id, subject_display=payload.subject_display,
                encounter_type=e_type, encounter_id=e_id, encounter_display=payload.encounter_display,
                period_start=payload.period_start, period_end=payload.period_end,
            )
            session.add(ct)
            _add_children(session, ct, payload, org_id)
            await session.commit()

            stmt = _with_relationships(select(CareTeamModel).where(CareTeamModel.id == ct.id))
            return (await session.execute(stmt)).scalars().one()

    # ── Patch ─────────────────────────────────────────────────────────────────

    async def patch(
        self, care_team_id: int, payload: CareTeamPatchSchema, updated_by: Optional[str]
    ) -> Optional[CareTeamModel]:
        async with self.session_factory() as session:
            stmt = _with_relationships(select(CareTeamModel).where(CareTeamModel.care_team_id == care_team_id))
            ct = (await session.execute(stmt)).scalars().first()
            if not ct:
                return None

            updates = payload.model_dump(exclude_unset=True, exclude=set(CHILD_FIELDS))

            # references (format + allowed type only); null clears
            for key, enum_cls in (("subject", SubjectReferenceType), ("encounter", EncounterReferenceType)):
                if key in updates:
                    ref = updates.pop(key)
                    t, i = _optional_ref(ref, enum_cls, key)
                    setattr(ct, f"{key}_type", t)
                    setattr(ct, f"{key}_id", i)
                    if ref is None and f"{key}_display" not in updates:
                        setattr(ct, f"{key}_display", None)
            for name, value in updates.items():
                setattr(ct, name, value)
            ct.updated_by = updated_by

            # Child lists: a list that is present REPLACES the stored one ([] / null clears it).
            replaced = [f for f in CHILD_FIELDS if f in payload.model_fields_set]
            for f in replaced:
                getattr(ct, CHILD_FIELDS[f]).clear()
            if replaced:
                await session.flush()
                _add_children(session, ct, _OnlyFields(payload, replaced), ct.org_id)

            await session.commit()
            stmt = _with_relationships(select(CareTeamModel).where(CareTeamModel.id == ct.id))
            return (await session.execute(stmt)).scalars().one()

    # ── Delete ────────────────────────────────────────────────────────────────

    async def delete(self, care_team_id: int) -> None:
        async with self.session_factory() as session:
            ct = (await session.execute(
                select(CareTeamModel).where(CareTeamModel.care_team_id == care_team_id))).scalars().first()
            if ct:
                await session.delete(ct)
                await session.commit()
