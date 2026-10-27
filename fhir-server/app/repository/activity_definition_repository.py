from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func, or_
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
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
from app.models.activity_definition.activity_definition import (
    ActivityDefinitionBodySite,
    ActivityDefinitionContact,
    ActivityDefinitionContactTelecom,
    ActivityDefinitionDosage,
    ActivityDefinitionDosageAdditionalInstruction,
    ActivityDefinitionDosageDoseAndRate,
    ActivityDefinitionDynamicValue,
    ActivityDefinitionIdentifier,
    ActivityDefinitionJurisdiction,
    ActivityDefinitionLibrary,
    ActivityDefinitionModel,
    ActivityDefinitionObservationRequirement,
    ActivityDefinitionObservationResultRequirement,
    ActivityDefinitionParticipant,
    ActivityDefinitionRelatedArtifact,
    ActivityDefinitionSpecimenRequirement,
    ActivityDefinitionTopic,
    ActivityDefinitionUseContext,
)
from app.models.activity_definition.enums import (
    ActivityDefinitionLocationReferenceType,
    ActivityDefinitionObservationReferenceType,
    ActivityDefinitionProductReferenceType,
    ActivityDefinitionSpecimenReferenceType,
    PlanDefinitionContactKind,
    PlanDefinitionGroupReferenceType,
    PlanDefinitionStatus,
    PlanDefinitionUseContextReferenceType,
    RelatedArtifactType,
)
from app.repository.plan_definition_repository import (
    _canonical_match,
    _cc_names,
    _csv,  # noqa: F401
    _names,
    _parse_ref,
    _ref_cols,
    _unprocessable,
)
from app.schemas.activity_definition import ActivityDefinitionCreateSchema, ActivityDefinitionPatchSchema

# String search params that support the `:exact` / `:contains` modifiers.
STRING_PARAMS = ("name", "title", "publisher", "description")


@dataclass
class ActivityDefinitionSearch:
    """FHIR R4 ActivityDefinition search parameters (https://www.hl7.org/fhir/R4/activitydefinition.html#search)."""

    id: Optional[str] = None                      # _id
    identifier: Optional[str] = None
    url: Optional[str] = None
    version: Optional[str] = None
    ad_status: Optional[str] = None
    topic: Optional[str] = None
    jurisdiction: Optional[str] = None
    context: Optional[str] = None
    context_type: Optional[str] = None
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
    """Eager-load every child table."""
    M = ActivityDefinitionModel
    return stmt.options(
        selectinload(M.identifiers),
        selectinload(M.contacts).selectinload(ActivityDefinitionContact.telecoms),
        selectinload(M.use_contexts),
        selectinload(M.jurisdictions),
        selectinload(M.topics),
        selectinload(M.related_artifacts),
        selectinload(M.libraries),
        selectinload(M.participants),
        selectinload(M.dosages).selectinload(ActivityDefinitionDosage.additional_instructions),
        selectinload(M.dosages).selectinload(ActivityDefinitionDosage.dose_and_rates),
        selectinload(M.body_sites),
        selectinload(M.specimen_requirements),
        selectinload(M.observation_requirements),
        selectinload(M.observation_result_requirements),
        selectinload(M.dynamic_values),
    )


# ── row builders (used by create AND patch) ────────────────────────────────────

_CONTACT_KINDS = ("contact", "author", "editor", "reviewer", "endorser")

# list field name -> (ORM collection attribute on the model)
_LIST_COLLECTIONS = {
    "identifier": "identifiers",
    "use_context": "use_contexts",
    "jurisdiction": "jurisdictions",
    "topic": "topics",
    "related_artifact": "related_artifacts",
    "library": "libraries",
    "participant": "participants",
    "dosage": "dosages",
    "body_site": "body_sites",
    "specimen_requirement": "specimen_requirements",
    "observation_requirement": "observation_requirements",
    "observation_result_requirement": "observation_result_requirements",
    "dynamic_value": "dynamic_values",
}

# Fields replaced as a unit by PATCH (and created by POST).
CHILD_FIELDS = tuple(_LIST_COLLECTIONS) + _CONTACT_KINDS


class _OnlyFields:
    """View of a payload exposing only the listed fields; every other attribute reads as None."""

    def __init__(self, payload, fields):
        self._payload = payload
        self._fields = set(fields)

    def __getattr__(self, name):
        return getattr(self._payload, name) if name in self._fields else None


