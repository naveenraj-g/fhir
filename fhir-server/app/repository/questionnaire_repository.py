from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException, status as http_status
from sqlalchemy import func, or_
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker  # noqa: F401
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.search_params import (
    enum_token_values,
    instant_clause,
    parse_date_param,
    period_date_clause,
    split_or,
    string_clause,
    token_clause,
)
from app.models.questionnaire.enums import (
    QuestionnaireStatus,
    QuestionnaireUseContextReferenceType,
)
from app.models.questionnaire.questionnaire import (
    QuestionnaireCode,
    QuestionnaireContact,
    QuestionnaireContactTelecom,
    QuestionnaireIdentifier,
    QuestionnaireItem,
    QuestionnaireItemAnswerOption,
    QuestionnaireItemCode,
    QuestionnaireItemEnableWhen,
    QuestionnaireItemInitial,
    QuestionnaireJurisdiction,
    QuestionnaireModel,
    QuestionnaireSubjectType,
    QuestionnaireUseContext,
)
from app.schemas.questionnaire.input import (
    QuestionnaireCreateSchema,
    QuestionnaireItemInput,
    QuestionnairePatchSchema,
)

# String search params that support the `:exact` / `:contains` modifiers.
STRING_PARAMS = ("name", "title", "publisher", "description")


@dataclass
class QuestionnaireSearch:
    """FHIR R4 Questionnaire search parameters (https://www.hl7.org/fhir/R4/questionnaire.html#search)."""

    id: Optional[str] = None                      # _id
    identifier: Optional[str] = None
    url: Optional[str] = None
    version: Optional[str] = None
    q_status: Optional[str] = None
    date: List[str] = field(default_factory=list)
    effective: List[str] = field(default_factory=list)
    jurisdiction: Optional[str] = None
    code: Optional[str] = None                    # item.code token
    definition: Optional[str] = None              # item.definition uri
    subject_type: Optional[str] = None
    context: Optional[str] = None                 # useContext.valueCodeableConcept token
    context_type: Optional[str] = None            # useContext.code token
    last_updated: List[str] = field(default_factory=list)   # _lastUpdated
    # string params: {"name": {"startswith": "x", "contains": "y", "exact": "z"}, ...}
    strings: Dict[str, Dict[str, str]] = field(default_factory=dict)


def _with_relationships(stmt):
    """Eager-load every child table; items are loaded flat (all depths) with their own children."""
    return stmt.options(
        selectinload(QuestionnaireModel.identifiers),
        selectinload(QuestionnaireModel.subject_types),
        selectinload(QuestionnaireModel.contacts).selectinload(QuestionnaireContact.telecoms),
        selectinload(QuestionnaireModel.use_contexts),
        selectinload(QuestionnaireModel.jurisdictions),
        selectinload(QuestionnaireModel.codes),
        selectinload(QuestionnaireModel.items).selectinload(QuestionnaireItem.codes),
        selectinload(QuestionnaireModel.items).selectinload(QuestionnaireItem.enable_whens),
        selectinload(QuestionnaireModel.items).selectinload(QuestionnaireItem.answer_options),
        selectinload(QuestionnaireModel.items).selectinload(QuestionnaireItem.initials),
    )


def _unprocessable(detail: str) -> HTTPException:
    return HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


def _parse_ref(ref: str, enum_cls, field_name: str):
    """Parse 'Type/id'. With enum_cls the type is validated against it; otherwise (open Reference(Any)) any type is accepted."""
    parts = ref.split("/", 1)
    if len(parts) != 2 or not parts[0]:
        raise _unprocessable(f"Invalid reference format: '{ref}'. Expected 'ResourceType/id'.")
    try:
        ref_id = int(parts[1])
    except ValueError:
        raise _unprocessable(f"Invalid reference id in: '{ref}'. Id must be an integer.")
    if enum_cls is None:
        return parts[0], ref_id
    try:
        return enum_cls(parts[0]), ref_id
    except ValueError:
        raise _unprocessable(
            f"Invalid reference type '{parts[0]}' for {field_name}. Allowed: {[e.value for e in enum_cls]}."
        )


