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
    parse_reference_param,
    period_date_clause,
    reference_clause,
    split_or,
    token_clause,
)
from app.models.enums import EncounterReferenceType
from app.models.procedure.enums import (
    ProcedureStatus,
    ProcedureSubjectType,
    ProcedureRecorderType,
    ProcedureAsserterType,
    ProcedureLocationReferenceType,
    ProcedurePerformerActorType,
    ProcedurePerformerOnBehalfOfType,
    ProcedureBasedOnReferenceType,
    ProcedurePartOfReferenceType,
    ProcedureReasonReferenceType,
    ProcedureReportReferenceType,
    ProcedureComplicationDetailReferenceType,
    ProcedureNoteAuthorReferenceType,
    ProcedureFocalDeviceManipulatedReferenceType,
    ProcedureUsedReferenceType,
)
from app.models.procedure.procedure import (
    ProcedureModel,
    ProcedureIdentifier,
    ProcedureBasedOn,
    ProcedurePartOf,
    ProcedurePerformer,
    ProcedureReasonCode,
    ProcedureReasonReference,
    ProcedureBodySite,
    ProcedureReport,
    ProcedureComplication,
    ProcedureComplicationDetail,
    ProcedureFollowUp,
    ProcedureNote,
    ProcedureFocalDevice,
    ProcedureUsedReference,
    ProcedureUsedCode,
)
from app.schemas.procedure import ProcedureCreateSchema, ProcedurePatchSchema


def _with_relationships(stmt):
    return stmt.options(
        selectinload(ProcedureModel.identifiers),
        selectinload(ProcedureModel.based_on),
        selectinload(ProcedureModel.part_of),
        selectinload(ProcedureModel.performers),
        selectinload(ProcedureModel.reason_codes),
        selectinload(ProcedureModel.reason_references),
        selectinload(ProcedureModel.body_sites),
        selectinload(ProcedureModel.reports),
        selectinload(ProcedureModel.complications),
        selectinload(ProcedureModel.complication_details),
        selectinload(ProcedureModel.follow_ups),
        selectinload(ProcedureModel.notes),
        selectinload(ProcedureModel.focal_devices),
        selectinload(ProcedureModel.used_references),
        selectinload(ProcedureModel.used_codes),
    )


def _parse_ref(ref: str, enum_cls, field: str):
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


@dataclass
class ProcedureSearch:
    """FHIR R4 Procedure search parameters (https://www.hl7.org/fhir/R4/procedure.html#search)."""

    id: Optional[str] = None                      # _id
    identifier: Optional[str] = None
    status: Optional[str] = None
    category: Optional[str] = None
    code: Optional[str] = None
    patient: Optional[str] = None
    subject: Optional[str] = None
    encounter: Optional[str] = None
    date: List[str] = field(default_factory=list)
    performer: Optional[str] = None
    location: Optional[str] = None
    part_of: Optional[str] = None
    based_on: Optional[str] = None
    reason_code: Optional[str] = None
    reason_reference: Optional[str] = None
    instantiates_canonical: Optional[str] = None
    instantiates_uri: Optional[str] = None
    last_updated: List[str] = field(default_factory=list)   # _lastUpdated
    performed_from: Optional[datetime] = None     # legacy range helpers
    performed_to: Optional[datetime] = None


class _PatientOnly(str, Enum):
    Patient = "Patient"



# Child-list fields shared by create and patch: payload field -> ProcedureModel relationship name.
CHILD_FIELDS = {
    "identifier": "identifiers",
    "based_on": "based_on",
    "part_of": "part_of",
    "performer": "performers",
    "reason_code": "reason_codes",
    "reason_reference": "reason_references",
    "body_site": "body_sites",
    "report": "reports",
    "complication": "complications",
    "complication_detail": "complication_details",
    "follow_up": "follow_ups",
    "note": "notes",
    "focal_device": "focal_devices",
    "used_reference": "used_references",
    "used_code": "used_codes",
}