def _ref_row(item, enum_cls, field_name: str) -> dict:
    """reference_type/_id/_display for a reference list entry."""
    t, i = _parse_ref(item.reference, enum_cls, field_name)
    return {"reference_type": t, "reference_id": i, "reference_display": item.reference_display}


def _add_dosages(session, ad, dosages, org_id) -> None:
    for d in dosages or []:
        row = ActivityDefinitionDosage(
            activity_definition=ad, org_id=org_id, sequence=d.sequence, text=d.text,
            patient_instruction=d.patient_instruction, as_needed_boolean=d.as_needed_boolean,
            **pack("timing", "timing", d.timing),
            **_names(d, _cc_names("as_needed")), **_names(d, _cc_names("site")),
            **_names(d, _cc_names("route")), **_names(d, _cc_names("method")),
            **pack("max_dose_per_period", "ratio", d.max_dose_per_period),
            **pack("max_dose_per_administration", "simple_quantity", d.max_dose_per_administration),
            **pack("max_dose_per_lifetime", "simple_quantity", d.max_dose_per_lifetime),
        )
        session.add(row)
        for a in d.additional_instruction or []:
            session.add(ActivityDefinitionDosageAdditionalInstruction(
                dosage=row, org_id=org_id, coding_system=a.coding_system, coding_code=a.coding_code,
                coding_display=a.coding_display, text=a.text))
        for r in d.dose_and_rate or []:
            session.add(ActivityDefinitionDosageDoseAndRate(
                dosage=row, org_id=org_id, **_names(r, _cc_names("type")),
                **pack("dose_range", "range", r.dose_range), **pack("dose_quantity", "simple_quantity", r.dose_quantity),
                **pack("rate_ratio", "ratio", r.rate_ratio), **pack("rate_range", "range", r.rate_range),
                **pack("rate_quantity", "simple_quantity", r.rate_quantity)))


def _add_children(session, ad, payload, org_id) -> None:
    """Create the child rows for every child list present on `payload` (None / missing = none)."""
    for i in payload.identifier or []:
        session.add(ActivityDefinitionIdentifier(
            activity_definition=ad, org_id=org_id, use=i.use, type_system=i.type_system, type_code=i.type_code,
            type_display=i.type_display, type_text=i.type_text, system=i.system, value=i.value,
            period_start=i.period_start, period_end=i.period_end, assigner=i.assigner))
    for kind in _CONTACT_KINDS:
        for c in getattr(payload, kind) or []:
            crow = ActivityDefinitionContact(
                activity_definition=ad, org_id=org_id, kind=PlanDefinitionContactKind(kind), name=c.name)
            session.add(crow)
            for t in c.telecom or []:
                session.add(ActivityDefinitionContactTelecom(
                    contact=crow, org_id=org_id, system=t.system, value=t.value, use=t.use, rank=t.rank,
                    period_start=t.period_start, period_end=t.period_end))
    for u in payload.use_context or []:
        session.add(ActivityDefinitionUseContext(
            activity_definition=ad, org_id=org_id, code_system=u.code_system, code_code=u.code_code,
            code_display=u.code_display, **_names(u, _cc_names("value_cc")),
            **{f"value_quantity_{s}": getattr(u, f"value_quantity_{s}") for s in ("value", "unit", "system", "code")},
            **{f"value_range_{b}_{s}": getattr(u, f"value_range_{b}_{s}") for b in ("low", "high") for s in ("value", "unit", "system", "code")},
            **_ref_cols("value_reference", u.value_reference, u.value_reference_display, PlanDefinitionUseContextReferenceType)))
    for j in payload.jurisdiction or []:
        session.add(ActivityDefinitionJurisdiction(
            activity_definition=ad, org_id=org_id, coding_system=j.coding_system, coding_code=j.coding_code,
            coding_display=j.coding_display, text=j.text))
    for t in payload.topic or []:
        session.add(ActivityDefinitionTopic(
            activity_definition=ad, org_id=org_id, coding_system=t.coding_system, coding_code=t.coding_code,
            coding_display=t.coding_display, text=t.text))
    for b in payload.body_site or []:
        session.add(ActivityDefinitionBodySite(
            activity_definition=ad, org_id=org_id, coding_system=b.coding_system, coding_code=b.coding_code,
            coding_display=b.coding_display, text=b.text))
    for a in payload.related_artifact or []:
        session.add(ActivityDefinitionRelatedArtifact(
            activity_definition=ad, org_id=org_id, type=a.type, label=a.label, display=a.display,
            citation=a.citation, url=a.url, resource=a.resource, **pack("document", "attachment", a.document)))
    for canonical in payload.library or []:
        session.add(ActivityDefinitionLibrary(activity_definition=ad, org_id=org_id, canonical=canonical))
    for p in payload.participant or []:
        session.add(ActivityDefinitionParticipant(
            activity_definition=ad, org_id=org_id, type=p.type, **_names(p, _cc_names("role"))))
    _add_dosages(session, ad, payload.dosage, org_id)
    for model, attr, enum_cls in (
        (ActivityDefinitionSpecimenRequirement, "specimen_requirement", ActivityDefinitionSpecimenReferenceType),
        (ActivityDefinitionObservationRequirement, "observation_requirement", ActivityDefinitionObservationReferenceType),
        (ActivityDefinitionObservationResultRequirement, "observation_result_requirement", ActivityDefinitionObservationReferenceType),
    ):
        for item in getattr(payload, attr) or []:
            session.add(model(activity_definition=ad, org_id=org_id, **_ref_row(item, enum_cls, attr)))
    for d in payload.dynamic_value or []:
        session.add(ActivityDefinitionDynamicValue(
            activity_definition=ad, org_id=org_id, path=d.path, **pack("expression", "expression", d.expression)))


