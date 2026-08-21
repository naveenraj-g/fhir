"""Read and delete. Create/patch live in full.py. Review — the clinician's
accept/reject/needs-revision decision — lives here too: it is a scalar-only
write, same shape as get/delete above, not the nested-payload write full.py
exists for."""

from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.future import select

from app.core.filters import (
    apply_date_range_filter,
    apply_string_filter,
    apply_token_filter,
)
from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.enums import StagingStatus
from app.models.staging_medical_record import StagingMedicalRecordModel
from app.schemas.staging_medical_record.input import StagingReviewInput

from ._shared import _SORTABLE_FIELDS, _with_relationships

logger = get_logger(__name__)


class _CoreMixin:
    async def get_by_staging_medical_record_id(
        self, staging_medical_record_id: int
    ) -> StagingMedicalRecordModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(StagingMedicalRecordModel).where(
                    StagingMedicalRecordModel.staging_medical_record_id == staging_medical_record_id
                )
            )
            return (await session.execute(stmt)).scalars().first()

    def _apply_list_filters(
        self,
        stmt,
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
    ):
        """Every filter is on staging_medical_record's own columns — no joins, no
        EXISTS subqueries. Observations are not searchable through this
        endpoint; they come back nested but are not a query surface."""
        stmt = apply_token_filter(stmt, StagingMedicalRecordModel.org_id, org_id)
        stmt = apply_token_filter(stmt, StagingMedicalRecordModel.user_id, user_id)
        stmt = apply_token_filter(stmt, StagingMedicalRecordModel.status, staging_status)
        stmt = apply_token_filter(stmt, StagingMedicalRecordModel.file_id, file_id)
        stmt = apply_token_filter(stmt, StagingMedicalRecordModel.patient_id, patient_id)
        stmt = apply_token_filter(
            stmt, StagingMedicalRecordModel.appointment_id, appointment_id
        )
        stmt = apply_token_filter(stmt, StagingMedicalRecordModel.encounter_id, encounter_id)
        stmt = apply_token_filter(
            stmt, StagingMedicalRecordModel.service_request_id, service_request_id
        )
        stmt = apply_token_filter(
            stmt, StagingMedicalRecordModel.diagnostic_report_id, diagnostic_report_id
        )
        stmt = apply_string_filter(
            stmt, StagingMedicalRecordModel.attachment_title, attachment_title
        )
        stmt = apply_date_range_filter(
            stmt, StagingMedicalRecordModel.created_at, created_after, created_before
        )
        return stmt

    async def list(
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
        """Paginated, filtered, sorted list. Returns (rows, total); total is
        None when total_mode="none"."""
        async with self.session_factory() as session:
            filter_kwargs = {
                "org_id": org_id,
                "user_id": user_id,
                "staging_status": staging_status,
                "file_id": file_id,
                "patient_id": patient_id,
                "appointment_id": appointment_id,
                "encounter_id": encounter_id,
                "service_request_id": service_request_id,
                "diagnostic_report_id": diagnostic_report_id,
                "attachment_title": attachment_title,
                "created_after": created_after,
                "created_before": created_before,
            }
            base = self._apply_list_filters(
                _with_relationships(select(StagingMedicalRecordModel)), **filter_kwargs
            )
            # Built from the same filter call so the two can never drift apart.
            count_base = self._apply_list_filters(
                select(func.count()).select_from(StagingMedicalRecordModel), **filter_kwargs
            )
            sort_column, sort_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                default_column=StagingMedicalRecordModel.staging_medical_record_id,
                default_desc=True,
            )
            rows, total = await self._execute_paginated(
                session,
                base,
                count_base,
                sort_column=sort_column,
                sort_desc=sort_desc,
                limit=limit,
                offset=offset,
                total_mode=total_mode,
            )
        logger.debug(
            "Staging records listed",
            extra={
                "event": "staging_medical_record.listed",
                "returned": len(rows),
                "total": total,
                "limit": limit,
                "offset": offset,
                "filters": sorted(
                    k for k, v in filter_kwargs.items() if v is not None
                ),
            },
        )
        return rows, total

    async def delete(self, staging_medical_record_id: int) -> bool:
        """Deletes the record and, by cascade, every staging_observation hanging off
        it (delete-orphan on StagingMedicalRecordModel.observations). Returns False
        when there was nothing to delete."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(StagingMedicalRecordModel).where(
                    StagingMedicalRecordModel.staging_medical_record_id == staging_medical_record_id
                )
            )
            rec = (await session.execute(stmt)).scalars().first()
            if not rec:
                return False
            try:
                await session.delete(rec)
                await session.commit()
            except Exception:
                await session.rollback()
                raise
        logger.info(
            "Staging record deleted",
            extra={
                "event": "staging_medical_record.deleted",
                "staging_medical_record_id": staging_medical_record_id,
            },
        )
        return True

    async def review(
        self, staging_medical_record_id: int, payload: StagingReviewInput
    ) -> StagingMedicalRecordModel | None:
        """Applies a clinician's review decision. `reviewed_at` is always set
        server-side to the moment this request is processed — it is not a
        caller-supplied field, unlike `reviewed_by`.

        Returns None when no such record exists, so the service can raise a
        404 rather than the repository inventing an HTTP concern.
        """
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(StagingMedicalRecordModel).where(
                    StagingMedicalRecordModel.staging_medical_record_id == staging_medical_record_id
                )
            )
            rec = (await session.execute(stmt)).scalars().first()
            if not rec:
                return None

            try:
                rec.review_status = payload.review_status
                rec.reviewed_by = payload.reviewed_by
                rec.review_notes = payload.review_notes
                rec.reviewed_at = datetime.now(timezone.utc)
                await session.commit()
            except Exception:
                await session.rollback()
                raise

            refreshed = (await session.execute(stmt)).scalars().first()

        logger.info(
            "Staging record reviewed",
            extra={
                "event": "staging_medical_record.reviewed",
                "staging_medical_record_id": staging_medical_record_id,
                "review_status": payload.review_status.value,
                "reviewed_by": payload.reviewed_by,
            },
        )
        return refreshed
