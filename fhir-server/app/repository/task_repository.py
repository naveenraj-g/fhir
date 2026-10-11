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
    parse_open_reference_param,
    parse_reference_param,
    period_date_clause,
    reference_clause,
    split_or,
    token_clause,
)
from app.models.enums import EncounterReferenceType
from app.models.task.enums import (
    TaskInsuranceReferenceType,
    TaskIntent,
    TaskLocationReferenceType,
    TaskOwnerReferenceType,
    TaskPartOfReferenceType,
    TaskPriority,
    TaskRelevantHistoryReferenceType,
    TaskRequesterReferenceType,
    TaskRestrictionRecipientReferenceType,
    TaskStatus,
)
from app.models.task.task import (
    TaskBasedOn,
    TaskIdentifier,
    TaskInput,
    TaskInsurance,
    TaskModel,
    TaskNote,
    TaskOutput,
    TaskPartOf,
    TaskPerformerType,
    TaskRelevantHistory,
    TaskRestrictionRecipient,
)
from app.schemas.task.input import TaskCreateSchema, TaskPatchSchema


@dataclass
class TaskSearch:
    """FHIR R4 Task search parameters (https://www.hl7.org/fhir/R4/task.html#search)."""

    id: Optional[str] = None                      # _id
    identifier: Optional[str] = None
    group_identifier: Optional[str] = None
    task_status: Optional[str] = None
    intent: Optional[str] = None
    priority: Optional[str] = None
    code: Optional[str] = None
    business_status: Optional[str] = None
    subject: Optional[str] = None                 # Task.for (any resource type)
    patient: Optional[str] = None                 # Task.for restricted to Patient
    focus: Optional[str] = None
    encounter: Optional[str] = None
    owner: Optional[str] = None
    requester: Optional[str] = None
    performer: Optional[str] = None               # token on Task.performerType
    based_on: Optional[str] = None
    part_of: Optional[str] = None
    authored_on: List[str] = field(default_factory=list)
    modified: List[str] = field(default_factory=list)
    period: List[str] = field(default_factory=list)          # Task.executionPeriod
    last_updated: List[str] = field(default_factory=list)    # _lastUpdated


class _PatientOnly(str, Enum):
    Patient = "Patient"


# Child lists shared by create and patch. The payload field and the relationship share one name.
CHILD_FIELDS = (
    "identifiers", "based_on", "part_of", "performer_types", "insurance", "notes",
    "relevant_history", "restriction_recipients", "inputs", "outputs",
)

# Scalar columns copied 1:1 from the payload (references are handled separately).
SCALAR_FIELDS = (
    "description", "instantiates_canonical", "instantiates_uri", "authored_on", "last_modified",
    "group_identifier_use", "group_identifier_system", "group_identifier_value",
    "group_identifier_type_system", "group_identifier_type_code",
    "group_identifier_type_display", "group_identifier_type_text",
    "status_reason_system", "status_reason_code", "status_reason_display", "status_reason_text",
    "business_status_system", "business_status_code", "business_status_display", "business_status_text",
    "code_system", "code_code", "code_display", "code_text",
    "execution_period_start", "execution_period_end",
    "reason_code_system", "reason_code_code", "reason_code_display", "reason_code_text",
    "restriction_repetitions", "restriction_period_start", "restriction_period_end",
    "focus_display", "for_display", "encounter_display", "requester_display",
    "owner_display", "location_display", "reason_reference_display",
)

# Single-reference fields: (payload field, allowed-type enum or None for Reference(Any), column prefix)
REFERENCE_FIELDS = (
    ("focus", None, "focus"),
    ("for_reference", None, "for"),
    ("encounter", EncounterReferenceType, "encounter"),
    ("requester", TaskRequesterReferenceType, "requester"),
    ("owner", TaskOwnerReferenceType, "owner"),
    ("location", TaskLocationReferenceType, "location"),
    ("reason_reference", None, "reason_reference"),
)

# value[x] columns shared by Task.input and Task.output (the open Reference is handled separately).
VALUE_FIELDS = tuple(
    c.name for c in TaskInput.__table__.columns
    if c.name.startswith("value_") and not c.name.startswith("value_reference")
)


class _OnlyFields:
    """View of a payload exposing only the listed fields; every other attribute reads as None."""

    def __init__(self, payload, fields):
        self._payload = payload
        self._fields = set(fields)

    def __getattr__(self, name):
        return getattr(self._payload, name) if name in self._fields else None


