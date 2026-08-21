"""Staging-record business logic.

Thin by design: this service has no auth and no tenant scoping to enforce, so
there is far less here than in fhir-server's equivalent. What it does own is
the not-found boundary — the repository returns None, and turning that into a
404 is a policy decision, not a data-access one.
"""

from datetime import datetime

from app.core.logging import get_logger
from app.errors.domain import NotFoundError
from app.models.enums import StagingStatus
from app.models.staging_medical_record import StagingMedicalRecordModel
from app.repository.staging_medical_record import StagingMedicalRecordRepository
from app.schemas.staging_medical_record.input import (
    StagingMedicalRecordCreateSchema,
    StagingMedicalRecordPatchSchema,
    StagingReviewInput,
)
from app.serializers import to_plain_staging_medical_record

logger = get_logger(__name__)


class _CoreMixin:
    def __init__(self, repository: StagingMedicalRecordRepository):
        self.repository = repository

    # ── Formatter ─────────────────────────────────────────────────────────
    # Underscore-prefixed so @trace_methods skips it — it runs once per row
    # and would bury the actual call flow.

    def _to_plain(self, rec: StagingMedicalRecordModel) -> dict:
        return to_plain_staging_medical_record(rec)

    # ── Read ──────────────────────────────────────────────────────────────

    async def get_staging_medical_record(self, staging_medical_record_id: int) -> StagingMedicalRecordModel:
        rec = await self.repository.get_by_staging_medical_record_id(staging_medical_record_id)
        if not rec:
            raise NotFoundError(f"Staging record {staging_medical_record_id} not found")
        return rec

    async def list_staging_medical_records(
        self,
        org_id: str | None = None,
        user_id: str | None = None,
        staging_status: StagingStatus | None = None,
        file_id: str | None = None,
        patient_id: int | None = None,
        appointment_id: int | None = None,
        encounter_id: int | None = None,
        service_request_id: int | None = None,
        diagnostic_report_id: int | None = None,
        attachment_title: str | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[StagingMedicalRecordModel], int | None]:
        return await self.repository.list(
            org_id=org_id,
            user_id=user_id,
            staging_status=staging_status,
            file_id=file_id,
            patient_id=patient_id,
            appointment_id=appointment_id,
            encounter_id=encounter_id,
            service_request_id=service_request_id,
            diagnostic_report_id=diagnostic_report_id,
            attachment_title=attachment_title,
            created_after=created_after,
            created_before=created_before,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    # ── Write ─────────────────────────────────────────────────────────────

    async def create_staging_medical_record(
        self, payload: StagingMedicalRecordCreateSchema
    ) -> StagingMedicalRecordModel:
        return await self.repository.create(payload)

    async def patch_staging_medical_record(
        self, staging_medical_record_id: int, payload: StagingMedicalRecordPatchSchema
    ) -> StagingMedicalRecordModel:
        rec = await self.repository.patch(staging_medical_record_id, payload)
        if not rec:
            raise NotFoundError(f"Staging record {staging_medical_record_id} not found")
        return rec

    async def delete_staging_medical_record(self, staging_medical_record_id: int) -> None:
        deleted = await self.repository.delete(staging_medical_record_id)
        if not deleted:
            raise NotFoundError(f"Staging record {staging_medical_record_id} not found")

    async def review_staging_medical_record(
        self, staging_medical_record_id: int, payload: StagingReviewInput
    ) -> StagingMedicalRecordModel:
        """Applies a clinician's accept/reject/needs-revision decision. Kept
        as its own method (not folded into patch_staging_medical_record)
        because it is called from the dedicated /review router endpoint by a
        different actor (a clinician, not the agent pipeline) — see
        StagingReviewInput's docstring for why the two write paths are kept
        separate all the way down."""
        rec = await self.repository.review(staging_medical_record_id, payload)
        if not rec:
            raise NotFoundError(f"Staging record {staging_medical_record_id} not found")
        return rec