def _open_ref(ref: Optional[str], field_name: str):
    """Optional open reference -> (type, id) or (None, None)."""
    if ref is None:
        return None, None
    return _parse_ref(ref, None, field_name)


def _copy(dst, src, prefix_dst: str, prefix_src: str, names: Tuple[str, ...]) -> None:
    """Copy `<prefix_src><name>` attributes of a pydantic input onto `<prefix_dst><name>` of an ORM row."""
    for n in names:
        setattr(dst, f"{prefix_dst}{n}", getattr(src, f"{prefix_src}{n}"))


_ANSWER_NAMES = (
    "boolean", "decimal", "integer", "date", "datetime", "time", "string",
    "coding_system", "coding_code", "coding_display",
    "quantity_value", "quantity_unit", "quantity_system", "quantity_code",
)
_OPTION_NAMES = (
    "integer", "date", "time", "string",
    "coding_system", "coding_code", "coding_display",
)
_INITIAL_NAMES = (
    "boolean", "decimal", "integer", "date", "datetime", "time", "string", "uri",
    "attachment_content_type", "attachment_language", "attachment_data", "attachment_url",
    "attachment_size", "attachment_hash", "attachment_title", "attachment_creation",
    "coding_system", "coding_code", "coding_display",
    "quantity_value", "quantity_unit", "quantity_system", "quantity_code",
)


def _build_items(
    q: QuestionnaireModel,
    items: Optional[List[QuestionnaireItemInput]],
    parent: Optional[QuestionnaireItem],
    org_id: Optional[str],
    counter: List[int],
    session,
) -> None:
    """Depth-first creation of the item tree; `counter` assigns the global sibling-order position."""
    for node in items or []:
        counter[0] += 1
        db = QuestionnaireItem(
            questionnaire=q, parent=parent, org_id=org_id, position=counter[0],
            link_id=node.link_id, definition=node.definition, prefix=node.prefix, text=node.text,
            type=node.type, enable_behavior=node.enable_behavior, required=node.required,
            repeats=node.repeats, read_only=node.read_only, max_length=node.max_length,
            answer_value_set=node.answer_value_set,
        )
        session.add(db)
        for c in node.code or []:
            session.add(QuestionnaireItemCode(item=db, org_id=org_id, system=c.system, code=c.code, display=c.display))
        for e in node.enable_when or []:
            row = QuestionnaireItemEnableWhen(item=db, org_id=org_id, question=e.question, operator=e.operator)
            _copy(row, e, "answer_", "answer_", _ANSWER_NAMES)
            row.answer_reference_type, row.answer_reference_id = _open_ref(e.answer_reference, "enable_when.answer_reference")
            row.answer_reference_display = e.answer_reference_display
            session.add(row)
        for a in node.answer_option or []:
            row = QuestionnaireItemAnswerOption(item=db, org_id=org_id, initial_selected=a.initial_selected)
            _copy(row, a, "value_", "value_", _OPTION_NAMES)
            row.value_reference_type, row.value_reference_id = _open_ref(a.value_reference, "answer_option.value_reference")
            row.value_reference_display = a.value_reference_display
            session.add(row)
        for i in node.initial or []:
            row = QuestionnaireItemInitial(item=db, org_id=org_id)
            _copy(row, i, "value_", "value_", _INITIAL_NAMES)
            row.value_reference_type, row.value_reference_id = _open_ref(i.value_reference, "initial.value_reference")
            row.value_reference_display = i.value_reference_display
            session.add(row)
        _build_items(q, node.item, db, org_id, counter, session)



# Child-list fields shared by create and patch: payload field -> QuestionnaireModel relationship name.
CHILD_FIELDS = {
    "identifier": "identifiers",
    "subject_type": "subject_types",
    "contact": "contacts",
    "use_context": "use_contexts",
    "jurisdiction": "jurisdictions",
    "code": "codes",
    "item": "items",
}


class _OnlyFields:
    """View of a payload exposing only the listed fields; every other attribute reads as None."""

    def __init__(self, payload, fields):
        self._payload = payload
        self._fields = set(fields)

    def __getattr__(self, name):
        return getattr(self._payload, name) if name in self._fields else None


