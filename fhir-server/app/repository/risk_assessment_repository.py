from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Tuple

from fastapi import HTTPException, status as http_status
from sqlalchemy import and_, func, not_, or_
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker  # noqa: F401
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.search_params import (
    enum_token_values,
    instant_clause,
    parse_date_param,
    parse_number_param,
    parse_reference_param,
    period_date_clause,
    reference_clause,
    split_or,
    token_clause,
)
from app.models.enums import EncounterReferenceType
from app.models.risk_assessment.enums import (
    RiskAssessmentConditionReferenceType,
    RiskAssessmentNoteAuthorReferenceType,
    RiskAssessmentPerformerType,
    RiskAssessmentReasonReferenceType,
    RiskAssessmentStatus,
    RiskAssessmentSubjectType,
)
from app.models.risk_assessment.risk_assessment import (
    RiskAssessmentBasis,
    RiskAssessmentIdentifier,
    RiskAssessmentModel,
    RiskAssessmentNote,
    RiskAssessmentPrediction,
    RiskAssessmentReasonCode,
    RiskAssessmentReasonReference,
)
from app.schemas.risk_assessment import RiskAssessmentCreateSchema, RiskAssessmentPatchSchema


@dataclass
class RiskAssessmentSearch:
    """FHIR R4 RiskAssessment search parameters (https://www.hl7.org/fhir/R4/riskassessment.html#search)."""

    id: Optional[str] = None                      # _id
    identifier: Optional[str] = None
    ra_status: Optional[str] = None
    method: Optional[str] = None
    subject: Optional[str] = None
    patient: Optional[str] = None
    encounter: Optional[str] = None
    condition: Optional[str] = None
    performer: Optional[str] = None
    date: List[str] = field(default_factory=list)
    probability: List[str] = field(default_factory=list)
    risk: Optional[str] = None
    last_updated: List[str] = field(default_factory=list)   # _lastUpdated


class _PatientOnly(str, Enum):
    Patient = "Patient"


def _with_relationships(stmt):
    return stmt.options(
        selectinload(RiskAssessmentModel.identifiers),
        selectinload(RiskAssessmentModel.reason_codes),
        selectinload(RiskAssessmentModel.reason_references),
        selectinload(RiskAssessmentModel.basis),
        selectinload(RiskAssessmentModel.predictions),
        selectinload(RiskAssessmentModel.notes),
    )


def _unprocessable(detail: str) -> HTTPException:
    return HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


def _parse_ref(ref: str, enum_cls, field_name: str):
    """Parse 'Type/id' (format check only). enum_cls=None means Reference(Any): any type string."""
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


# Single-reference fields on the main row: (payload key, enum or None for Reference(Any), column prefix)
_REF_FIELDS = (
    ("based_on", None, "based_on"),
    ("parent", None, "parent"),
    ("condition", RiskAssessmentConditionReferenceType, "condition"),
    ("performer", RiskAssessmentPerformerType, "performer"),
)


def _probability_clause(prefix: str, v: float):
    """Match prediction.probability (decimal, or the Range bounds) against a number search value."""
    P = RiskAssessmentPrediction
    dec = P.probability_decimal
    low = func.coalesce(dec, P.probability_range_low_value)
    high = func.coalesce(dec, P.probability_range_high_value)
    equals = or_(dec == v, and_(P.probability_range_low_value <= v, P.probability_range_high_value >= v))
    if prefix in ("eq", "ap"):
        return equals
    if prefix == "ne":
        # coalesce: a NULL comparison (no range / no decimal) must count as "not equal", not drop the row.
        has_probability = or_(dec.isnot(None), P.probability_range_low_value.isnot(None),
                              P.probability_range_high_value.isnot(None))
        return and_(has_probability, not_(func.coalesce(equals, False)))
    if prefix in ("gt", "sa"):
        return high > v
    if prefix == "ge":
        return high >= v
    if prefix in ("lt", "eb"):
        return low < v
    return low <= v  # le



