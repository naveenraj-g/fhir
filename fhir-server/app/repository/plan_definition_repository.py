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
from app.fhir.mappers.plan_definition.codec import pack
from app.models.plan_definition.enums import (
    DataRequirementRole,
    PlanDefinitionContactKind,
    PlanDefinitionGroupReferenceType,
    PlanDefinitionScheduleReferenceType,
    PlanDefinitionStatus,
    PlanDefinitionUseContextReferenceType,
    RelatedArtifactScope,
    RelatedArtifactType,
)
from app.models.plan_definition.plan_definition import (
    PlanDefinitionAction,
    PlanDefinitionActionCode,
    PlanDefinitionActionCondition,
    PlanDefinitionActionDynamicValue,
    PlanDefinitionActionGoalId,
    PlanDefinitionActionParticipant,
    PlanDefinitionActionRelatedAction,
    PlanDefinitionActionTrigger,
    PlanDefinitionContact,
    PlanDefinitionContactTelecom,
    PlanDefinitionDataRequirement,
    PlanDefinitionDataRequirementCodeFilter,
    PlanDefinitionDataRequirementCodeFilterCode,
    PlanDefinitionDataRequirementDateFilter,
    PlanDefinitionDataRequirementSort,
    PlanDefinitionGoal,
    PlanDefinitionGoalAddress,
    PlanDefinitionGoalTarget,
    PlanDefinitionIdentifier,
    PlanDefinitionJurisdiction,
    PlanDefinitionLibrary,
    PlanDefinitionModel,
    PlanDefinitionRelatedArtifact,
    PlanDefinitionTopic,
    PlanDefinitionUseContext,
)
from app.schemas.plan_definition import PlanDefinitionCreateSchema, PlanDefinitionPatchSchema, validate_plan_tree

# String search params that support the `:exact` / `:contains` modifiers.
STRING_PARAMS = ("name", "title", "publisher", "description")


@dataclass
class PlanDefinitionSearch:
    """FHIR R4 PlanDefinition search parameters (https://www.hl7.org/fhir/R4/plandefinition.html#search)."""

    id: Optional[str] = None                      # _id
    identifier: Optional[str] = None
    url: Optional[str] = None
    version: Optional[str] = None
    pd_status: Optional[str] = None
    type: Optional[str] = None
    topic: Optional[str] = None
    jurisdiction: Optional[str] = None
    context: Optional[str] = None
    context_type: Optional[str] = None
    definition: Optional[str] = None
    depends_on: Optional[str] = None
    derived_from: Optional[str] = None
    predecessor: Optional[str] = None
    successor: Optional[str] = None
    composed_of: Optional[str] = None
    date: List[str] = field(default_factory=list)
    effective: List[str] = field(default_factory=list)
    last_updated: List[str] = field(default_factory=list)   # _lastUpdated
    strings: Dict[str, Dict[str, str]] = field(default_factory=dict)


def _with_relationships(stmt):
    """Eager-load every child table; actions and all their children are loaded flat (all depths)."""
    M = PlanDefinitionModel
    return stmt.options(
        selectinload(M.identifiers),
        selectinload(M.contacts).selectinload(PlanDefinitionContact.telecoms),
        selectinload(M.use_contexts),
        selectinload(M.jurisdictions),
        selectinload(M.topics),
        selectinload(M.libraries),
        selectinload(M.related_artifacts),
        selectinload(M.goals).selectinload(PlanDefinitionGoal.addresses),
        selectinload(M.goals).selectinload(PlanDefinitionGoal.targets),
        selectinload(M.actions),
        selectinload(M.action_codes),
        selectinload(M.action_goal_ids),
        selectinload(M.triggers),
        selectinload(M.conditions),
        selectinload(M.data_requirements).selectinload(PlanDefinitionDataRequirement.code_filters)
        .selectinload(PlanDefinitionDataRequirementCodeFilter.codes),
        selectinload(M.data_requirements).selectinload(PlanDefinitionDataRequirement.date_filters),
        selectinload(M.data_requirements).selectinload(PlanDefinitionDataRequirement.sorts),
        selectinload(M.related_actions),
        selectinload(M.participants),
        selectinload(M.dynamic_values),
    )