def _add_children(session, q, payload, org_id) -> None:
    """Create the child rows (and the item tree) for every child list present on `payload`."""
    for i in payload.identifier or []:
        session.add(QuestionnaireIdentifier(
            questionnaire=q, org_id=org_id, use=i.use, type_system=i.type_system, type_code=i.type_code,
            type_display=i.type_display, type_text=i.type_text, system=i.system, value=i.value,
            period_start=i.period_start, period_end=i.period_end, assigner=i.assigner,
        ))
    for code in payload.subject_type or []:
        session.add(QuestionnaireSubjectType(questionnaire=q, org_id=org_id, code=code))
    for c in payload.contact or []:
        contact = QuestionnaireContact(questionnaire=q, org_id=org_id, name=c.name)
        session.add(contact)
        for t in c.telecom or []:
            session.add(QuestionnaireContactTelecom(
                contact=contact, org_id=org_id, system=t.system, value=t.value, use=t.use,
                rank=t.rank, period_start=t.period_start, period_end=t.period_end,
            ))
    for u in payload.use_context or []:
        ref_type, ref_id = (None, None)
        if u.value_reference:
            ref_type, ref_id = _parse_ref(
                u.value_reference, QuestionnaireUseContextReferenceType, "use_context.value_reference"
            )
        session.add(QuestionnaireUseContext(
            questionnaire=q, org_id=org_id,
            code_system=u.code_system, code_code=u.code_code, code_display=u.code_display,
            value_cc_system=u.value_cc_system, value_cc_code=u.value_cc_code,
            value_cc_display=u.value_cc_display, value_cc_text=u.value_cc_text,
            value_quantity_value=u.value_quantity_value, value_quantity_unit=u.value_quantity_unit,
            value_quantity_system=u.value_quantity_system, value_quantity_code=u.value_quantity_code,
            value_range_low_value=u.value_range_low_value, value_range_low_unit=u.value_range_low_unit,
            value_range_high_value=u.value_range_high_value, value_range_high_unit=u.value_range_high_unit,
            value_reference_type=ref_type, value_reference_id=ref_id,
            value_reference_display=u.value_reference_display,
        ))
    for j in payload.jurisdiction or []:
        session.add(QuestionnaireJurisdiction(
            questionnaire=q, org_id=org_id, coding_system=j.coding_system, coding_code=j.coding_code,
            coding_display=j.coding_display, text=j.text,
        ))
    for c in payload.code or []:
        session.add(QuestionnaireCode(questionnaire=q, org_id=org_id, system=c.system, code=c.code, display=c.display))

    _build_items(q, payload.item, None, org_id, [0], session)

class QuestionnaireRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    # ── Read ──────────────────────────────────────────────────────────────────

    async def get_by_questionnaire_id(self, questionnaire_id: int) -> Optional[QuestionnaireModel]:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(QuestionnaireModel).where(QuestionnaireModel.questionnaire_id == questionnaire_id)
            )
            return (await session.execute(stmt)).scalars().first()

    def _apply_list_filters(self, stmt, user_id, org_id, search: Optional[QuestionnaireSearch] = None):
        """user_id/org_id are optional tenant filters; `search` carries FHIR R4 search params."""
        if user_id:
            stmt = stmt.where(QuestionnaireModel.user_id == user_id)
        if org_id:
            stmt = stmt.where(QuestionnaireModel.org_id == org_id)
        if search is None:
            return stmt
        M = QuestionnaireModel

        # _id
        if search.id:
            ids = []
            for v in split_or(search.id):
                try:
                    ids.append(int(v))
                except ValueError:
                    raise _unprocessable(f"Invalid _id '{v}'. Must be an integer.")
            stmt = stmt.where(M.questionnaire_id.in_(ids))

        # identifier (token)
        clause = token_clause(QuestionnaireIdentifier.system, QuestionnaireIdentifier.value, search.identifier)
        if clause is not None:
            stmt = stmt.where(select(QuestionnaireIdentifier.id).where(
                QuestionnaireIdentifier.questionnaire_id == M.id, clause).exists())

        # url (uri, exact) / version (token-like exact)
        urls = split_or(search.url)
        if urls:
            stmt = stmt.where(M.url.in_(urls))
        versions = split_or(search.version)
        if versions:
            stmt = stmt.where(M.version.in_(versions))

        # status
        statuses = enum_token_values(search.q_status, QuestionnaireStatus, "status")
        if statuses:
            stmt = stmt.where(M.status.in_(statuses))

        # string params with :exact / :contains modifiers
        for name in STRING_PARAMS:
            for mode, value in (search.strings.get(name) or {}).items():
                clause = string_clause(getattr(M, name), value, mode)
                if clause is not None:
                    stmt = stmt.where(clause)

        # date (Questionnaire.date) / effective (effectivePeriod)
        for value in search.date or []:
            prefix, s_lo, s_hi = parse_date_param(value, "date")
            stmt = stmt.where(instant_clause(M.date, prefix, s_lo, s_hi))
        for value in search.effective or []:
            prefix, s_lo, s_hi = parse_date_param(value, "effective")
            stmt = stmt.where(period_date_clause(M.effective_period_start, M.effective_period_end, prefix, s_lo, s_hi))

        # _lastUpdated
        for value in search.last_updated or []:
            prefix, s_lo, s_hi = parse_date_param(value, "_lastUpdated")
            stmt = stmt.where(instant_clause(func.coalesce(M.updated_at, M.created_at), prefix, s_lo, s_hi))

        # jurisdiction (token on CodeableConcept)
        clause = token_clause(QuestionnaireJurisdiction.coding_system, QuestionnaireJurisdiction.coding_code, search.jurisdiction)
        if clause is not None:
            stmt = stmt.where(select(QuestionnaireJurisdiction.id).where(
                QuestionnaireJurisdiction.questionnaire_id == M.id, clause).exists())

        # code (token on any item.code) — questionnaire-level code[] also matches
        item_clause = token_clause(QuestionnaireItemCode.system, QuestionnaireItemCode.code, search.code)
        if item_clause is not None:
            top_clause = token_clause(QuestionnaireCode.system, QuestionnaireCode.code, search.code)
            item_exists = select(QuestionnaireItemCode.id).join(
                QuestionnaireItem, QuestionnaireItem.id == QuestionnaireItemCode.item_id
            ).where(QuestionnaireItem.questionnaire_id == M.id, item_clause).exists()
            top_exists = select(QuestionnaireCode.id).where(
                QuestionnaireCode.questionnaire_id == M.id, top_clause).exists()
            stmt = stmt.where(or_(item_exists, top_exists))

        # definition (uri, exact) on any item
        defs = split_or(search.definition)
        if defs:
            stmt = stmt.where(select(QuestionnaireItem.id).where(
                QuestionnaireItem.questionnaire_id == M.id, QuestionnaireItem.definition.in_(defs)).exists())

        # subject-type (token on code)
        subject_types = split_or(search.subject_type)
        if subject_types:
            stmt = stmt.where(select(QuestionnaireSubjectType.id).where(
                QuestionnaireSubjectType.questionnaire_id == M.id,
                QuestionnaireSubjectType.code.in_(subject_types)).exists())

        # context (useContext value CodeableConcept) / context-type (useContext code)
        clause = token_clause(QuestionnaireUseContext.value_cc_system, QuestionnaireUseContext.value_cc_code, search.context)
        if clause is not None:
            stmt = stmt.where(select(QuestionnaireUseContext.id).where(
                QuestionnaireUseContext.questionnaire_id == M.id, clause).exists())
        clause = token_clause(QuestionnaireUseContext.code_system, QuestionnaireUseContext.code_code, search.context_type)
        if clause is not None:
            stmt = stmt.where(select(QuestionnaireUseContext.id).where(
                QuestionnaireUseContext.questionnaire_id == M.id, clause).exists())
        return stmt

    async def _search(
        self, user_id, org_id, search: Optional[QuestionnaireSearch], limit: int, offset: int
    ) -> Tuple[List[QuestionnaireModel], int]:
        async with self.session_factory() as session:
            base = self._apply_list_filters(_with_relationships(select(QuestionnaireModel)), user_id, org_id, search)
            count_base = self._apply_list_filters(
                select(func.count()).select_from(QuestionnaireModel), user_id, org_id, search
            )
            total = (await session.execute(count_base)).scalar_one()
            rows = list((await session.execute(
                base.order_by(func.coalesce(QuestionnaireModel.date, QuestionnaireModel.created_at).desc().nulls_last(),
                              QuestionnaireModel.id.desc())
                .offset(offset).limit(limit)
            )).scalars().all())
        return rows, total

    async def get_me(
        self, user_id: str, org_id: str, search: Optional[QuestionnaireSearch] = None,
        limit: int = 50, offset: int = 0,
    ) -> Tuple[List[QuestionnaireModel], int]:
        return await self._search(user_id, org_id, search, limit, offset)

    async def list(
        self, user_id: Optional[str] = None, org_id: Optional[str] = None,
        search: Optional[QuestionnaireSearch] = None, limit: int = 50, offset: int = 0,
    ) -> Tuple[List[QuestionnaireModel], int]:
        return await self._search(user_id, org_id, search, limit, offset)

    # ── Create ────────────────────────────────────────────────────────────────

    async def create(
        self,
        payload: QuestionnaireCreateSchema,
        user_id: Optional[str],
        org_id: Optional[str],
        created_by: Optional[str],
    ) -> QuestionnaireModel:
        async with self.session_factory() as session:
            q = QuestionnaireModel(
                user_id=user_id, org_id=org_id, created_by=created_by,
                url=payload.url, version=payload.version, name=payload.name, title=payload.title,
                status=payload.status, experimental=payload.experimental, date=payload.date,
                publisher=payload.publisher, description=payload.description, purpose=payload.purpose,
                copyright=payload.copyright, approval_date=payload.approval_date,
                last_review_date=payload.last_review_date,
                effective_period_start=payload.effective_period_start,
                effective_period_end=payload.effective_period_end,
                derived_from=",".join(payload.derived_from) if payload.derived_from else None,
            )
            session.add(q)

            _add_children(session, q, payload, org_id)

            await session.commit()

            stmt = _with_relationships(select(QuestionnaireModel).where(QuestionnaireModel.id == q.id))
            return (await session.execute(stmt)).scalars().one()

    # ── Patch ─────────────────────────────────────────────────────────────────

    async def patch(
        self, questionnaire_id: int, payload: QuestionnairePatchSchema, updated_by: Optional[str]
    ) -> Optional[QuestionnaireModel]:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(QuestionnaireModel).where(QuestionnaireModel.questionnaire_id == questionnaire_id)
            )
            q = (await session.execute(stmt)).scalars().first()
            if not q:
                return None

            updates = payload.model_dump(exclude_unset=True, exclude=set(CHILD_FIELDS))
            if "derived_from" in updates and updates["derived_from"] is not None:
                updates["derived_from"] = ",".join(updates["derived_from"])
            for field_name, value in updates.items():
                setattr(q, field_name, value)
            q.updated_by = updated_by

            # Child lists (and the whole item tree): a list that is present REPLACES the stored one.
            replaced = [f for f in CHILD_FIELDS if f in payload.model_fields_set]
            for f in replaced:
                getattr(q, CHILD_FIELDS[f]).clear()
            if replaced:
                await session.flush()
                _add_children(session, q, _OnlyFields(payload, replaced), q.org_id)

            await session.commit()

            stmt = _with_relationships(select(QuestionnaireModel).where(QuestionnaireModel.id == q.id))
            return (await session.execute(stmt)).scalars().one()

    # ── Delete ────────────────────────────────────────────────────────────────

    async def delete(self, questionnaire_id: int) -> None:
        async with self.session_factory() as session:
            stmt = select(QuestionnaireModel).where(QuestionnaireModel.questionnaire_id == questionnaire_id)
            q = (await session.execute(stmt)).scalars().first()
            if q:
                await session.delete(q)
                await session.commit()