# Child-list fields shared by create and patch: payload field -> RiskAssessmentModel relationship name.
CHILD_FIELDS = {
    "identifier": "identifiers",
    "reason_code": "reason_codes",
    "reason_reference": "reason_references",
    "basis": "basis",
    "prediction": "predictions",
    "note": "notes",
}


class _OnlyFields:
    """View of a payload exposing only the listed fields; every other attribute reads as None."""

    def __init__(self, payload, fields):
        self._payload = payload
        self._fields = set(fields)

    def __getattr__(self, name):
        return getattr(self._payload, name) if name in self._fields else None


def _add_children(session, ra, payload, org_id) -> None:
    """Create the child rows for every child list present on `payload` (None / missing = none)."""
    for i in payload.identifier or []:
        session.add(RiskAssessmentIdentifier(
            risk_assessment=ra, org_id=org_id, use=i.use, type_system=i.type_system,
            type_code=i.type_code, type_display=i.type_display, type_text=i.type_text,
            system=i.system, value=i.value, period_start=i.period_start,
            period_end=i.period_end, assigner=i.assigner))
    for r in payload.reason_code or []:
        session.add(RiskAssessmentReasonCode(
            risk_assessment=ra, org_id=org_id, coding_system=r.coding_system,
            coding_code=r.coding_code, coding_display=r.coding_display, text=r.text))
    for r in payload.reason_reference or []:
        t, i = _parse_ref(r.reference, RiskAssessmentReasonReferenceType, "reason_reference")
        session.add(RiskAssessmentReasonReference(
            risk_assessment=ra, org_id=org_id, reference_type=t, reference_id=i,
            reference_display=r.reference_display))
    for b in payload.basis or []:
        t, i = _parse_ref(b.reference, None, "basis")
        session.add(RiskAssessmentBasis(
            risk_assessment=ra, org_id=org_id, reference_type=t, reference_id=i,
            reference_display=b.reference_display))
    for p in payload.prediction or []:
        session.add(RiskAssessmentPrediction(risk_assessment=ra, org_id=org_id, **p.model_dump()))
    for n in payload.note or []:
        t, i = _optional_ref(n.author_reference, RiskAssessmentNoteAuthorReferenceType, "note.author_reference")
        session.add(RiskAssessmentNote(
            risk_assessment=ra, org_id=org_id, text=n.text, time=n.time, author_string=n.author_string,
            author_reference_type=t, author_reference_id=i,
            author_reference_display=n.author_reference_display))

class RiskAssessmentRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    # ── Read ──────────────────────────────────────────────────────────────────

    async def get_by_risk_assessment_id(self, risk_assessment_id: int) -> Optional[RiskAssessmentModel]:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(RiskAssessmentModel).where(RiskAssessmentModel.risk_assessment_id == risk_assessment_id)
            )
            return (await session.execute(stmt)).scalars().first()

    def _apply_list_filters(self, stmt, user_id, org_id, search: Optional[RiskAssessmentSearch] = None):
        """user_id/org_id are optional tenant filters; `search` carries FHIR R4 search params."""
        if user_id:
            stmt = stmt.where(RiskAssessmentModel.user_id == user_id)
        if org_id:
            stmt = stmt.where(RiskAssessmentModel.org_id == org_id)
        if search is None:
            return stmt
        M = RiskAssessmentModel
        P = RiskAssessmentPrediction

        if search.id:
            ids = []
            for v in split_or(search.id):
                try:
                    ids.append(int(v))
                except ValueError:
                    raise _unprocessable(f"Invalid _id '{v}'. Must be an integer.")
            stmt = stmt.where(M.risk_assessment_id.in_(ids))

        clause = token_clause(RiskAssessmentIdentifier.system, RiskAssessmentIdentifier.value, search.identifier)
        if clause is not None:
            stmt = stmt.where(select(RiskAssessmentIdentifier.id).where(
                RiskAssessmentIdentifier.risk_assessment_id == M.id, clause).exists())

        statuses = enum_token_values(search.ra_status, RiskAssessmentStatus, "status")
        if statuses:
            stmt = stmt.where(M.status.in_(statuses))

        clause = token_clause(M.method_system, M.method_code, search.method)
        if clause is not None:
            stmt = stmt.where(clause)

        for value, enum_cls, name in (
            (search.patient, _PatientOnly, "patient"),
            (search.subject, RiskAssessmentSubjectType, "subject"),
        ):
            if value:
                stmt = stmt.where(reference_clause(
                    M.subject_type, M.subject_id, parse_reference_param(value, enum_cls, name)))

        if search.encounter:
            stmt = stmt.where(reference_clause(
                M.encounter_type, M.encounter_id,
                parse_reference_param(search.encounter, EncounterReferenceType, "encounter")))

        if search.condition:
            stmt = stmt.where(reference_clause(
                M.condition_type, M.condition_id,
                parse_reference_param(search.condition, RiskAssessmentConditionReferenceType, "condition")))
        if search.performer:
            stmt = stmt.where(reference_clause(
                M.performer_type, M.performer_id,
                parse_reference_param(search.performer, RiskAssessmentPerformerType, "performer")))

        # date — occurrence[x]: dateTime or Period
        lo = func.coalesce(M.occurrence_datetime, M.occurrence_period_start)
        hi = func.coalesce(M.occurrence_datetime, M.occurrence_period_end)
        for value in search.date or []:
            prefix, s_lo, s_hi = parse_date_param(value, "date")
            stmt = stmt.where(period_date_clause(lo, hi, prefix, s_lo, s_hi))

        for value in search.last_updated or []:
            prefix, s_lo, s_hi = parse_date_param(value, "_lastUpdated")
            stmt = stmt.where(instant_clause(func.coalesce(M.updated_at, M.created_at), prefix, s_lo, s_hi))

        # probability (number, AND across repeated values) — any prediction must satisfy each
        for value in search.probability or []:
            prefix, number = parse_number_param(value, "probability")
            stmt = stmt.where(select(P.id).where(
                P.risk_assessment_id == M.id, _probability_clause(prefix, number)).exists())

        # risk — token on prediction.qualitativeRisk
        clause = token_clause(P.qualitative_risk_system, P.qualitative_risk_code, search.risk)
        if clause is not None:
            stmt = stmt.where(select(P.id).where(P.risk_assessment_id == M.id, clause).exists())
        return stmt

    async def _search(
        self, user_id, org_id, search: Optional[RiskAssessmentSearch], limit: int, offset: int
    ) -> Tuple[List[RiskAssessmentModel], int]:
        async with self.session_factory() as session:
            base = self._apply_list_filters(_with_relationships(select(RiskAssessmentModel)), user_id, org_id, search)
            count_base = self._apply_list_filters(
                select(func.count()).select_from(RiskAssessmentModel), user_id, org_id, search)
            total = (await session.execute(count_base)).scalar_one()
            when = func.coalesce(RiskAssessmentModel.occurrence_datetime, RiskAssessmentModel.occurrence_period_start)
            rows = list((await session.execute(
                base.order_by(when.desc().nulls_last(), RiskAssessmentModel.id.desc()).offset(offset).limit(limit)
            )).scalars().all())
        return rows, total

    async def get_me(
        self, user_id: str, org_id: str, search: Optional[RiskAssessmentSearch] = None,
        limit: int = 50, offset: int = 0,
    ) -> Tuple[List[RiskAssessmentModel], int]:
        return await self._search(user_id, org_id, search, limit, offset)

    async def list(
        self, user_id: Optional[str] = None, org_id: Optional[str] = None,
        search: Optional[RiskAssessmentSearch] = None, limit: int = 50, offset: int = 0,
    ) -> Tuple[List[RiskAssessmentModel], int]:
        return await self._search(user_id, org_id, search, limit, offset)

    # ── Create ────────────────────────────────────────────────────────────────

    async def create(
        self,
        payload: RiskAssessmentCreateSchema,
        user_id: Optional[str],
        org_id: Optional[str],
        created_by: Optional[str],
    ) -> RiskAssessmentModel:
        subject_type, subject_id = _parse_ref(payload.subject, RiskAssessmentSubjectType, "subject")
        refs = {}
        for key, enum_cls, prefix in _REF_FIELDS:
            t, i = _optional_ref(getattr(payload, key), enum_cls, key)
            refs[f"{prefix}_type"], refs[f"{prefix}_id"] = t, i
            refs[f"{prefix}_display"] = getattr(payload, f"{key}_display")

        async with self.session_factory() as session:
            encounter_public_id = None
            if payload.encounter_id is not None:
                encounter_public_id = payload.encounter_id

            ra = RiskAssessmentModel(
                user_id=user_id, org_id=org_id, created_by=created_by,
                status=payload.status,
                method_system=payload.method_system, method_code=payload.method_code,
                method_display=payload.method_display, method_text=payload.method_text,
                code_system=payload.code_system, code_code=payload.code_code,
                code_display=payload.code_display, code_text=payload.code_text,
                subject_type=subject_type, subject_id=subject_id, subject_display=payload.subject_display,
                encounter_type=EncounterReferenceType.Encounter if encounter_public_id else None,
                encounter_id=encounter_public_id, encounter_display=payload.encounter_display,
                occurrence_datetime=payload.occurrence_datetime,
                occurrence_period_start=payload.occurrence_period_start,
                occurrence_period_end=payload.occurrence_period_end,
                mitigation=payload.mitigation,
                **refs,
            )
            session.add(ra)

            _add_children(session, ra, payload, org_id)

            await session.commit()
            stmt = _with_relationships(select(RiskAssessmentModel).where(RiskAssessmentModel.id == ra.id))
            return (await session.execute(stmt)).scalars().one()

    # ── Patch ─────────────────────────────────────────────────────────────────

    async def patch(
        self, risk_assessment_id: int, payload: RiskAssessmentPatchSchema, updated_by: Optional[str]
    ) -> Optional[RiskAssessmentModel]:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(RiskAssessmentModel).where(RiskAssessmentModel.risk_assessment_id == risk_assessment_id))
            ra = (await session.execute(stmt)).scalars().first()
            if not ra:
                return None

            updates = payload.model_dump(exclude_unset=True, exclude=set(CHILD_FIELDS))

            if "subject" in updates:
                ra.subject_type, ra.subject_id = _parse_ref(updates.pop("subject"), RiskAssessmentSubjectType, "subject")
            if "encounter_id" in updates:
                public_enc = updates.pop("encounter_id")
                if public_enc is None:
                    ra.encounter_id, ra.encounter_type = None, None
                    updates.setdefault("encounter_display", None)
                else:
                    ra.encounter_id = public_enc
                    ra.encounter_type = EncounterReferenceType.Encounter
            for key, enum_cls, prefix in _REF_FIELDS:
                if key in updates:
                    ref = updates.pop(key)
                    t, i = _optional_ref(ref, enum_cls, key)
                    setattr(ra, f"{prefix}_type", t)
                    setattr(ra, f"{prefix}_id", i)
                    if ref is None:
                        updates.setdefault(f"{prefix}_display", None)

            for field_name, value in updates.items():
                setattr(ra, field_name, value)
            ra.updated_by = updated_by

            # Child lists: a list that is present REPLACES the stored one ([] / null clears it).
            replaced = [f for f in CHILD_FIELDS if f in payload.model_fields_set]
            for f in replaced:
                getattr(ra, CHILD_FIELDS[f]).clear()
            if replaced:
                await session.flush()
                _add_children(session, ra, _OnlyFields(payload, replaced), ra.org_id)

            await session.commit()
            stmt = _with_relationships(select(RiskAssessmentModel).where(RiskAssessmentModel.id == ra.id))
            return (await session.execute(stmt)).scalars().one()

    # ── Delete ────────────────────────────────────────────────────────────────

    async def delete(self, risk_assessment_id: int) -> None:
        async with self.session_factory() as session:
            stmt = select(RiskAssessmentModel).where(RiskAssessmentModel.risk_assessment_id == risk_assessment_id)
            ra = (await session.execute(stmt)).scalars().first()
            if ra:
                await session.delete(ra)
                await session.commit()