class _OnlyFields:
    """View of a payload exposing only the listed fields; every other attribute reads as None."""

    def __init__(self, payload, fields):
        self._payload = payload
        self._fields = set(fields)

    def __getattr__(self, name):
        return getattr(self._payload, name) if name in self._fields else None


def _add_children(session, proc, payload, org_id) -> None:
    """Create the child rows for every child list present on `payload` (None / missing = none)."""
    for item in (payload.identifier or []):
        session.add(ProcedureIdentifier(
            procedure=proc, org_id=org_id,
            use=item.use, type_system=item.type_system, type_code=item.type_code,
            type_display=item.type_display, type_text=item.type_text,
            system=item.system, value=item.value,
            period_start=item.period_start, period_end=item.period_end,
            assigner=item.assigner,
        ))

    for item in (payload.based_on or []):
        bo_type, bo_id = _parse_ref(item.reference, ProcedureBasedOnReferenceType, "based_on")
        session.add(ProcedureBasedOn(
            procedure=proc, org_id=org_id,
            reference_type=bo_type, reference_id=bo_id,
            reference_display=item.reference_display,
        ))

    for item in (payload.part_of or []):
        po_type, po_id = _parse_ref(item.reference, ProcedurePartOfReferenceType, "part_of")
        session.add(ProcedurePartOf(
            procedure=proc, org_id=org_id,
            reference_type=po_type, reference_id=po_id,
            reference_display=item.reference_display,
        ))

    for item in (payload.performer or []):
        actor_type, actor_id = _parse_ref(item.actor, ProcedurePerformerActorType, "performer.actor")
        obo_type, obo_id = None, None
        if item.on_behalf_of:
            obo_type, obo_id = _parse_ref(
                item.on_behalf_of, ProcedurePerformerOnBehalfOfType, "performer.onBehalfOf"
            )
        session.add(ProcedurePerformer(
            procedure=proc, org_id=org_id,
            function_system=item.function_system, function_code=item.function_code,
            function_display=item.function_display, function_text=item.function_text,
            actor_type=actor_type, actor_id=actor_id, actor_display=item.actor_display,
            on_behalf_of_type=obo_type, on_behalf_of_id=obo_id,
            on_behalf_of_display=item.on_behalf_of_display,
        ))

    for item in (payload.reason_code or []):
        session.add(ProcedureReasonCode(
            procedure=proc, org_id=org_id,
            coding_system=item.coding_system, coding_code=item.coding_code,
            coding_display=item.coding_display, text=item.text,
        ))

    for item in (payload.reason_reference or []):
        rr_type, rr_id = _parse_ref(item.reference, ProcedureReasonReferenceType, "reason_reference")
        session.add(ProcedureReasonReference(
            procedure=proc, org_id=org_id,
            reference_type=rr_type, reference_id=rr_id,
            reference_display=item.reference_display,
        ))

    for item in (payload.body_site or []):
        session.add(ProcedureBodySite(
            procedure=proc, org_id=org_id,
            coding_system=item.coding_system, coding_code=item.coding_code,
            coding_display=item.coding_display, text=item.text,
        ))

    for item in (payload.report or []):
        rp_type, rp_id = _parse_ref(item.reference, ProcedureReportReferenceType, "report")
        session.add(ProcedureReport(
            procedure=proc, org_id=org_id,
            reference_type=rp_type, reference_id=rp_id,
            reference_display=item.reference_display,
        ))

    for item in (payload.complication or []):
        session.add(ProcedureComplication(
            procedure=proc, org_id=org_id,
            coding_system=item.coding_system, coding_code=item.coding_code,
            coding_display=item.coding_display, text=item.text,
        ))

    for item in (payload.complication_detail or []):
        cd_type, cd_id = _parse_ref(
            item.reference, ProcedureComplicationDetailReferenceType, "complication_detail"
        )
        session.add(ProcedureComplicationDetail(
            procedure=proc, org_id=org_id,
            reference_type=cd_type, reference_id=cd_id,
            reference_display=item.reference_display,
        ))

    for item in (payload.follow_up or []):
        session.add(ProcedureFollowUp(
            procedure=proc, org_id=org_id,
            coding_system=item.coding_system, coding_code=item.coding_code,
            coding_display=item.coding_display, text=item.text,
        ))

    for item in (payload.note or []):
        note_ref_type, note_ref_id = None, None
        if item.author_reference:
            note_ref_type, note_ref_id = _parse_ref(
                item.author_reference, ProcedureNoteAuthorReferenceType, "note.authorReference"
            )
        session.add(ProcedureNote(
            procedure=proc, org_id=org_id,
            text=item.text, time=item.time,
            author_string=item.author_string,
            author_reference_type=note_ref_type, author_reference_id=note_ref_id,
            author_reference_display=item.author_reference_display,
        ))

    for item in (payload.focal_device or []):
        manip_type, manip_id = _parse_ref(
            item.manipulated_reference,
            ProcedureFocalDeviceManipulatedReferenceType,
            "focal_device.manipulated",
        )
        session.add(ProcedureFocalDevice(
            procedure=proc, org_id=org_id,
            action_system=item.action_system, action_code=item.action_code,
            action_display=item.action_display, action_text=item.action_text,
            manipulated_reference_type=manip_type, manipulated_reference_id=manip_id,
            manipulated_reference_display=item.manipulated_reference_display,
        ))

    for item in (payload.used_reference or []):
        ur_type, ur_id = _parse_ref(item.reference, ProcedureUsedReferenceType, "used_reference")
        session.add(ProcedureUsedReference(
            procedure=proc, org_id=org_id,
            reference_type=ur_type, reference_id=ur_id,
            reference_display=item.reference_display,
        ))

    for item in (payload.used_code or []):
        session.add(ProcedureUsedCode(
            procedure=proc, org_id=org_id,
            coding_system=item.coding_system, coding_code=item.coding_code,
            coding_display=item.coding_display, text=item.text,
        ))

class ProcedureRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    # ── Read ──────────────────────────────────────────────────────────────────

    async def get_by_procedure_id(self, procedure_id: int) -> Optional[ProcedureModel]:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(ProcedureModel).where(ProcedureModel.procedure_id == procedure_id)
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    def _apply_list_filters(self, stmt, user_id, org_id, search: Optional["ProcedureSearch"] = None):
        """user_id/org_id are optional tenant filters; `search` carries FHIR R4 search params."""
        if user_id:
            stmt = stmt.where(ProcedureModel.user_id == user_id)
        if org_id:
            stmt = stmt.where(ProcedureModel.org_id == org_id)
        if search is None:
            return stmt
        M = ProcedureModel

        # _id
        if search.id:
            ids = []
            for v in split_or(search.id):
                try:
                    ids.append(int(v))
                except ValueError:
                    raise HTTPException(
                        status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Invalid _id '{v}'. Must be an integer.",
                    )
            stmt = stmt.where(M.procedure_id.in_(ids))

        # identifier (token on Identifier.system|value)
        clause = token_clause(ProcedureIdentifier.system, ProcedureIdentifier.value, search.identifier)
        if clause is not None:
            stmt = stmt.where(
                select(ProcedureIdentifier.id)
                .where(ProcedureIdentifier.procedure_id == M.id, clause)
                .exists()
            )

        # status
        statuses = enum_token_values(search.status, ProcedureStatus, "status")
        if statuses:
            stmt = stmt.where(M.status.in_(statuses))

        # category / code (token on CodeableConcept.coding)
        for value, sys_col, code_col in (
            (search.category, M.category_system, M.category_code),
            (search.code, M.code_system, M.code_code),
        ):
            clause = token_clause(sys_col, code_col, value)
            if clause is not None:
                stmt = stmt.where(clause)

        # patient (Patient only) / subject (Patient|Group)
        for value, enum_cls, name in (
            (search.patient, _PatientOnly, "patient"),
            (search.subject, ProcedureSubjectType, "subject"),
        ):
            if value:
                clause = reference_clause(
                    M.subject_type, M.subject_id, parse_reference_param(value, enum_cls, name)
                )
                stmt = stmt.where(clause)

        # encounter — public encounter_id mapped to the internal FK
        if search.encounter:
            stmt = stmt.where(reference_clause(
                M.encounter_type, M.encounter_id,
                parse_reference_param(search.encounter, EncounterReferenceType, "encounter")))

        # date — performed[x]: dateTime or Period
        lo_expr = func.coalesce(M.performed_datetime, M.performed_period_start)
        hi_expr = func.coalesce(M.performed_datetime, M.performed_period_end)
        for value in search.date or []:
            prefix, s_lo, s_hi = parse_date_param(value, "date")
            stmt = stmt.where(period_date_clause(lo_expr, hi_expr, prefix, s_lo, s_hi))
        if search.performed_from is not None:
            stmt = stmt.where(lo_expr >= search.performed_from)
        if search.performed_to is not None:
            stmt = stmt.where(lo_expr <= search.performed_to)

        # _lastUpdated
        for value in search.last_updated or []:
            prefix, s_lo, s_hi = parse_date_param(value, "_lastUpdated")
            stmt = stmt.where(
                instant_clause(func.coalesce(M.updated_at, M.created_at), prefix, s_lo, s_hi)
            )

        # performer (performer.actor)
        if search.performer:
            clause = reference_clause(
                ProcedurePerformer.actor_type,
                ProcedurePerformer.actor_id,
                parse_reference_param(search.performer, ProcedurePerformerActorType, "performer"),
            )
            stmt = stmt.where(
                select(ProcedurePerformer.id)
                .where(ProcedurePerformer.procedure_id == M.id, clause)
                .exists()
            )

        # location
        if search.location:
            stmt = stmt.where(reference_clause(
                M.location_type,
                M.location_id,
                parse_reference_param(search.location, ProcedureLocationReferenceType, "location"),
            ))

        # part-of / based-on / reason-reference (child reference tables)
        for value, child, enum_cls, name in (
            (search.part_of, ProcedurePartOf, ProcedurePartOfReferenceType, "part-of"),
            (search.based_on, ProcedureBasedOn, ProcedureBasedOnReferenceType, "based-on"),
            (search.reason_reference, ProcedureReasonReference, ProcedureReasonReferenceType, "reason-reference"),
        ):
            if value:
                clause = reference_clause(
                    child.reference_type, child.reference_id,
                    parse_reference_param(value, enum_cls, name),
                )
                stmt = stmt.where(
                    select(child.id).where(child.procedure_id == M.id, clause).exists()
                )

        # reason-code
        clause = token_clause(
            ProcedureReasonCode.coding_system, ProcedureReasonCode.coding_code, search.reason_code
        )
        if clause is not None:
            stmt = stmt.where(
                select(ProcedureReasonCode.id)
                .where(ProcedureReasonCode.procedure_id == M.id, clause)
                .exists()
            )

        # instantiates-canonical / instantiates-uri (comma-joined text columns)
        for value, col in (
            (search.instantiates_canonical, M.instantiates_canonical),
            (search.instantiates_uri, M.instantiates_uri),
        ):
            items = split_or(value)
            if items:
                stmt = stmt.where(or_(*[
                    func.concat(",", col, ",").like(f"%,{item},%") for item in items
                ]))
        return stmt

    async def _search(
        self, user_id, org_id, search: Optional["ProcedureSearch"], limit: int, offset: int
    ) -> Tuple[List[ProcedureModel], int]:
        async with self.session_factory() as session:
            base = self._apply_list_filters(
                _with_relationships(select(ProcedureModel)), user_id, org_id, search
            )
            count_base = self._apply_list_filters(
                select(func.count()).select_from(ProcedureModel), user_id, org_id, search
            )
            total = (await session.execute(count_base)).scalar_one()
            performed = func.coalesce(
                ProcedureModel.performed_datetime, ProcedureModel.performed_period_start
            )
            rows = list((await session.execute(
                base.order_by(performed.desc().nulls_last(), ProcedureModel.id.desc())
                .offset(offset).limit(limit)
            )).scalars().all())
        return rows, total

    async def get_me(
        self,
        user_id: str,
        org_id: str,
        search: Optional["ProcedureSearch"] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[ProcedureModel], int]:
        return await self._search(user_id, org_id, search, limit, offset)

    async def list(
        self,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        search: Optional["ProcedureSearch"] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[ProcedureModel], int]:
        return await self._search(user_id, org_id, search, limit, offset)

    # ── Create ────────────────────────────────────────────────────────────────

    async def create(
        self,
        payload: ProcedureCreateSchema,
        user_id: Optional[str],
        org_id: Optional[str],
        created_by: Optional[str],
    ) -> ProcedureModel:
        async with self.session_factory() as session:
            # resolve subject
            subject_type, subject_id = None, None
            if payload.subject:
                subject_type, subject_id = _parse_ref(payload.subject, ProcedureSubjectType, "subject")

            # resolve encounter
            encounter_public_id = None
            if payload.encounter_id is not None:
                encounter_public_id = payload.encounter_id

            # resolve recorder
            recorder_type, recorder_id = None, None
            if payload.recorder:
                recorder_type, recorder_id = _parse_ref(payload.recorder, ProcedureRecorderType, "recorder")

            # resolve asserter
            asserter_type, asserter_id = None, None
            if payload.asserter:
                asserter_type, asserter_id = _parse_ref(payload.asserter, ProcedureAsserterType, "asserter")

            # resolve location
            location_type, location_ref_id = None, None
            if payload.location:
                location_type, location_ref_id = _parse_ref(
                    payload.location, ProcedureLocationReferenceType, "location"
                )

            proc = ProcedureModel(
                user_id=user_id,
                org_id=org_id,
                created_by=created_by,
                status=payload.status,
                status_reason_system=payload.status_reason_system,
                status_reason_code=payload.status_reason_code,
                status_reason_display=payload.status_reason_display,
                status_reason_text=payload.status_reason_text,
                category_system=payload.category_system,
                category_code=payload.category_code,
                category_display=payload.category_display,
                category_text=payload.category_text,
                code_system=payload.code_system,
                code_code=payload.code_code,
                code_display=payload.code_display,
                code_text=payload.code_text,
                subject_type=subject_type,
                subject_id=subject_id,
                subject_display=payload.subject_display,
                encounter_type=EncounterReferenceType.Encounter if encounter_public_id else None,
                encounter_id=encounter_public_id,
                encounter_display=payload.encounter_display,
                performed_datetime=payload.performed_datetime,
                performed_period_start=payload.performed_period_start,
                performed_period_end=payload.performed_period_end,
                performed_string=payload.performed_string,
                performed_age_value=payload.performed_age_value,
                performed_age_comparator=payload.performed_age_comparator,
                performed_age_unit=payload.performed_age_unit,
                performed_age_system=payload.performed_age_system,
                performed_age_code=payload.performed_age_code,
                performed_range_low_value=payload.performed_range_low_value,
                performed_range_low_unit=payload.performed_range_low_unit,
                performed_range_low_system=payload.performed_range_low_system,
                performed_range_low_code=payload.performed_range_low_code,
                performed_range_high_value=payload.performed_range_high_value,
                performed_range_high_unit=payload.performed_range_high_unit,
                performed_range_high_system=payload.performed_range_high_system,
                performed_range_high_code=payload.performed_range_high_code,
                recorder_type=recorder_type,
                recorder_id=recorder_id,
                recorder_display=payload.recorder_display,
                asserter_type=asserter_type,
                asserter_id=asserter_id,
                asserter_display=payload.asserter_display,
                location_type=location_type,
                location_id=location_ref_id,
                location_display=payload.location_display,
                outcome_system=payload.outcome_system,
                outcome_code=payload.outcome_code,
                outcome_display=payload.outcome_display,
                outcome_text=payload.outcome_text,
                instantiates_canonical=",".join(payload.instantiates_canonical) if payload.instantiates_canonical else None,
                instantiates_uri=",".join(payload.instantiates_uri) if payload.instantiates_uri else None,
            )
            session.add(proc)

            _add_children(session, proc, payload, org_id)

            await session.commit()
            await session.refresh(proc)

            stmt = _with_relationships(
                select(ProcedureModel).where(ProcedureModel.id == proc.id)
            )
            result = await session.execute(stmt)
            return result.scalars().one()

    # ── Patch ─────────────────────────────────────────────────────────────────

    async def patch(
        self,
        procedure_id: int,
        payload: ProcedurePatchSchema,
        updated_by: Optional[str],
    ) -> Optional[ProcedureModel]:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(ProcedureModel).where(ProcedureModel.procedure_id == procedure_id)
            )
            result = await session.execute(stmt)
            proc = result.scalars().first()
            if not proc:
                return None

            updates = payload.model_dump(exclude_unset=True, exclude=set(CHILD_FIELDS))
            # join list fields to comma-separated strings
            for list_field in ("instantiates_canonical", "instantiates_uri"):
                if list_field in updates and updates[list_field] is not None:
                    updates[list_field] = ",".join(updates[list_field])

            # reference fields: resolve "Type/id" strings into *_type / *_id columns
            if "subject" in updates:
                proc.subject_type, proc.subject_id = _parse_ref(
                    updates.pop("subject"), ProcedureSubjectType, "subject"
                )
            if "encounter_id" in updates:
                public_enc = updates.pop("encounter_id")
                if public_enc is None:
                    proc.encounter_id, proc.encounter_type = None, None
                    updates.setdefault("encounter_display", None)
                else:
                    proc.encounter_id = public_enc
                    proc.encounter_type = EncounterReferenceType.Encounter
            for key, enum_cls, id_attr in (
                ("recorder", ProcedureRecorderType, "recorder_id"),
                ("asserter", ProcedureAsserterType, "asserter_id"),
                ("location", ProcedureLocationReferenceType, "location_id"),
            ):
                if key in updates:
                    ref = updates.pop(key)
                    if ref is None:
                        setattr(proc, f"{key}_type", None)
                        setattr(proc, id_attr, None)
                        updates.setdefault(f"{key}_display", None)
                    else:
                        ref_type, ref_id = _parse_ref(ref, enum_cls, key)
                        setattr(proc, f"{key}_type", ref_type)
                        setattr(proc, id_attr, ref_id)

            for field_name, value in updates.items():
                setattr(proc, field_name, value)
            proc.updated_by = updated_by

            # Child lists: a list that is present REPLACES the stored one ([] / null clears it).
            replaced = [f for f in CHILD_FIELDS if f in payload.model_fields_set]
            for f in replaced:
                getattr(proc, CHILD_FIELDS[f]).clear()
            if replaced:
                await session.flush()
                _add_children(session, proc, _OnlyFields(payload, replaced), proc.org_id)

            await session.commit()
            await session.refresh(proc)

            stmt = _with_relationships(
                select(ProcedureModel).where(ProcedureModel.id == proc.id)
            )
            result = await session.execute(stmt)
            return result.scalars().one()

    # ── Delete ────────────────────────────────────────────────────────────────

    async def delete(self, procedure_id: int) -> None:
        async with self.session_factory() as session:
            stmt = select(ProcedureModel).where(ProcedureModel.procedure_id == procedure_id)
            result = await session.execute(stmt)
            proc = result.scalars().first()
            if proc:
                await session.delete(proc)
                await session.commit()
