from dataclasses import dataclass, field
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
    parse_reference_param,
    period_date_clause,
    reference_clause,
    split_or,
    token_clause,
)
from app.models.care_plan.enums import (
    CarePlanActivityReferenceType,
    CarePlanAddressesReferenceType,
    CarePlanAuthorReferenceType,
    CarePlanBasedOnReferenceType,
    CarePlanCareTeamReferenceType,
    CarePlanContributorReferenceType,
    CarePlanDetailActivityStatus,
    CarePlanDetailGoalReferenceType,
    CarePlanDetailLocationReferenceType,
    CarePlanDetailPerformerReferenceType,
    CarePlanDetailProductReferenceType,
    CarePlanDetailReasonReferenceType,
    CarePlanGoalReferenceType,
    CarePlanIntent,
    CarePlanPartOfReferenceType,
    CarePlanReplacesReferenceType,
    CarePlanStatus,
    CarePlanSubjectReferenceType,
)
from app.models.enums import EncounterReferenceType
from app.models.care_plan.care_plan import (
    CarePlanActivity,
    CarePlanActivityDetailGoal,
    CarePlanActivityDetailPerformer,
    CarePlanActivityDetailReasonCode,
    CarePlanActivityDetailReasonRef,
    CarePlanActivityOutcomeCC,
    CarePlanActivityOutcomeRef,
    CarePlanActivityProgress,
    CarePlanAddresses,
    CarePlanBasedOn,
    CarePlanCareTeam,
    CarePlanCategory,
    CarePlanContributor,
    CarePlanGoal,
    CarePlanIdentifier,
    CarePlanModel,
    CarePlanNote,
    CarePlanPartOf,
    CarePlanReplaces,
    CarePlanSupportingInfo,
)
from app.schemas.care_plan.input import CarePlanCreateSchema, CarePlanPatchSchema

# activity.detail.scheduled timing bounds[x] Duration / Range columns (flat)
_BOUNDS_FIELDS = tuple(
    [f"detail_scheduled_timing_repeat_bounds_duration_{f}" for f in ("value", "comparator", "unit", "system", "code")]
    + [f"detail_scheduled_timing_repeat_bounds_range_{b}_{f}" for b in ("low", "high") for f in ("value", "unit", "system", "code")]
)


@dataclass
class CarePlanSearch:
    """FHIR R4 CarePlan search parameters (https://www.hl7.org/fhir/R4/careplan.html#search)."""

    id: Optional[str] = None                      # _id
    identifier: Optional[str] = None
    cp_status: Optional[str] = None
    intent: Optional[str] = None
    category: Optional[str] = None
    activity_code: Optional[str] = None
    activity_reference: Optional[str] = None
    based_on: Optional[str] = None
    replaces: Optional[str] = None
    part_of: Optional[str] = None
    care_team: Optional[str] = None
    condition: Optional[str] = None
    goal: Optional[str] = None
    encounter: Optional[str] = None
    subject: Optional[str] = None
    patient: Optional[str] = None
    performer: Optional[str] = None
    instantiates_canonical: Optional[str] = None
    instantiates_uri: Optional[str] = None
    date: List[str] = field(default_factory=list)
    activity_date: List[str] = field(default_factory=list)
    last_updated: List[str] = field(default_factory=list)   # _lastUpdated


def _csv_member(col, value: str):
    """Match one value inside a comma-separated column; also matches when the stored item ends with '/<value>'."""
    return or_(
        col == value, col.like(f"{value},%"), col.like(f"%,{value}"), col.like(f"%,{value},%"),
        col.like(f"%/{value}"), col.like(f"%/{value},%"),
    )


def _with_relationships(stmt):
    return stmt.options(
        selectinload(CarePlanModel.identifiers),
        selectinload(CarePlanModel.based_on),
        selectinload(CarePlanModel.replaces),
        selectinload(CarePlanModel.part_of),
        selectinload(CarePlanModel.categories),
        selectinload(CarePlanModel.contributors),
        selectinload(CarePlanModel.care_teams),
        selectinload(CarePlanModel.addresses),
        selectinload(CarePlanModel.supporting_info),
        selectinload(CarePlanModel.goals),
        selectinload(CarePlanModel.notes),
        selectinload(CarePlanModel.activities).selectinload(CarePlanActivity.outcome_codeable_concepts),
        selectinload(CarePlanModel.activities).selectinload(CarePlanActivity.outcome_references),
        selectinload(CarePlanModel.activities).selectinload(CarePlanActivity.progress),
        selectinload(CarePlanModel.activities).selectinload(CarePlanActivity.detail_reason_codes),
        selectinload(CarePlanModel.activities).selectinload(CarePlanActivity.detail_reason_references),
        selectinload(CarePlanModel.activities).selectinload(CarePlanActivity.detail_goals),
        selectinload(CarePlanModel.activities).selectinload(CarePlanActivity.detail_performers),
    )