def _unprocessable(detail: str) -> HTTPException:
    return HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


def _parse_ref(ref: str, enum_cls, field_name: str):
    """Parse 'Type/id' (format + allowed type only — existence is never verified)."""
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


def _ref_cols(prefix: str, ref: Optional[str], display: Optional[str], enum_cls) -> dict:
    """`<prefix>_type/_id/_display` column values for an optional reference string."""
    if not ref:
        return {f"{prefix}_display": display}
    t, i = _parse_ref(ref, enum_cls, prefix)
    return {f"{prefix}_type": t, f"{prefix}_id": i, f"{prefix}_display": display}


def _names(obj, names) -> dict:
    return {n: getattr(obj, n) for n in names}


def _csv(values) -> Optional[str]:
    items = [str(v) for v in (values or [])]
    return ",".join(items) if items else None


_CC = ("system", "code", "display", "text")


def _cc_names(prefix: str):
    return [f"{prefix}_{s}" for s in _CC]


# ── row builders (used by create AND patch) ────────────────────────────────────


def _add_artifact(session, pd, a, scope, org_id, goal=None, action=None):
    row = PlanDefinitionRelatedArtifact(
        plan_definition=pd, goal=goal, action=action, org_id=org_id, scope=scope, type=a.type, label=a.label,
        display=a.display, citation=a.citation, url=a.url, resource=a.resource,
        **pack("document", "attachment", a.document),
    )
    session.add(row)


def _add_data_requirement(session, pd, dr, role, org_id, action=None, trigger=None):
    row = PlanDefinitionDataRequirement(
        plan_definition=pd, action=action, trigger=trigger, org_id=org_id, role=role, type=dr.type,
        profile=_csv(dr.profile), must_support=_csv(dr.must_support), limit=dr.limit,
        **_names(dr, _cc_names("subject_cc")),
        **_ref_cols("subject_reference", dr.subject_reference, dr.subject_reference_display, PlanDefinitionGroupReferenceType),
    )
    session.add(row)
    for cf in dr.code_filter or []:
        frow = PlanDefinitionDataRequirementCodeFilter(
            data_requirement=row, org_id=org_id, path=cf.path, search_param=cf.search_param, value_set=cf.value_set)
        session.add(frow)
        for c in cf.code or []:
            session.add(PlanDefinitionDataRequirementCodeFilterCode(
                code_filter=frow, org_id=org_id, system=c.system, code=c.code, display=c.display))
    for df in dr.date_filter or []:
        session.add(PlanDefinitionDataRequirementDateFilter(
            data_requirement=row, org_id=org_id, path=df.path, search_param=df.search_param,
            value_datetime=df.value_datetime, **pack("value_period", "period", df.value_period),
            **pack("value_duration", "quantity", df.value_duration)))
    for s in dr.sort or []:
        session.add(PlanDefinitionDataRequirementSort(data_requirement=row, org_id=org_id, path=s.path, direction=s.direction))


