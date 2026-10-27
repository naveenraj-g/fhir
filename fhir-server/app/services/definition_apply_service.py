"""
FHIR `$apply` operations for PlanDefinition and ActivityDefinition.

An ActivityDefinition is a template; applying it to a subject produces the request resource named by its
`kind`. Only `kind = ServiceRequest` is generated today — any other kind is reported in `skipped`, never
silently dropped. Applying a PlanDefinition applies, in order, every action that points at an
ActivityDefinition (`action.definitionCanonical`).

`persist=false` validates and maps the would-be ServiceRequests without writing anything; `persist=true`
saves them all in one transaction.
"""
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from fastapi import HTTPException, status as http_status

from app.fhir.mappers.service_request import to_fhir_service_request, to_plain_service_request
from app.models.activity_definition.activity_definition import ActivityDefinitionModel
from app.models.activity_definition.enums import ActivityDefinitionKind, PlanDefinitionStatus
from app.models.plan_definition.plan_definition import PlanDefinitionAction, PlanDefinitionModel
from app.models.service_request.service_request import ServiceRequestModel
from app.repository.activity_definition_repository import ActivityDefinitionRepository
from app.repository.service_request_repository import ServiceRequestRepository
from app.schemas.definition_apply import ActivityDefinitionApplyRequest, PlanDefinitionApplyRequest
from app.schemas.service_request import ServiceRequestCreateSchema

_AD_REF = re.compile(r"ActivityDefinition/(\d+)$")
_ENCOUNTER_REF = re.compile(r"^Encounter/(\d+)$")


@dataclass
class SkippedAction:
    reason: str
    action_id: Optional[str] = None
    action_title: Optional[str] = None
    definition: Optional[str] = None


@dataclass
class ApplyResult:
    definition: str  # "PlanDefinition/400001" | "ActivityDefinition/410001"
    subject: str
    encounter: Optional[str]
    persisted: bool
    service_requests: List[ServiceRequestModel] = field(default_factory=list)
    skipped: List[SkippedAction] = field(default_factory=list)


def _encounter_public_id(encounter: Optional[str]) -> Optional[int]:
    if encounter is None:
        return None
    m = _ENCOUNTER_REF.match(encounter)
    if not m:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid encounter reference: '{encounter}'. Expected 'Encounter/<id>'.",
        )
    return int(m.group(1))


def _canonical_of(ad: ActivityDefinitionModel) -> str:
    return ad.url or f"ActivityDefinition/{ad.activity_definition_id}"


def _split_canonical(canonical: str) -> Tuple[Optional[int], str]:
    """'https://x/ActivityDefinition/410001|1.0.0' -> (410001, 'https://x/ActivityDefinition/410001')."""
    base = canonical.split("|", 1)[0].strip()
    m = _AD_REF.search(base)
    return (int(m.group(1)) if m else None), base