class _OnlyFields:
    """View of a payload exposing only the listed fields; every other attribute reads as None."""

    def __init__(self, payload, fields):
        self._payload = payload
        self._fields = set(fields)

    def __getattr__(self, name):
        return getattr(self._payload, name) if name in self._fields else None


# payload list field -> ORM collection attribute on CarePlanModel
_COLLECTIONS = {
    "identifiers": "identifiers", "based_on": "based_on", "replaces": "replaces", "part_of": "part_of",
    "categories": "categories", "contributors": "contributors", "care_teams": "care_teams",
    "addresses": "addresses", "supporting_info": "supporting_info", "goals": "goals",
    "activities": "activities", "notes": "notes",
}
CHILD_FIELDS = tuple(_COLLECTIONS)


def _parse_ref_closed(ref: str, enum_cls, field: str):
    parts = ref.split("/", 1)
    if len(parts) != 2:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid reference format: '{ref}'. Expected 'ResourceType/id'.",
        )
    try:
        ref_id = int(parts[1])
    except ValueError:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid reference id in: '{ref}'. Id must be an integer.",
        )
    try:
        ref_type = enum_cls(parts[0])
    except ValueError:
        allowed = [e.value for e in enum_cls]
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid reference type '{parts[0]}' for {field}. Allowed: {allowed}.",
        )
    return ref_type, ref_id


def _parse_ref_open(ref: str, field: str):
    parts = ref.split("/", 1)
    if len(parts) != 2:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid reference format: '{ref}'. Expected 'ResourceType/id'.",
        )
    try:
        ref_id = int(parts[1])
    except ValueError:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid reference id in: '{ref}'. Id must be an integer.",
        )
    return parts[0], ref_id


def _parse_ref_closed_opt(ref: Optional[str], enum_cls, field: str):
    if not ref:
        return None, None
    return _parse_ref_closed(ref, enum_cls, field)


def _parse_ref_open_opt(ref: Optional[str], field: str):
    if not ref:
        return None, None
    return _parse_ref_open(ref, field)


def _cast_status(v) -> Optional[str]:
    if v is None:
        return None
    try:
        return CarePlanStatus(v).value
    except ValueError:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status '{v}'. Allowed: {[e.value for e in CarePlanStatus]}.",
        )


def _cast_intent(v) -> Optional[str]:
    if v is None:
        return None
    try:
        return CarePlanIntent(v).value
    except ValueError:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid intent '{v}'. Allowed: {[e.value for e in CarePlanIntent]}.",
        )


def _cast_detail_status(v) -> Optional[str]:
    if v is None:
        return None
    try:
        return CarePlanDetailActivityStatus(v).value
    except ValueError:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid detail_status '{v}'. Allowed: {[e.value for e in CarePlanDetailActivityStatus]}.",
        )


class CarePlanRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    async def get_by_care_plan_id(self, care_plan_id: int) -> Optional[CarePlanModel]:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(CarePlanModel).where(CarePlanModel.care_plan_id == care_plan_id)
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    def _apply_list_filters(self, stmt, user_id, org_id, search: Optional[CarePlanSearch] = None):
        """user_id/org_id are tenant filters; `search` carries the FHIR R4 search parameters."""
        if user_id:
            stmt = stmt.where(CarePlanModel.user_id == user_id)
        if org_id:
            stmt = stmt.where(CarePlanModel.org_id == org_id)
        if search is None:
            return stmt
        M = CarePlanModel

        if search.id:
            ids = []
            for v in split_or(search.id):
                try:
                    ids.append(int(v))
                except ValueError:
                    raise HTTPException(
                        status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid _id '{v}'. Must be an integer.")
            stmt = stmt.where(M.care_plan_id.in_(ids))

        clause = token_clause(CarePlanIdentifier.system, CarePlanIdentifier.value, search.identifier)
        if clause is not None:
            stmt = stmt.where(select(CarePlanIdentifier.id).where(CarePlanIdentifier.care_plan_id == M.id, clause).exists())
        statuses = enum_token_values(search.cp_status, CarePlanStatus, "status")
        if statuses:
            stmt = stmt.where(M.status.in_(statuses))
        intents = enum_token_values(search.intent, CarePlanIntent, "intent")
        if intents:
            stmt = stmt.where(M.intent.in_(intents))
        clause = token_clause(CarePlanCategory.coding_system, CarePlanCategory.coding_code, search.category)
        if clause is not None:
            stmt = stmt.where(select(CarePlanCategory.id).where(CarePlanCategory.care_plan_id == M.id, clause).exists())

        A = CarePlanActivity
        clause = token_clause(A.detail_code_system, A.detail_code_code, search.activity_code)
        if clause is not None:
            stmt = stmt.where(select(A.id).where(A.care_plan_id == M.id, clause).exists())
        if search.activity_reference:
            clause = reference_clause(
                A.reference_type, A.reference_id,
                parse_reference_param(search.activity_reference, CarePlanActivityReferenceType, "activity-reference"))
            stmt = stmt.where(select(A.id).where(A.care_plan_id == M.id, clause).exists())

        # reference lists living in child tables
        for value, model, enum_cls, name in (
            (search.based_on, CarePlanBasedOn, CarePlanBasedOnReferenceType, "based-on"),
            (search.replaces, CarePlanReplaces, CarePlanReplacesReferenceType, "replaces"),
            (search.part_of, CarePlanPartOf, CarePlanPartOfReferenceType, "part-of"),
            (search.care_team, CarePlanCareTeam, CarePlanCareTeamReferenceType, "care-team"),
            (search.condition, CarePlanAddresses, CarePlanAddressesReferenceType, "condition"),
            (search.goal, CarePlanGoal, CarePlanGoalReferenceType, "goal"),
        ):
            if value:
                clause = reference_clause(model.reference_type, model.reference_id, parse_reference_param(value, enum_cls, name))
                stmt = stmt.where(select(model.id).where(model.care_plan_id == M.id, clause).exists())
        if search.performer:
            P = CarePlanActivityDetailPerformer
            clause = reference_clause(
                P.reference_type, P.reference_id,
                parse_reference_param(search.performer, CarePlanDetailPerformerReferenceType, "performer"))
            stmt = stmt.where(
                select(P.id).join(A, A.id == P.activity_id).where(A.care_plan_id == M.id, clause).exists())

        # scalar references on the plan
        if search.subject:
            stmt = stmt.where(reference_clause(
                M.subject_type, M.subject_id, parse_reference_param(search.subject, CarePlanSubjectReferenceType, "subject")))
        if search.patient:
            refs = [
                (CarePlanSubjectReferenceType.Patient, rid)
                for rtype, rid in parse_reference_param(search.patient, CarePlanSubjectReferenceType, "patient")
                if rtype in (None, CarePlanSubjectReferenceType.Patient)
            ]
            stmt = stmt.where(reference_clause(M.subject_type, M.subject_id, refs) if refs else M.id.is_(None))
        if search.encounter:
            stmt = stmt.where(reference_clause(
                M.encounter_type, M.encounter_id, parse_reference_param(search.encounter, EncounterReferenceType, "encounter")))

        # canonical / uri lists stored comma-separated
        for value in split_or(search.instantiates_canonical):
            stmt = stmt.where(_csv_member(M.instantiates_canonical, value))
        for value in split_or(search.instantiates_uri):
            stmt = stmt.where(_csv_member(M.instantiates_uri, value))

        for value in search.date or []:
            prefix, s_lo, s_hi = parse_date_param(value, "date")
            stmt = stmt.where(period_date_clause(M.period_start, M.period_end, prefix, s_lo, s_hi))
        for value in search.activity_date or []:
            prefix, s_lo, s_hi = parse_date_param(value, "activity-date")
            lo = func.coalesce(A.detail_scheduled_period_start, A.detail_scheduled_timing_repeat_bounds_start)
            hi = func.coalesce(A.detail_scheduled_period_end, A.detail_scheduled_timing_repeat_bounds_end)
            stmt = stmt.where(select(A.id).where(
                A.care_plan_id == M.id, period_date_clause(lo, hi, prefix, s_lo, s_hi)).exists())
        for value in search.last_updated or []:
            prefix, s_lo, s_hi = parse_date_param(value, "_lastUpdated")
            stmt = stmt.where(instant_clause(func.coalesce(M.updated_at, M.created_at), prefix, s_lo, s_hi))
        return stmt

    async def _search(self, user_id, org_id, search, limit: int, offset: int) -> Tuple[List[CarePlanModel], int]:
        async with self.session_factory() as session:
            base = self._apply_list_filters(_with_relationships(select(CarePlanModel)), user_id, org_id, search)
            count_base = self._apply_list_filters(select(func.count()).select_from(CarePlanModel), user_id, org_id, search)
            total = (await session.execute(count_base)).scalar_one()
            rows = list((await session.execute(
                base.order_by(
                    func.coalesce(CarePlanModel.created, CarePlanModel.created_at).desc().nulls_last(),
                    CarePlanModel.id.desc(),
                ).offset(offset).limit(limit)
            )).scalars().all())
        return rows, total

    async def get_me(
        self, user_id: str, org_id: str, search: Optional[CarePlanSearch] = None, limit: int = 50, offset: int = 0
    ) -> Tuple[List[CarePlanModel], int]:
        return await self._search(user_id, org_id, search, limit, offset)

    async def list(
        self, user_id: Optional[str] = None, org_id: Optional[str] = None,
        search: Optional[CarePlanSearch] = None, limit: int = 50, offset: int = 0,
    ) -> Tuple[List[CarePlanModel], int]:
        return await self._search(user_id, org_id, search, limit, offset)

    def _build_activity_grandchildren(self, session, activity, org_id, item):
        for oc in (item.outcome_codeable_concepts or []):
            session.add(CarePlanActivityOutcomeCC(
                activity=activity, org_id=org_id,
                coding_system=oc.coding_system, coding_code=oc.coding_code,
                coding_display=oc.coding_display, text=oc.text,
            ))
        for oref in (item.outcome_references or []):
            ref_type, ref_id = _parse_ref_open(oref.reference, "outcome_references.reference")
            session.add(CarePlanActivityOutcomeRef(
                activity=activity, org_id=org_id,
                reference_type=ref_type, reference_id=ref_id, reference_display=oref.reference_display,
            ))
        for prog in (item.progress or []):
            auth_type, auth_id = _parse_ref_open_opt(prog.author_reference, "progress.author_reference")
            session.add(CarePlanActivityProgress(
                activity=activity, org_id=org_id,
                text=prog.text, time=prog.time, author_string=prog.author_string,
                author_reference_type=auth_type, author_reference_id=auth_id,
                author_reference_display=prog.author_reference_display,
            ))
        for rc in (item.detail_reason_codes or []):
            session.add(CarePlanActivityDetailReasonCode(
                activity=activity, org_id=org_id,
                coding_system=rc.coding_system, coding_code=rc.coding_code,
                coding_display=rc.coding_display, text=rc.text,
            ))
        for rref in (item.detail_reason_references or []):
            ref_type, ref_id = _parse_ref_closed(rref.reference, CarePlanDetailReasonReferenceType, "detail_reason_references.reference")
            session.add(CarePlanActivityDetailReasonRef(
                activity=activity, org_id=org_id,
                reference_type=ref_type, reference_id=ref_id, reference_display=rref.reference_display,
            ))
        for g in (item.detail_goals or []):
            ref_type, ref_id = _parse_ref_closed(g.reference, CarePlanDetailGoalReferenceType, "detail_goals.reference")
            session.add(CarePlanActivityDetailGoal(
                activity=activity, org_id=org_id,
                reference_type=ref_type, reference_id=ref_id, reference_display=g.reference_display,
            ))
        for p in (item.detail_performers or []):
            ref_type, ref_id = _parse_ref_closed(p.reference, CarePlanDetailPerformerReferenceType, "detail_performers.reference")
            session.add(CarePlanActivityDetailPerformer(
                activity=activity, org_id=org_id,
                reference_type=ref_type, reference_id=ref_id, reference_display=p.reference_display,
            ))

    def _build_children(self, session, care_plan, org_id, payload):
        for item in (payload.identifiers or []):
            session.add(CarePlanIdentifier(
                care_plan=care_plan, org_id=org_id,
                use=item.use, type_system=item.type_system, type_code=item.type_code,
                type_display=item.type_display, type_text=item.type_text,
                system=item.system, value=item.value,
                period_start=item.period_start, period_end=item.period_end, assigner=item.assigner,
            ))
        for item in (payload.based_on or []):
            ref_type, ref_id = _parse_ref_closed(item.reference, CarePlanBasedOnReferenceType, "based_on.reference")
            session.add(CarePlanBasedOn(
                care_plan=care_plan, org_id=org_id,
                reference_type=ref_type, reference_id=ref_id, reference_display=item.reference_display,
            ))
        for item in (payload.replaces or []):
            ref_type, ref_id = _parse_ref_closed(item.reference, CarePlanReplacesReferenceType, "replaces.reference")
            session.add(CarePlanReplaces(
                care_plan=care_plan, org_id=org_id,
                reference_type=ref_type, reference_id=ref_id, reference_display=item.reference_display,
            ))
        for item in (payload.part_of or []):
            ref_type, ref_id = _parse_ref_closed(item.reference, CarePlanPartOfReferenceType, "part_of.reference")
            session.add(CarePlanPartOf(
                care_plan=care_plan, org_id=org_id,
                reference_type=ref_type, reference_id=ref_id, reference_display=item.reference_display,
            ))
        for item in (payload.categories or []):
            session.add(CarePlanCategory(
                care_plan=care_plan, org_id=org_id,
                coding_system=item.coding_system, coding_code=item.coding_code,
                coding_display=item.coding_display, text=item.text,
            ))
        for item in (payload.contributors or []):
            ref_type, ref_id = _parse_ref_closed(item.reference, CarePlanContributorReferenceType, "contributors.reference")
            session.add(CarePlanContributor(
                care_plan=care_plan, org_id=org_id,
                reference_type=ref_type, reference_id=ref_id, reference_display=item.reference_display,
            ))
        for item in (payload.care_teams or []):
            ref_type, ref_id = _parse_ref_closed(item.reference, CarePlanCareTeamReferenceType, "care_teams.reference")
            session.add(CarePlanCareTeam(
                care_plan=care_plan, org_id=org_id,
                reference_type=ref_type, reference_id=ref_id, reference_display=item.reference_display,
            ))
        for item in (payload.addresses or []):
            ref_type, ref_id = _parse_ref_closed(item.reference, CarePlanAddressesReferenceType, "addresses.reference")
            session.add(CarePlanAddresses(
                care_plan=care_plan, org_id=org_id,
                reference_type=ref_type, reference_id=ref_id, reference_display=item.reference_display,
            ))
        for item in (payload.supporting_info or []):
            ref_type, ref_id = _parse_ref_open(item.reference, "supporting_info.reference")
            session.add(CarePlanSupportingInfo(
                care_plan=care_plan, org_id=org_id,
                reference_type=ref_type, reference_id=ref_id, reference_display=item.reference_display,
            ))
        for item in (payload.goals or []):
            ref_type, ref_id = _parse_ref_closed(item.reference, CarePlanGoalReferenceType, "goals.reference")
            session.add(CarePlanGoal(
                care_plan=care_plan, org_id=org_id,
                reference_type=ref_type, reference_id=ref_id, reference_display=item.reference_display,
            ))
        for item in (payload.notes or []):
            auth_type, auth_id = _parse_ref_open_opt(item.author_reference, "notes.author_reference")
            session.add(CarePlanNote(
                care_plan=care_plan, org_id=org_id,
                text=item.text, time=item.time, author_string=item.author_string,
                author_reference_type=auth_type, author_reference_id=auth_id,
                author_reference_display=item.author_reference_display,
            ))
        for item in (payload.activities or []):
            act_ref_type, act_ref_id = _parse_ref_closed_opt(item.reference, CarePlanActivityReferenceType, "activities.reference")
            loc_type, loc_id = _parse_ref_closed_opt(item.detail_location, CarePlanDetailLocationReferenceType, "detail_location")
            prod_ref_type, prod_ref_id = _parse_ref_closed_opt(item.detail_product_reference, CarePlanDetailProductReferenceType, "detail_product_reference")

            activity = CarePlanActivity(
                care_plan=care_plan, org_id=org_id,
                reference_type=act_ref_type, reference_id=act_ref_id, reference_display=item.reference_display,
                detail_kind=item.detail_kind.value if item.detail_kind is not None else None,
                detail_instantiates_canonical=item.detail_instantiates_canonical,
                detail_instantiates_uri=item.detail_instantiates_uri,
                detail_code_system=item.detail_code_system,
                detail_code_code=item.detail_code_code,
                detail_code_display=item.detail_code_display,
                detail_code_text=item.detail_code_text,
                detail_status=_cast_detail_status(item.detail_status),
                detail_status_reason_system=item.detail_status_reason_system,
                detail_status_reason_code=item.detail_status_reason_code,
                detail_status_reason_display=item.detail_status_reason_display,
                detail_status_reason_text=item.detail_status_reason_text,
                detail_do_not_perform=item.detail_do_not_perform,
                detail_scheduled_timing_event=item.detail_scheduled_timing_event,
                detail_scheduled_timing_code_system=item.detail_scheduled_timing_code_system,
                detail_scheduled_timing_code_code=item.detail_scheduled_timing_code_code,
                detail_scheduled_timing_code_display=item.detail_scheduled_timing_code_display,
                detail_scheduled_timing_code_text=item.detail_scheduled_timing_code_text,
                detail_scheduled_timing_repeat_count=item.detail_scheduled_timing_repeat_count,
                detail_scheduled_timing_repeat_count_max=item.detail_scheduled_timing_repeat_count_max,
                detail_scheduled_timing_repeat_duration=item.detail_scheduled_timing_repeat_duration,
                detail_scheduled_timing_repeat_duration_max=item.detail_scheduled_timing_repeat_duration_max,
                detail_scheduled_timing_repeat_duration_unit=item.detail_scheduled_timing_repeat_duration_unit,
                detail_scheduled_timing_repeat_frequency=item.detail_scheduled_timing_repeat_frequency,
                detail_scheduled_timing_repeat_frequency_max=item.detail_scheduled_timing_repeat_frequency_max,
                detail_scheduled_timing_repeat_period=item.detail_scheduled_timing_repeat_period,
                detail_scheduled_timing_repeat_period_max=item.detail_scheduled_timing_repeat_period_max,
                detail_scheduled_timing_repeat_period_unit=item.detail_scheduled_timing_repeat_period_unit,
                detail_scheduled_timing_repeat_day_of_week=item.detail_scheduled_timing_repeat_day_of_week,
                detail_scheduled_timing_repeat_time_of_day=item.detail_scheduled_timing_repeat_time_of_day,
                detail_scheduled_timing_repeat_when=item.detail_scheduled_timing_repeat_when,
                detail_scheduled_timing_repeat_offset=item.detail_scheduled_timing_repeat_offset,
                detail_scheduled_timing_repeat_bounds_start=item.detail_scheduled_timing_repeat_bounds_start,
                detail_scheduled_timing_repeat_bounds_end=item.detail_scheduled_timing_repeat_bounds_end,
                detail_scheduled_period_start=item.detail_scheduled_period_start,
                detail_scheduled_period_end=item.detail_scheduled_period_end,
                detail_scheduled_string=item.detail_scheduled_string,
                detail_location_type=loc_type,
                detail_location_id=loc_id,
                detail_location_display=item.detail_location_display,
                detail_product_codeable_concept_system=item.detail_product_codeable_concept_system,
                detail_product_codeable_concept_code=item.detail_product_codeable_concept_code,
                detail_product_codeable_concept_display=item.detail_product_codeable_concept_display,
                detail_product_codeable_concept_text=item.detail_product_codeable_concept_text,
                detail_product_reference_type=prod_ref_type,
                detail_product_reference_id=prod_ref_id,
                detail_product_reference_display=item.detail_product_reference_display,
                detail_daily_amount_value=item.detail_daily_amount_value,
                detail_daily_amount_unit=item.detail_daily_amount_unit,
                detail_daily_amount_system=item.detail_daily_amount_system,
                detail_daily_amount_code=item.detail_daily_amount_code,
                detail_quantity_value=item.detail_quantity_value,
                detail_quantity_unit=item.detail_quantity_unit,
                detail_quantity_system=item.detail_quantity_system,
                detail_quantity_code=item.detail_quantity_code,
                detail_description=item.detail_description,
                **{n: getattr(item, n) for n in _BOUNDS_FIELDS},
            )
            session.add(activity)
            self._build_activity_grandchildren(session, activity, org_id, item)

    async def create(
        self,
        payload: CarePlanCreateSchema,
        user_id: str,
        org_id: str,
        created_by: str,
    ) -> CarePlanModel:
        subject_type, subject_id = _parse_ref_closed_opt(payload.subject, CarePlanSubjectReferenceType, "subject")
        encounter_type, encounter_id = _parse_ref_closed_opt(payload.encounter, EncounterReferenceType, "encounter")
        author_type, author_id = _parse_ref_closed_opt(payload.author, CarePlanAuthorReferenceType, "author")

        async with self.session_factory() as session:
            care_plan = CarePlanModel(
                user_id=user_id,
                org_id=org_id,
                status=_cast_status(payload.status),
                intent=_cast_intent(payload.intent),
                title=payload.title,
                description=payload.description,
                subject_type=subject_type,
                subject_id=subject_id,
                subject_display=payload.subject_display,
                encounter_type=encounter_type,
                encounter_id=encounter_id,
                encounter_display=payload.encounter_display,
                period_start=payload.period_start,
                period_end=payload.period_end,
                created=payload.created,
                author_type=author_type,
                author_id=author_id,
                author_display=payload.author_display,
                instantiates_canonical=payload.instantiates_canonical,
                instantiates_uri=payload.instantiates_uri,
                created_by=created_by,
            )
            session.add(care_plan)
            await session.flush()
            self._build_children(session, care_plan, org_id, payload)
            await session.commit()
            await session.refresh(care_plan)

        return await self.get_by_care_plan_id(care_plan.care_plan_id)

    async def patch(
        self,
        care_plan_id: int,
        payload: CarePlanPatchSchema,
        updated_by: str,
    ) -> Optional[CarePlanModel]:
        async with self.session_factory() as session:
            stmt = _with_relationships(select(CarePlanModel).where(CarePlanModel.care_plan_id == care_plan_id))
            care_plan = (await session.execute(stmt)).scalars().first()
            if not care_plan:
                return None

            data = payload.model_dump(exclude_unset=True)

            # plain scalars (status / intent are enums, never null — enforced by the schema)
            for key in (
                "status", "intent", "title", "description", "subject_display", "encounter_display",
                "period_start", "period_end", "created", "author_display", "instantiates_canonical", "instantiates_uri",
            ):
                if key in data:
                    setattr(care_plan, key, data[key])

            # references (format + allowed type only); null clears the optional ones
            for key, enum_cls, prefix in (
                ("subject", CarePlanSubjectReferenceType, "subject"),
                ("encounter", EncounterReferenceType, "encounter"),
                ("author", CarePlanAuthorReferenceType, "author"),
            ):
                if key in data:
                    if data[key] is None:
                        setattr(care_plan, f"{prefix}_type", None)
                        setattr(care_plan, f"{prefix}_id", None)
                        if f"{prefix}_display" not in data:
                            setattr(care_plan, f"{prefix}_display", None)
                    else:
                        rt, ri = _parse_ref_closed(data[key], enum_cls, key)
                        setattr(care_plan, f"{prefix}_type", rt)
                        setattr(care_plan, f"{prefix}_id", ri)

            care_plan.updated_by = updated_by

            # child lists: a list that is sent REPLACES the stored one; [] / null clears; omitted = untouched
            replaced = [f for f in CHILD_FIELDS if f in payload.model_fields_set]
            for f in replaced:
                getattr(care_plan, _COLLECTIONS[f]).clear()
            if replaced:
                await session.flush()
                self._build_children(session, care_plan, care_plan.org_id, _OnlyFields(payload, replaced))

            await session.commit()

        return await self.get_by_care_plan_id(care_plan_id)

    async def delete(self, care_plan_id: int) -> bool:
        async with self.session_factory() as session:
            stmt = select(CarePlanModel).where(CarePlanModel.care_plan_id == care_plan_id)
            result = await session.execute(stmt)
            care_plan = result.scalars().first()
            if not care_plan:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail=f"CarePlan {care_plan_id} not found.",
                )
            await session.delete(care_plan)
            await session.commit()
        return True