def _add_actions(session, pd, actions, parent, org_id, counter):
    """Depth-first creation of the action tree; `counter` assigns the global sibling-order position."""
    for a in actions or []:
        counter[0] += 1
        row = PlanDefinitionAction(
            plan_definition=pd, parent=parent, org_id=org_id, position=counter[0], element_id=a.element_id,
            prefix=a.prefix, title=a.title, description=a.description, text_equivalent=a.text_equivalent,
            priority=a.priority, timing_datetime=a.timing_datetime,
            grouping_behavior=a.grouping_behavior, selection_behavior=a.selection_behavior,
            required_behavior=a.required_behavior, precheck_behavior=a.precheck_behavior,
            cardinality_behavior=a.cardinality_behavior, definition_canonical=a.definition_canonical,
            definition_uri=a.definition_uri, transform=a.transform,
            **_names(a, _cc_names("subject_cc")), **_names(a, _cc_names("type")),
            **_ref_cols("subject_reference", a.subject_reference, a.subject_reference_display, PlanDefinitionGroupReferenceType),
            **pack("timing_age", "quantity", a.timing_age), **pack("timing_period", "period", a.timing_period),
            **pack("timing_duration", "quantity", a.timing_duration), **pack("timing_range", "range", a.timing_range),
            **pack("timing_timing", "timing", a.timing_timing),
        )
        session.add(row)
        for kind, items in (("code", a.code), ("reason", a.reason)):
            for c in items or []:
                session.add(PlanDefinitionActionCode(
                    plan_definition=pd, action=row, org_id=org_id, kind=kind, coding_system=c.coding_system,
                    coding_code=c.coding_code, coding_display=c.coding_display, text=c.text))
        for d in a.documentation or []:
            _add_artifact(session, pd, d, RelatedArtifactScope.action, org_id, action=row)
        for gid in a.goal_id or []:
            session.add(PlanDefinitionActionGoalId(plan_definition=pd, action=row, org_id=org_id, goal_element_id=gid))
        for t in a.trigger or []:
            trow = PlanDefinitionActionTrigger(
                plan_definition=pd, action=row, org_id=org_id, type=t.type, name=t.name,
                timing_date=t.timing_date, timing_datetime=t.timing_datetime,
                **pack("timing_timing", "timing", t.timing_timing),
                **_ref_cols("timing_reference", t.timing_reference, t.timing_reference_display, PlanDefinitionScheduleReferenceType),
                **pack("condition", "expression", t.condition),
            )
            session.add(trow)
            for d in t.data or []:
                _add_data_requirement(session, pd, d, DataRequirementRole.trigger, org_id, trigger=trow)
        for c in a.condition or []:
            session.add(PlanDefinitionActionCondition(
                plan_definition=pd, action=row, org_id=org_id, kind=c.kind, **pack("expression", "expression", c.expression)))
        for d in a.input or []:
            _add_data_requirement(session, pd, d, DataRequirementRole.input, org_id, action=row)
        for d in a.output or []:
            _add_data_requirement(session, pd, d, DataRequirementRole.output, org_id, action=row)
        for r in a.related_action or []:
            session.add(PlanDefinitionActionRelatedAction(
                plan_definition=pd, action=row, org_id=org_id, related_action_id=r.action_id,
                relationship_type=r.relationship, **pack("offset_duration", "quantity", r.offset_duration),
                **pack("offset_range", "range", r.offset_range)))
        for p in a.participant or []:
            session.add(PlanDefinitionActionParticipant(
                plan_definition=pd, action=row, org_id=org_id, type=p.type, **_names(p, _cc_names("role"))))
        for d in a.dynamic_value or []:
            session.add(PlanDefinitionActionDynamicValue(
                plan_definition=pd, action=row, org_id=org_id, path=d.path, **pack("expression", "expression", d.expression)))
        _add_actions(session, pd, a.action, row, org_id, counter)


def _add_goals(session, pd, goals, org_id):
    for g in goals or []:
        row = PlanDefinitionGoal(
            plan_definition=pd, org_id=org_id, element_id=g.element_id,
            **_names(g, _cc_names("category")), **_names(g, _cc_names("description")),
            **_names(g, _cc_names("priority")), **_names(g, _cc_names("start")))
        session.add(row)
        for a in g.addresses or []:
            session.add(PlanDefinitionGoalAddress(
                goal=row, org_id=org_id, coding_system=a.coding_system, coding_code=a.coding_code,
                coding_display=a.coding_display, text=a.text))
        for d in g.documentation or []:
            _add_artifact(session, pd, d, RelatedArtifactScope.goal, org_id, goal=row)
        for t in g.target or []:
            session.add(PlanDefinitionGoalTarget(
                goal=row, org_id=org_id, **_names(t, _cc_names("measure")), **_names(t, _cc_names("detail_cc")),
                **pack("detail_quantity", "quantity", t.detail_quantity), **pack("detail_range", "range", t.detail_range),
                **pack("due", "quantity", t.due)))