class DefinitionApplyService:
    def __init__(
        self,
        activity_definition_repository: ActivityDefinitionRepository,
        service_request_repository: ServiceRequestRepository,
    ):
        self.ad_repo = activity_definition_repository
        self.sr_repo = service_request_repository

    # ── output ────────────────────────────────────────────────────────────────

    @staticmethod
    def to_plain(result: ApplyResult) -> dict:
        items = []
        for sr in result.service_requests:
            d = to_plain_service_request(sr)
            if not result.persisted:  # unsaved rows have no public id yet; the encounter link is not loaded either
                d["id"] = None
                d["encounter_id"] = _encounter_public_id(result.encounter)
            items.append(d)
        return {
            "definition": result.definition,
            "subject": result.subject,
            "encounter": result.encounter,
            "persisted": result.persisted,
            "total": len(items),
            "service_requests": items,
            "skipped": [
                {"action_id": s.action_id, "action_title": s.action_title, "definition": s.definition, "reason": s.reason}
                for s in result.skipped
            ],
        }

    @staticmethod
    def to_fhir(result: ApplyResult) -> dict:
        entries = []
        for sr in result.service_requests:
            r = to_fhir_service_request(sr)
            if not result.persisted:
                r.pop("id", None)
                if result.encounter:
                    r["encounter"] = {"reference": result.encounter}
            entries.append({"resource": r})
        if result.skipped:
            entries.append({
                "resource": {
                    "resourceType": "OperationOutcome",
                    "issue": [
                        {
                            "severity": "information",
                            "code": "informational",
                            "details": {"text": s.action_title or s.action_id or s.definition or "action"},
                            "diagnostics": s.reason,
                        }
                        for s in result.skipped
                    ],
                }
            })
        return {
            "resourceType": "Bundle",
            "type": "collection",
            "total": len(result.service_requests),
            "entry": entries,
        }

    # ── building blocks ───────────────────────────────────────────────────────

    @staticmethod
    def _payload(
        ad: ActivityDefinitionModel,
        req: ActivityDefinitionApplyRequest,
        instantiates: List[str],
        instruction: Optional[str],
    ) -> ServiceRequestCreateSchema:
        data: dict = {
            "user_id": req.user_id,
            "org_id": req.org_id,
            "created_by": req.created_by,
            "status": req.status or ("active" if req.persist else "draft"),
            "intent": ad.intent.value if ad.intent else "order",
            "priority": ad.priority.value if ad.priority else None,
            "do_not_perform": ad.do_not_perform,
            "code_system": ad.code_system,
            "code_code": ad.code_code,
            "code_display": ad.code_display,
            "code_text": ad.code_text or (None if ad.code_code else ad.title or ad.name),
            "subject": req.subject,
            "subject_display": req.subject_display,
            "encounter_id": _encounter_public_id(req.encounter),
            "encounter_display": req.encounter_display,
            "authored_on": datetime.now(timezone.utc),
            "requester": req.practitioner,
            "requester_display": req.practitioner_display,
            "quantity_value": ad.quantity_value,
            "quantity_unit": ad.quantity_unit,
            "quantity_system": ad.quantity_system,
            "quantity_code": ad.quantity_code,
            "instantiates_canonical": ",".join(instantiates),
            "patient_instruction": instruction,
        }
        # occurrence[x] <- timing[x]
        if ad.timing_datetime:
            data["occurrence_datetime"] = ad.timing_datetime
        elif ad.timing_period_start or ad.timing_period_end:
            data["occurrence_period_start"] = ad.timing_period_start
            data["occurrence_period_end"] = ad.timing_period_end
        elif ad.timing_timing_repeat_frequency is not None or ad.timing_timing_repeat_period is not None:
            data["occurrence_timing_frequency"] = ad.timing_timing_repeat_frequency
            data["occurrence_timing_period"] = ad.timing_timing_repeat_period
            data["occurrence_timing_period_unit"] = ad.timing_timing_repeat_period_unit
            data["occurrence_timing_bounds_start"] = ad.timing_timing_repeat_bounds_period_start
            data["occurrence_timing_bounds_end"] = ad.timing_timing_repeat_bounds_period_end
        return ServiceRequestCreateSchema(**{k: v for k, v in data.items() if v is not None})

    async def _finish(
        self,
        definition: str,
        req: ActivityDefinitionApplyRequest,
        payloads: List[ServiceRequestCreateSchema],
        skipped: List[SkippedAction],
    ) -> ApplyResult:
        if req.persist and payloads:
            rows = await self.sr_repo.create_many(payloads, req.user_id, req.org_id, req.created_by)
        else:
            rows = await self.sr_repo.build_drafts(payloads, req.user_id, req.org_id) if payloads else []
        return ApplyResult(
            definition=definition, subject=req.subject, encounter=req.encounter,
            persisted=req.persist, service_requests=rows, skipped=skipped,
        )

    async def _existing(self, req: ActivityDefinitionApplyRequest, canonicals: List[str]) -> set:
        if req.allow_duplicates or not canonicals:
            return set()
        return await self.sr_repo.existing_instantiated(
            req.org_id, req.subject, _encounter_public_id(req.encounter), canonicals
        )

    @staticmethod
    def _check_applicable(ad: ActivityDefinitionModel) -> Optional[str]:
        if ad.status == PlanDefinitionStatus.retired:
            return "ActivityDefinition is retired"
        if ad.kind != ActivityDefinitionKind.ServiceRequest:
            kind = ad.kind.value if ad.kind else "none"
            return f"ActivityDefinition kind '{kind}' is not supported yet — only ServiceRequest is generated"
        return None

    # ── ActivityDefinition/$apply ─────────────────────────────────────────────

    async def apply_activity_definition(
        self, ad: ActivityDefinitionModel, req: ActivityDefinitionApplyRequest
    ) -> ApplyResult:
        definition = f"ActivityDefinition/{ad.activity_definition_id}"
        skipped: List[SkippedAction] = []
        payloads: List[ServiceRequestCreateSchema] = []
        canonical = _canonical_of(ad)
        reason = self._check_applicable(ad)
        if not reason and canonical in await self._existing(req, [canonical]):
            reason = "A ServiceRequest for this definition already exists for the subject/encounter"
        if reason:
            skipped.append(SkippedAction(reason=reason, action_title=ad.title or ad.name, definition=definition))
        else:
            payloads.append(self._payload(ad, req, [canonical], None))
        return await self._finish(definition, req, payloads, skipped)

    # ── PlanDefinition/$apply ─────────────────────────────────────────────────

    async def apply_plan_definition(
        self, plan: PlanDefinitionModel, req: PlanDefinitionApplyRequest
    ) -> ApplyResult:
        definition = f"PlanDefinition/{plan.plan_definition_id}"
        actions: List[PlanDefinitionAction] = sorted(plan.actions, key=lambda a: a.position)

        if req.selected_actions is not None:
            known = {a.element_id for a in actions if a.element_id}
            unknown = [a for a in req.selected_actions if a not in known]
            if unknown:
                raise HTTPException(
                    status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"selected_actions not part of {definition}: {unknown}. Known action ids: {sorted(known)}.",
                )

        skipped: List[SkippedAction] = []
        resolved: List[Tuple[PlanDefinitionAction, ActivityDefinitionModel]] = []
        seen = set()
        for action in actions:
            if not (action.definition_canonical or action.definition_uri):
                continue  # grouping action: it only has children, nothing to generate
            info = dict(action_id=action.element_id, action_title=action.title or action.text_equivalent,
                        definition=action.definition_canonical or action.definition_uri)
            if req.selected_actions is not None and action.element_id not in req.selected_actions:
                continue  # not chosen by the caller: neither generated nor reported
            if action.type_code and action.type_code != "create":
                skipped.append(SkippedAction(reason=f"Action type '{action.type_code}' is not supported — only 'create'", **info))
                continue
            if not action.definition_canonical:
                skipped.append(SkippedAction(reason="Action definition is a plain uri, not an ActivityDefinition canonical", **info))
                continue
            public_id, url = _split_canonical(action.definition_canonical)
            ad = await self.ad_repo.find_for_apply(req.org_id, public_id=public_id, url=None if public_id else url)
            if ad is None:
                skipped.append(SkippedAction(reason="ActivityDefinition not found in this organization", **info))
                continue
            reason = self._check_applicable(ad)
            if reason:
                skipped.append(SkippedAction(reason=reason, **info))
                continue
            if ad.activity_definition_id in seen:
                skipped.append(SkippedAction(reason="Already generated by an earlier action of this plan", **info))
                continue
            seen.add(ad.activity_definition_id)
            resolved.append((action, ad))

        existing = await self._existing(req, [_canonical_of(ad) for _, ad in resolved])
        payloads: List[ServiceRequestCreateSchema] = []
        plan_ref = f"PlanDefinition/{plan.plan_definition_id}"
        for action, ad in resolved:
            canonical = _canonical_of(ad)
            if canonical in existing:
                skipped.append(SkippedAction(
                    reason="A ServiceRequest for this definition already exists for the subject/encounter",
                    action_id=action.element_id, action_title=action.title or action.text_equivalent,
                    definition=action.definition_canonical,
                ))
                continue
            payloads.append(self._payload(ad, req, [canonical, plan_ref], action.description))
        return await self._finish(definition, req, payloads, skipped)