def _clear(ad, field_name: str) -> None:
    """Remove the stored rows behind one child-list field (delete-orphan deletes them)."""
    if field_name in _CONTACT_KINDS:
        for c in [c for c in ad.contacts if getattr(c.kind, "value", c.kind) == field_name]:
            ad.contacts.remove(c)
    else:
        getattr(ad, _LIST_COLLECTIONS[field_name]).clear()


# Scalar reference columns: input field -> (column prefix, allowed-type enum)
_REFS = {
    "subject_reference": ("subject_reference", PlanDefinitionGroupReferenceType),
    "location": ("location", ActivityDefinitionLocationReferenceType),
    "product_reference": ("product_reference", ActivityDefinitionProductReferenceType),
}

# Nested-datatype input field -> codec kind (stored in flat `<field>_*` columns)
_NESTED = {
    "timing_age": "quantity",
    "timing_period": "period",
    "timing_range": "range",
    "timing_duration": "quantity",
    "timing_timing": "timing",
    "quantity": "simple_quantity",
}

# Choice-type groups: setting one variant clears the others (column prefixes).
_CHOICES = (
    ("timing_datetime", "timing_age_", "timing_period_", "timing_range_", "timing_duration_", "timing_timing_"),
    ("subject_cc_", "subject_reference_"),
    ("product_reference_", "product_cc_"),
)


def _clear_columns(ad, prefix: str) -> None:
    """Null every column of the main table whose name starts with `prefix` (or equals it)."""
    for c in ActivityDefinitionModel.__table__.columns:
        if c.name == prefix or (prefix.endswith("_") and c.name.startswith(prefix)):
            setattr(ad, c.key, None)


def _canonical_or(col, values):
    return or_(*[_canonical_match(col, v) for v in values])


class ActivityDefinitionRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    # ── Read ──────────────────────────────────────────────────────────────────

    async def get_by_activity_definition_id(self, activity_definition_id: int) -> Optional[ActivityDefinitionModel]:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(ActivityDefinitionModel).where(ActivityDefinitionModel.activity_definition_id == activity_definition_id)
            )
            return (await session.execute(stmt)).scalars().first()

    async def find_for_apply(
        self, org_id: str, public_id: Optional[int] = None, url: Optional[str] = None
    ) -> Optional[ActivityDefinitionModel]:
        """Resolve an action's definition inside one tenant, by public id or by canonical url (latest row wins)."""
        if public_id is None and not url:
            return None
        M = ActivityDefinitionModel
        stmt = select(M).where(M.org_id == org_id)
        stmt = stmt.where(M.activity_definition_id == public_id) if public_id is not None else stmt.where(M.url == url)
        async with self.session_factory() as session:
            return (await session.execute(_with_relationships(stmt.order_by(M.id.desc())))).scalars().first()

    def _apply_list_filters(self, stmt, user_id, org_id, search: Optional[ActivityDefinitionSearch] = None):
        """user_id/org_id are tenant filters; `search` carries the FHIR R4 search parameters."""
        if user_id:
            stmt = stmt.where(ActivityDefinitionModel.user_id == user_id)
        if org_id:
            stmt = stmt.where(ActivityDefinitionModel.org_id == org_id)
        if search is None:
            return stmt
        M = ActivityDefinitionModel

        if search.id:
            ids = []
            for v in split_or(search.id):
                try:
                    ids.append(int(v))
                except ValueError:
                    raise _unprocessable(f"Invalid _id '{v}'. Must be an integer.")
            stmt = stmt.where(M.activity_definition_id.in_(ids))

        clause = token_clause(ActivityDefinitionIdentifier.system, ActivityDefinitionIdentifier.value, search.identifier)
        if clause is not None:
            stmt = stmt.where(select(ActivityDefinitionIdentifier.id).where(
                ActivityDefinitionIdentifier.activity_definition_id == M.id, clause).exists())

        urls = split_or(search.url)
        if urls:
            stmt = stmt.where(M.url.in_(urls))
        versions = split_or(search.version)
        if versions:
            stmt = stmt.where(M.version.in_(versions))

        statuses = enum_token_values(search.ad_status, PlanDefinitionStatus, "status")
        if statuses:
            stmt = stmt.where(M.status.in_(statuses))

        for name in STRING_PARAMS:
            for mode, value in (search.strings.get(name) or {}).items():
                clause = string_clause(getattr(M, name), value, mode)
                if clause is not None:
                    stmt = stmt.where(clause)

        for value, model in ((search.topic, ActivityDefinitionTopic), (search.jurisdiction, ActivityDefinitionJurisdiction)):
            clause = token_clause(model.coding_system, model.coding_code, value)
            if clause is not None:
                stmt = stmt.where(select(model.id).where(model.activity_definition_id == M.id, clause).exists())

        U = ActivityDefinitionUseContext
        clause = token_clause(U.value_cc_system, U.value_cc_code, search.context)
        if clause is not None:
            stmt = stmt.where(select(U.id).where(U.activity_definition_id == M.id, clause).exists())
        clause = token_clause(U.code_system, U.code_code, search.context_type)
        if clause is not None:
            stmt = stmt.where(select(U.id).where(U.activity_definition_id == M.id, clause).exists())

        # relatedArtifact.resource by relationship type (+ library for depends-on)
        R = ActivityDefinitionRelatedArtifact
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
                R.activity_definition_id == M.id, R.type == rtype, _canonical_or(R.resource, values)).exists()
            if rtype == RelatedArtifactType.depends_on:
                L = ActivityDefinitionLibrary
                match_library = select(L.id).where(
                    L.activity_definition_id == M.id, _canonical_or(L.canonical, values)).exists()
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
        self, user_id, org_id, search: Optional[ActivityDefinitionSearch], limit: int, offset: int
    ) -> Tuple[List[ActivityDefinitionModel], int]:
        async with self.session_factory() as session:
            base = self._apply_list_filters(_with_relationships(select(ActivityDefinitionModel)), user_id, org_id, search)
            count_base = self._apply_list_filters(
                select(func.count()).select_from(ActivityDefinitionModel), user_id, org_id, search)
            total = (await session.execute(count_base)).scalar_one()
            rows = list((await session.execute(
                base.order_by(
                    func.coalesce(ActivityDefinitionModel.date, ActivityDefinitionModel.created_at).desc().nulls_last(),
                    ActivityDefinitionModel.id.desc(),
                ).offset(offset).limit(limit)
            )).scalars().all())
        return rows, total

    async def get_me(
        self, user_id: str, org_id: str, search: Optional[ActivityDefinitionSearch] = None, limit: int = 50, offset: int = 0
    ) -> Tuple[List[ActivityDefinitionModel], int]:
        return await self._search(user_id, org_id, search, limit, offset)

    async def list(
        self, user_id: Optional[str] = None, org_id: Optional[str] = None,
        search: Optional[ActivityDefinitionSearch] = None, limit: int = 50, offset: int = 0,
    ) -> Tuple[List[ActivityDefinitionModel], int]:
        return await self._search(user_id, org_id, search, limit, offset)

    # ── Create ────────────────────────────────────────────────────────────────

    async def create(
        self, payload: ActivityDefinitionCreateSchema, user_id: Optional[str], org_id: Optional[str], created_by: Optional[str]
    ) -> ActivityDefinitionModel:
        async with self.session_factory() as session:
            scalars = {
                n: getattr(payload, n) for n in (
                    "url", "version", "name", "title", "subtitle", "status", "experimental", "date", "publisher",
                    "description", "purpose", "usage", "copyright", "approval_date", "last_review_date",
                    "effective_period_start", "effective_period_end", "kind", "profile", "intent", "priority",
                    "do_not_perform", "timing_datetime", "transform",
                )
            }
            ad = ActivityDefinitionModel(
                user_id=user_id, org_id=org_id, created_by=created_by, **scalars,
                **_names(payload, _cc_names("subject_cc")), **_names(payload, _cc_names("code")),
                **_names(payload, _cc_names("product_cc")),
                **_ref_cols("subject_reference", payload.subject_reference, payload.subject_reference_display,
                            PlanDefinitionGroupReferenceType),
                **_ref_cols("location", payload.location, payload.location_display, ActivityDefinitionLocationReferenceType),
                **_ref_cols("product_reference", payload.product_reference, payload.product_reference_display,
                            ActivityDefinitionProductReferenceType),
                **pack("timing_age", "quantity", payload.timing_age), **pack("timing_period", "period", payload.timing_period),
                **pack("timing_range", "range", payload.timing_range),
                **pack("timing_duration", "quantity", payload.timing_duration),
                **pack("timing_timing", "timing", payload.timing_timing),
                **pack("quantity", "simple_quantity", payload.quantity),
            )
            session.add(ad)
            _add_children(session, ad, payload, org_id)
            await session.commit()

            stmt = _with_relationships(select(ActivityDefinitionModel).where(ActivityDefinitionModel.id == ad.id))
            return (await session.execute(stmt)).scalars().one()

    # ── Patch ─────────────────────────────────────────────────────────────────

    async def patch(
        self, activity_definition_id: int, payload: ActivityDefinitionPatchSchema, updated_by: Optional[str]
    ) -> Optional[ActivityDefinitionModel]:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(ActivityDefinitionModel).where(ActivityDefinitionModel.activity_definition_id == activity_definition_id))
            ad = (await session.execute(stmt)).scalars().first()
            if not ad:
                return None

            updates = payload.model_dump(exclude_unset=True, exclude=set(CHILD_FIELDS))

            # choice[x]: setting one variant clears the others
            def _in(k, g):
                return k == g or (g.endswith("_") and (k == g[:-1] or k.startswith(g)))

            for group in _CHOICES:
                touched = [
                    k for k, v in updates.items()
                    if v is not None and not k.endswith("_reference_display") and any(_in(k, g) for g in group)
                ]
                if touched:
                    for g in group:
                        if not any(_in(k, g) for k in touched):
                            _clear_columns(ad, g)

            for key, (prefix, enum_cls) in _REFS.items():
                if key in updates:
                    ref = updates.pop(key)
                    if ref is None:
                        setattr(ad, f"{prefix}_type", None)
                        setattr(ad, f"{prefix}_id", None)
                        if f"{prefix}_display" not in updates:
                            setattr(ad, f"{prefix}_display", None)
                    else:
                        t, i = _parse_ref(ref, enum_cls, key)
                        setattr(ad, f"{prefix}_type", t)
                        setattr(ad, f"{prefix}_id", i)
            for key, kind in _NESTED.items():
                if key in updates:
                    value = updates.pop(key)
                    _clear_columns(ad, key + "_")
                    for col_name, v in pack(key, kind, value).items():
                        setattr(ad, col_name, v)
            for name, value in updates.items():
                setattr(ad, name, value)
            ad.updated_by = updated_by

            replaced = [f for f in CHILD_FIELDS if f in payload.model_fields_set]
            for f in replaced:
                _clear(ad, f)
            if replaced:
                await session.flush()
                _add_children(session, ad, _OnlyFields(payload, replaced), ad.org_id)

            await session.commit()
            stmt = _with_relationships(select(ActivityDefinitionModel).where(ActivityDefinitionModel.id == ad.id))
            return (await session.execute(stmt)).scalars().one()

    # ── Delete ────────────────────────────────────────────────────────────────

    async def delete(self, activity_definition_id: int) -> None:
        async with self.session_factory() as session:
            stmt = select(ActivityDefinitionModel).where(
                ActivityDefinitionModel.activity_definition_id == activity_definition_id)
            ad = (await session.execute(stmt)).scalars().first()
            if ad:
                await session.delete(ad)
                await session.commit()