_CONTACT_KINDS = ("contact", "author", "editor", "reviewer", "endorser")

# Fields replaced as a unit by PATCH (and created by POST).
CHILD_FIELDS = (
    "identifier", "contact", "author", "editor", "reviewer", "endorser", "use_context", "jurisdiction",
    "topic", "related_artifact", "library", "goal", "action",
)


class _OnlyFields:
    """View of a payload exposing only the listed fields; every other attribute reads as None."""

    def __init__(self, payload, fields):
        self._payload = payload
        self._fields = set(fields)

    def __getattr__(self, name):
        return getattr(self._payload, name) if name in self._fields else None


def _add_children(session, pd, payload, org_id) -> None:
    """Create the child rows for every child list present on `payload` (None / missing = none)."""
    for i in payload.identifier or []:
        session.add(PlanDefinitionIdentifier(
            plan_definition=pd, org_id=org_id, use=i.use, type_system=i.type_system, type_code=i.type_code,
            type_display=i.type_display, type_text=i.type_text, system=i.system, value=i.value,
            period_start=i.period_start, period_end=i.period_end, assigner=i.assigner))
    for kind in _CONTACT_KINDS:
        for c in getattr(payload, kind) or []:
            crow = PlanDefinitionContact(plan_definition=pd, org_id=org_id, kind=PlanDefinitionContactKind(kind), name=c.name)
            session.add(crow)
            for t in c.telecom or []:
                session.add(PlanDefinitionContactTelecom(
                    contact=crow, org_id=org_id, system=t.system, value=t.value, use=t.use, rank=t.rank,
                    period_start=t.period_start, period_end=t.period_end))
    for u in payload.use_context or []:
        session.add(PlanDefinitionUseContext(
            plan_definition=pd, org_id=org_id, code_system=u.code_system, code_code=u.code_code,
            code_display=u.code_display, **_names(u, _cc_names("value_cc")),
            **{f"value_quantity_{s}": getattr(u, f"value_quantity_{s}") for s in ("value", "unit", "system", "code")},
            **{f"value_range_{b}_{s}": getattr(u, f"value_range_{b}_{s}") for b in ("low", "high") for s in ("value", "unit", "system", "code")},
            **_ref_cols("value_reference", u.value_reference, u.value_reference_display, PlanDefinitionUseContextReferenceType)))
    for j in payload.jurisdiction or []:
        session.add(PlanDefinitionJurisdiction(
            plan_definition=pd, org_id=org_id, coding_system=j.coding_system, coding_code=j.coding_code,
            coding_display=j.coding_display, text=j.text))
    for t in payload.topic or []:
        session.add(PlanDefinitionTopic(
            plan_definition=pd, org_id=org_id, coding_system=t.coding_system, coding_code=t.coding_code,
            coding_display=t.coding_display, text=t.text))
    for a in payload.related_artifact or []:
        _add_artifact(session, pd, a, RelatedArtifactScope.plan, org_id)
    for canonical in payload.library or []:
        session.add(PlanDefinitionLibrary(plan_definition=pd, org_id=org_id, canonical=canonical))
    _add_goals(session, pd, payload.goal, org_id)
    _add_actions(session, pd, payload.action, None, org_id, [0])