def _with_relationships(stmt):
    return stmt.options(
        selectinload(TaskModel.identifiers),
        selectinload(TaskModel.based_on),
        selectinload(TaskModel.part_of),
        selectinload(TaskModel.performer_types),
        selectinload(TaskModel.insurance),
        selectinload(TaskModel.notes),
        selectinload(TaskModel.relevant_history),
        selectinload(TaskModel.restriction_recipients),
        selectinload(TaskModel.inputs),
        selectinload(TaskModel.outputs),
    )


def _unprocessable(detail: str) -> HTTPException:
    return HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


def _parse_ref(ref: str, enum_cls, field_name: str):
    """
    Parse 'Type/id' (format check only — existence is never verified).

    With enum_cls the type must be one of the allowed values; with None (Reference(Any))
    any resource type string is accepted.
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


def _as_utc(d):
    return d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d


def _add_children(session, task, payload, org_id) -> None:
    """Create the child rows for every child list present on `payload` (None / missing = none)."""
    for item in payload.identifiers or []:
        session.add(TaskIdentifier(
            task=task, org_id=org_id, use=item.use, type_system=item.type_system, type_code=item.type_code,
            type_display=item.type_display, type_text=item.type_text, system=item.system, value=item.value,
            period_start=item.period_start, period_end=item.period_end, assigner=item.assigner))

    for item in payload.based_on or []:
        t, i = _parse_ref(item.reference, None, "based_on.reference")
        session.add(TaskBasedOn(task=task, org_id=org_id, reference_type=t, reference_id=i,
                                reference_display=item.reference_display))

    for item in payload.part_of or []:
        t, i = _parse_ref(item.reference, TaskPartOfReferenceType, "part_of.reference")
        session.add(TaskPartOf(task=task, org_id=org_id, reference_type=t, reference_id=i,
                               reference_display=item.reference_display))

    for item in payload.performer_types or []:
        session.add(TaskPerformerType(
            task=task, org_id=org_id, coding_system=item.coding_system, coding_code=item.coding_code,
            coding_display=item.coding_display, text=item.text))

    for item in payload.insurance or []:
        t, i = _parse_ref(item.reference, TaskInsuranceReferenceType, "insurance.reference")
        session.add(TaskInsurance(task=task, org_id=org_id, reference_type=t, reference_id=i,
                                  reference_display=item.reference_display))

    for item in payload.notes or []:
        t, i = _optional_ref(item.author_reference, None, "note.author_reference")
        session.add(TaskNote(
            task=task, org_id=org_id, text=item.text, time=item.time, author_string=item.author_string,
            author_reference_type=t, author_reference_id=i,
            author_reference_display=item.author_reference_display))

    for item in payload.relevant_history or []:
        t, i = _parse_ref(item.reference, TaskRelevantHistoryReferenceType, "relevant_history.reference")
        session.add(TaskRelevantHistory(task=task, org_id=org_id, reference_type=t, reference_id=i,
                                        reference_display=item.reference_display))

    for item in payload.restriction_recipients or []:
        t, i = _parse_ref(item.reference, TaskRestrictionRecipientReferenceType, "restriction_recipient.reference")
        session.add(TaskRestrictionRecipient(task=task, org_id=org_id, reference_type=t, reference_id=i,
                                             reference_display=item.reference_display))

    for model_cls, items, label in ((TaskInput, payload.inputs, "input"), (TaskOutput, payload.outputs, "output")):
        for item in items or []:
            t, i = _optional_ref(item.value_reference, None, f"{label}.value_reference")
            row = model_cls(
                task=task, org_id=org_id,
                type_system=item.type_system, type_code=item.type_code,
                type_display=item.type_display, type_text=item.type_text,
                value_reference_type=t, value_reference_id=i,
                value_reference_display=item.value_reference_display,
            )
            for name in VALUE_FIELDS:
                setattr(row, name, getattr(item, name))
            session.add(row)


class TaskRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    async def get_by_task_id(self, task_id: int) -> Optional[TaskModel]:
        async with self.session_factory() as session:
            stmt = _with_relationships(select(TaskModel).where(TaskModel.task_id == task_id))
            return (await session.execute(stmt)).scalars().first()

    def _apply_list_filters(self, stmt, user_id, org_id, search: Optional[TaskSearch] = None):
        """user_id/org_id are optional tenant filters; `search` carries FHIR R4 search params."""
        if user_id:
            stmt = stmt.where(TaskModel.user_id == user_id)
        if org_id:
            stmt = stmt.where(TaskModel.org_id == org_id)
        if search is None:
            return stmt
        M = TaskModel

        if search.id:
            ids = []
            for v in split_or(search.id):
                try:
                    ids.append(int(v))
                except ValueError:
                    raise _unprocessable(f"Invalid _id '{v}'. Must be an integer.")
            stmt = stmt.where(M.task_id.in_(ids))

        clause = token_clause(TaskIdentifier.system, TaskIdentifier.value, search.identifier)
        if clause is not None:
            stmt = stmt.where(select(TaskIdentifier.id).where(TaskIdentifier.task_id == M.id, clause).exists())
        clause = token_clause(M.group_identifier_system, M.group_identifier_value, search.group_identifier)
        if clause is not None:
            stmt = stmt.where(clause)

        for value, enum_cls, col, name in (
            (search.task_status, TaskStatus, M.status, "status"),
            (search.intent, TaskIntent, M.intent, "intent"),
            (search.priority, TaskPriority, M.priority, "priority"),
        ):
            members = enum_token_values(value, enum_cls, name)
            if members:
                stmt = stmt.where(col.in_(members))

        for value, sys_col, code_col in (
            (search.code, M.code_system, M.code_code),
            (search.business_status, M.business_status_system, M.business_status_code),
        ):
            clause = token_clause(sys_col, code_col, value)
            if clause is not None:
                stmt = stmt.where(clause)

        clause = token_clause(TaskPerformerType.coding_system, TaskPerformerType.coding_code, search.performer)
        if clause is not None:
            stmt = stmt.where(select(TaskPerformerType.id).where(TaskPerformerType.task_id == M.id, clause).exists())

        # Task.for / focus are Reference(Any); patient restricts Task.for to Patient.
        if search.subject:
            stmt = stmt.where(reference_clause(M.for_type, M.for_id, parse_open_reference_param(search.subject, "subject")))
        if search.patient:
            stmt = stmt.where(reference_clause(
                M.for_type, M.for_id, [(t.value if t else None, i) for t, i in parse_reference_param(search.patient, _PatientOnly, "patient")]))
        if search.focus:
            stmt = stmt.where(reference_clause(M.focus_type, M.focus_id, parse_open_reference_param(search.focus, "focus")))

        # encounter_id stores the public encounter id (no join needed).
        if search.encounter:
            stmt = stmt.where(reference_clause(
                M.encounter_type, M.encounter_id, parse_reference_param(search.encounter, EncounterReferenceType, "encounter")))
        if search.owner:
            stmt = stmt.where(reference_clause(
                M.owner_type, M.owner_id, parse_reference_param(search.owner, TaskOwnerReferenceType, "owner")))
        if search.requester:
            stmt = stmt.where(reference_clause(
                M.requester_type, M.requester_id, parse_reference_param(search.requester, TaskRequesterReferenceType, "requester")))

        # based-on is Reference(Any); part-of is Reference(Task).
        if search.based_on:
            clause = reference_clause(TaskBasedOn.reference_type, TaskBasedOn.reference_id,
                                      parse_open_reference_param(search.based_on, "based-on"))
            stmt = stmt.where(select(TaskBasedOn.id).where(TaskBasedOn.task_id == M.id, clause).exists())
        if search.part_of:
            clause = reference_clause(TaskPartOf.reference_type, TaskPartOf.reference_id,
                                      parse_reference_param(search.part_of, TaskPartOfReferenceType, "part-of"))
            stmt = stmt.where(select(TaskPartOf.id).where(TaskPartOf.task_id == M.id, clause).exists())

        for values, col, name in (
            (search.authored_on, M.authored_on, "authored-on"),
            (search.modified, M.last_modified, "modified"),
        ):
            for value in values or []:
                prefix, s_lo, s_hi = parse_date_param(value, name)
                stmt = stmt.where(instant_clause(col, prefix, s_lo, s_hi))
        for value in search.period or []:
            prefix, s_lo, s_hi = parse_date_param(value, "period")
            stmt = stmt.where(period_date_clause(M.execution_period_start, M.execution_period_end, prefix, s_lo, s_hi))
        for value in search.last_updated or []:
            prefix, s_lo, s_hi = parse_date_param(value, "_lastUpdated")
            stmt = stmt.where(instant_clause(func.coalesce(M.updated_at, M.created_at), prefix, s_lo, s_hi))
        return stmt

    async def _search(
        self, user_id, org_id, search: Optional[TaskSearch], limit: int, offset: int
    ) -> Tuple[List[TaskModel], int]:
        async with self.session_factory() as session:
            base = self._apply_list_filters(_with_relationships(select(TaskModel)), user_id, org_id, search)
            count_base = self._apply_list_filters(select(func.count()).select_from(TaskModel), user_id, org_id, search)
            total = (await session.execute(count_base)).scalar_one()
            rows = list((await session.execute(
                base.order_by(TaskModel.authored_on.desc().nulls_last(), TaskModel.id.desc())
                .offset(offset).limit(limit)
            )).scalars().all())
        return rows, total

    async def get_me(
        self, user_id: str, org_id: str, search: Optional[TaskSearch] = None, limit: int = 50, offset: int = 0
    ) -> Tuple[List[TaskModel], int]:
        return await self._search(user_id, org_id, search, limit, offset)

    async def list(
        self, user_id: Optional[str] = None, org_id: Optional[str] = None,
        search: Optional[TaskSearch] = None, limit: int = 50, offset: int = 0,
    ) -> Tuple[List[TaskModel], int]:
        return await self._search(user_id, org_id, search, limit, offset)

    async def create(
        self, payload: TaskCreateSchema, user_id: Optional[str], org_id: Optional[str], created_by: Optional[str]
    ) -> TaskModel:
        refs = {}
        for payload_field, enum_cls, prefix in REFERENCE_FIELDS:
            t, i = _optional_ref(getattr(payload, payload_field), enum_cls, payload_field)
            refs[f"{prefix}_type"], refs[f"{prefix}_id"] = t, i

        async with self.session_factory() as session:
            task = TaskModel(
                user_id=user_id, org_id=org_id, created_by=created_by,
                status=payload.status, intent=payload.intent, priority=payload.priority,
                **{name: getattr(payload, name) for name in SCALAR_FIELDS},
                **refs,
            )
            session.add(task)
            _add_children(session, task, payload, org_id)
            await session.commit()

            stmt = _with_relationships(select(TaskModel).where(TaskModel.id == task.id))
            return (await session.execute(stmt)).scalars().one()

    async def patch(self, task_id: int, payload: TaskPatchSchema, updated_by: Optional[str]) -> Optional[TaskModel]:
        async with self.session_factory() as session:
            stmt = _with_relationships(select(TaskModel).where(TaskModel.task_id == task_id))
            task = (await session.execute(stmt)).scalars().first()
            if not task:
                return None

            updates = payload.model_dump(exclude_unset=True, exclude=set(CHILD_FIELDS))

            for key in ("status", "intent", "priority"):
                if key in updates:
                    setattr(task, key, updates.pop(key))

            # Reference fields arrive as 'Type/id' strings; null clears them (and their display).
            for payload_field, enum_cls, prefix in REFERENCE_FIELDS:
                if payload_field in updates:
                    ref = updates.pop(payload_field)
                    t, i = _optional_ref(ref, enum_cls, payload_field)
                    setattr(task, f"{prefix}_type", t)
                    setattr(task, f"{prefix}_id", i)
                    if ref is None:
                        updates.setdefault(f"{prefix}_display", None)

            for name, value in updates.items():
                if name in SCALAR_FIELDS:
                    setattr(task, name, value)
            task.updated_by = updated_by

            # Child lists: a list that is present REPLACES the stored one ([] / null clears it).
            replaced = [f for f in CHILD_FIELDS if f in payload.model_fields_set]
            for f in replaced:
                getattr(task, f).clear()
            if replaced:
                await session.flush()
                _add_children(session, task, _OnlyFields(payload, replaced), task.org_id)

            if task.authored_on and task.last_modified and _as_utc(task.last_modified) < _as_utc(task.authored_on):
                raise _unprocessable("last_modified must be on or after authored_on.")

            await session.commit()
            stmt = _with_relationships(select(TaskModel).where(TaskModel.id == task.id))
            return (await session.execute(stmt)).scalars().one()

    async def delete(self, task_id: int) -> None:
        async with self.session_factory() as session:
            task = (await session.execute(select(TaskModel).where(TaskModel.task_id == task_id))).scalars().first()
            if not task:
                raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Task not found")
            await session.delete(task)
            await session.commit()