def _clear(pd, field_name: str) -> None:
    """Remove the stored rows behind one child-list field (delete-orphan deletes them)."""
    if field_name == "identifier":
        pd.identifiers.clear()
    elif field_name in _CONTACT_KINDS:
        for c in [c for c in pd.contacts if getattr(c.kind, "value", c.kind) == field_name]:
            pd.contacts.remove(c)
    elif field_name == "use_context":
        pd.use_contexts.clear()
    elif field_name == "jurisdiction":
        pd.jurisdictions.clear()
    elif field_name == "topic":
        pd.topics.clear()
    elif field_name == "library":
        pd.libraries.clear()
    elif field_name == "related_artifact":
        for r in [r for r in pd.related_artifacts if getattr(r.scope, "value", r.scope) == "plan"]:
            pd.related_artifacts.remove(r)
    elif field_name == "goal":
        for r in [r for r in pd.related_artifacts if getattr(r.scope, "value", r.scope) == "goal"]:
            pd.related_artifacts.remove(r)
        pd.goals.clear()
    elif field_name == "action":
        for r in [r for r in pd.related_artifacts if getattr(r.scope, "value", r.scope) == "action"]:
            pd.related_artifacts.remove(r)
        for coll in (pd.action_codes, pd.action_goal_ids, pd.triggers, pd.conditions, pd.data_requirements,
                     pd.related_actions, pd.participants, pd.dynamic_values):
            coll.clear()
        pd.actions.clear()


def _canonical_match(col, value: str):
    """Match a stored canonical against a search value: exact, or the stored URL ends with '/<value>'."""
    return or_(col == value, col.like(f"%/{value}"))


class PlanDefinitionRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    # ── Read ──────────────────────────────────────────────────────────────────

    async def get_by_plan_definition_id(self, plan_definition_id: int) -> Optional[PlanDefinitionModel]:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(PlanDefinitionModel).where(PlanDefinitionModel.plan_definition_id == plan_definition_id)
            )
            return (await session.execute(stmt)).scalars().first()

    def _apply_list_filters(self, stmt, user_id, org_id, search: Optional[PlanDefinitionSearch] = None):
        """user_id/org_id are tenant filters; `search` carries the FHIR R4 search parameters."""
        if user_id:
            stmt = stmt.where(PlanDefinitionModel.user_id == user_id)
        if org_id:
            stmt = stmt.where(PlanDefinitionModel.org_id == org_id)
        if search is None:
            return stmt
        M = PlanDefinitionModel

        if search.id:
            ids = []
            for v in split_or(search.id):
                try:
                    ids.append(int(v))
                except ValueError:
                    raise _unprocessable(f"Invalid _id '{v}'. Must be an integer.")
            stmt = stmt.where(M.plan_definition_id.in_(ids))

        clause = token_clause(PlanDefinitionIdentifier.system, PlanDefinitionIdentifier.value, search.identifier)
        if clause is not None:
            stmt = stmt.where(select(PlanDefinitionIdentifier.id).where(
                PlanDefinitionIdentifier.plan_definition_id == M.id, clause).exists())

        urls = split_or(search.url)
        if urls:
            stmt = stmt.where(M.url.in_(urls))
        versions = split_or(search.version)
        if versions:
            stmt = stmt.where(M.version.in_(versions))

        statuses = enum_token_values(search.pd_status, PlanDefinitionStatus, "status")
        if statuses:
            stmt = stmt.where(M.status.in_(statuses))

        for name in STRING_PARAMS:
            for mode, value in (search.strings.get(name) or {}).items():
                clause = string_clause(getattr(M, name), value, mode)
                if clause is not None:
                    stmt = stmt.where(clause)

        clause = token_clause(M.type_system, M.type_code, search.type)
        if clause is not None:
            stmt = stmt.where(clause)

        for value, model in ((search.topic, PlanDefinitionTopic), (search.jurisdiction, PlanDefinitionJurisdiction)):
            clause = token_clause(model.coding_system, model.coding_code, value)
            if clause is not None:
                stmt = stmt.where(select(model.id).where(model.plan_definition_id == M.id, clause).exists())

        clause = token_clause(PlanDefinitionUseContext.value_cc_system, PlanDefinitionUseContext.value_cc_code, search.context)
        if clause is not None:
            stmt = stmt.where(select(PlanDefinitionUseContext.id).where(
                PlanDefinitionUseContext.plan_definition_id == M.id, clause).exists())
        clause = token_clause(PlanDefinitionUseContext.code_system, PlanDefinitionUseContext.code_code, search.context_type)
        if clause is not None:
            stmt = stmt.where(select(PlanDefinitionUseContext.id).where(
                PlanDefinitionUseContext.plan_definition_id == M.id, clause).exists())

        # definition — action.definition[x] (a canonical like ".../ActivityDefinition/1" or a uri)
        for value in split_or(search.definition):
            A = PlanDefinitionAction
            stmt = stmt.where(select(A.id).where(
                A.plan_definition_id == M.id,
                or_(_canonical_match(A.definition_canonical, value), _canonical_match(A.definition_uri, value))).exists())

        # relatedArtifact.resource by relationship type (+ library for depends-on)
        R = PlanDefinitionRelatedArtifact
        for value, rtype in (
            (search.depends_on, RelatedArtifactType.depends_on),
            (search.derived_from, RelatedArtifactType.derived_from),
            (search.predecessor, RelatedArtifactType.predecessor),
            (search.successor, RelatedArtifactType.successor),
            (search.composed_of, RelatedArtifactType.composed_of),
        ):
            values = split_or(value)
            if not values:
                continue
            match_artifact = select(R.id).where(
                R.plan_definition_id == M.id, R.type == rtype, or_(*[_canonical_match(R.resource, v) for v in values])).exists()
            if rtype == RelatedArtifactType.depends_on:
                match_library = select(PlanDefinitionLibrary.id).where(
                    PlanDefinitionLibrary.plan_definition_id == M.id,
                    or_(*[_canonical_match(PlanDefinitionLibrary.canonical, v) for v in values])).exists()
                stmt = stmt.where(or_(match_artifact, match_library))
            else:
                stmt = stmt.where(match_artifact)

        for value in search.date or []:
            prefix, s_lo, s_hi = parse_date_param(value, "date")
            stmt = stmt.where(instant_clause(M.date, prefix, s_lo, s_hi))
        for value in search.effective or []:
            prefix, s_lo, s_hi = parse_date_param(value, "effective")
            stmt = stmt.where(period_date_clause(M.effective_period_start, M.effective_period_end, prefix, s_lo, s_hi))
        for value in search.last_updated or []:
            prefix, s_lo, s_hi = parse_date_param(value, "_lastUpdated")
            stmt = stmt.where(instant_clause(func.coalesce(M.updated_at, M.created_at), prefix, s_lo, s_hi))
        return stmt

    async def _search(
        self, user_id, org_id, search: Optional[PlanDefinitionSearch], limit: int, offset: int
    ) -> Tuple[List[PlanDefinitionModel], int]:
        async with self.session_factory() as session:
            base = self._apply_list_filters(_with_relationships(select(PlanDefinitionModel)), user_id, org_id, search)
            count_base = self._apply_list_filters(
                select(func.count()).select_from(PlanDefinitionModel), user_id, org_id, search)
            total = (await session.execute(count_base)).scalar_one()
            rows = list((await session.execute(
                base.order_by(
                    func.coalesce(PlanDefinitionModel.date, PlanDefinitionModel.created_at).desc().nulls_last(),
                    PlanDefinitionModel.id.desc(),
                ).offset(offset).limit(limit)
            )).scalars().all())
        return rows, total

    async def get_me(
        self, user_id: str, org_id: str, search: Optional[PlanDefinitionSearch] = None, limit: int = 50, offset: int = 0
    ) -> Tuple[List[PlanDefinitionModel], int]:
        return await self._search(user_id, org_id, search, limit, offset)

    async def list(
        self, user_id: Optional[str] = None, org_id: Optional[str] = None,
        search: Optional[PlanDefinitionSearch] = None, limit: int = 50, offset: int = 0,
    ) -> Tuple[List[PlanDefinitionModel], int]:
        return await self._search(user_id, org_id, search, limit, offset)

    # ── Create ────────────────────────────────────────────────────────────────

    async def create(
        self, payload: PlanDefinitionCreateSchema, user_id: Optional[str], org_id: Optional[str], created_by: Optional[str]
    ) -> PlanDefinitionModel:
        async with self.session_factory() as session:
            pd = PlanDefinitionModel(
                user_id=user_id, org_id=org_id, created_by=created_by,
                url=payload.url, version=payload.version, name=payload.name, title=payload.title,
                subtitle=payload.subtitle, status=payload.status, experimental=payload.experimental,
                date=payload.date, publisher=payload.publisher, description=payload.description,
                purpose=payload.purpose, usage=payload.usage, copyright=payload.copyright,
                approval_date=payload.approval_date, last_review_date=payload.last_review_date,
                effective_period_start=payload.effective_period_start, effective_period_end=payload.effective_period_end,
                **_names(payload, _cc_names("type")), **_names(payload, _cc_names("subject_cc")),
                **_ref_cols("subject_reference", payload.subject_reference, payload.subject_reference_display,
                            PlanDefinitionGroupReferenceType),
            )
            session.add(pd)
            _add_children(session, pd, payload, org_id)
            await session.commit()

            stmt = _with_relationships(select(PlanDefinitionModel).where(PlanDefinitionModel.id == pd.id))
            return (await session.execute(stmt)).scalars().one()

    # ── Patch ─────────────────────────────────────────────────────────────────

    async def patch(
        self, plan_definition_id: int, payload: PlanDefinitionPatchSchema, updated_by: Optional[str]
    ) -> Optional[PlanDefinitionModel]:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(PlanDefinitionModel).where(PlanDefinitionModel.plan_definition_id == plan_definition_id))
            pd = (await session.execute(stmt)).scalars().first()
            if not pd:
                return None

            updates = payload.model_dump(exclude_unset=True, exclude=set(CHILD_FIELDS))

            if "subject_reference" in updates:
                ref = updates.pop("subject_reference")
                if ref is None:
                    pd.subject_reference_type, pd.subject_reference_id = None, None
                    if "subject_reference_display" not in updates:
                        pd.subject_reference_display = None
                else:
                    pd.subject_reference_type, pd.subject_reference_id = _parse_ref(
                        ref, PlanDefinitionGroupReferenceType, "subject_reference")
            for name, value in updates.items():
                setattr(pd, name, value)
            pd.updated_by = updated_by

            replaced = [f for f in CHILD_FIELDS if f in payload.model_fields_set]

            # Referential integrity against the part of the plan that is NOT being replaced.
            try:
                stored_goal_ids = {g.element_id for g in pd.goals if g.element_id}
                if "action" in replaced and "goal" not in replaced:
                    validate_plan_tree(None, payload.action, known_goal_ids=stored_goal_ids)
                if "goal" in replaced and "action" not in replaced:
                    new_ids = {g.element_id for g in (payload.goal or []) if g.element_id}
                    dangling = {g.goal_element_id for g in pd.action_goal_ids} - new_ids
                    if dangling:
                        raise ValueError(f"Existing actions still refer to goal ids {sorted(dangling)}; replace `action` too.")
            except ValueError as exc:
                raise _unprocessable(str(exc))

            for f in replaced:
                _clear(pd, f)
            if replaced:
                await session.flush()
                _add_children(session, pd, _OnlyFields(payload, replaced), pd.org_id)

            await session.commit()
            stmt = _with_relationships(select(PlanDefinitionModel).where(PlanDefinitionModel.id == pd.id))
            return (await session.execute(stmt)).scalars().one()

    # ── Delete ────────────────────────────────────────────────────────────────

    async def delete(self, plan_definition_id: int) -> None:
        async with self.session_factory() as session:
            stmt = select(PlanDefinitionModel).where(PlanDefinitionModel.plan_definition_id == plan_definition_id)
            pd = (await session.execute(stmt)).scalars().first()
            if pd:
                await session.delete(pd)
                await session.commit()
