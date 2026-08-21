"""Create and patch, both operating on the whole nested payload.

There is no scalar-only variant: the staging record and its observations are
written together or not at all, because "the agent finished, here is what it
found" is one event and must not be able to half-apply.
"""

from sqlalchemy.future import select

from app.core.logging import get_logger
from app.models.enums import StagingStatus
from app.models.staging_medical_record import StagingMedicalRecordModel
from app.schemas.staging_medical_record.input import (
    StagingMedicalRecordCreateSchema,
    StagingMedicalRecordPatchSchema,
)

from ._shared import _build_staging_observation, _with_relationships

logger = get_logger(__name__)

# Handled explicitly rather than copied onto the model.
_NON_COLUMN_CREATE_FIELDS = {"observations"}
_NON_COLUMN_PATCH_FIELDS = {"observations"}


class _FullMixin:
    async def create(
        self, payload: StagingMedicalRecordCreateSchema
    ) -> StagingMedicalRecordModel:
        """Registers a source document, with any observations already extracted.

        `status` defaults to 'pending' when the caller omits it — that is what
        puts the record on the agent's queue, so silently leaving it NULL would
        make the record invisible to `GET ?status=pending`.
        """
        data = payload.model_dump(exclude_unset=True)
        observations = data.pop("observations", None)
        for key in _NON_COLUMN_CREATE_FIELDS:
            data.pop(key, None)

        data.setdefault("status", StagingStatus.pending)

        rec = StagingMedicalRecordModel(**data)
        rec.observations = [
            _build_staging_observation(
                obs,
                org_id=payload.org_id,
                user_id=payload.user_id,
                actor=payload.created_by,
            )
            for obs in (payload.observations or [])
        ]

        async with self.session_factory() as session:
            try:
                session.add(rec)
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            # Re-read through _with_relationships: the write session's identity
            # map holds the objects, but the caller serializes the whole
            # four-level staging_observation tree and every collection on it must be
            # eagerly loaded or the async lazy-load raises.
            stmt = _with_relationships(
                select(StagingMedicalRecordModel).where(StagingMedicalRecordModel.id == rec.id)
            )
            created = (await session.execute(stmt)).scalars().first()

        logger.info(
            "Staging record created",
            extra={
                "event": "staging_medical_record.created",
                "staging_medical_record_id": created.staging_medical_record_id,
                "org_id": created.org_id,
                "user_id": created.user_id,
                "status": created.status.value if created.status else None,
                "staging_observation_count": len(created.observations),
            },
        )
        return created

    async def patch(
        self, staging_medical_record_id: int, payload: StagingMedicalRecordPatchSchema
    ) -> StagingMedicalRecordModel | None:
        """Applies only the fields present in the request body.

        ⚠️ `observations` is REPLACE, not append. Because the check is on
        *presence* in `exclude_unset` rather than on truthiness, an omitted key
        leaves the existing observations alone while an explicit `[]` clears
        them — two genuinely different requests that a truthiness check would
        collapse into one.

        Returns None when no such record exists, so the service can raise a
        404 rather than the repository inventing an HTTP concern.
        """
        data = payload.model_dump(exclude_unset=True)
        replace_staging_observations = "observations" in data
        data.pop("observations", None)
        for key in _NON_COLUMN_PATCH_FIELDS:
            data.pop(key, None)

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
                for key, value in data.items():
                    setattr(rec, key, value)

                if replace_staging_observations:
                    # Reassigning the collection lets delete-orphan reap the
                    # old rows; the new ones inherit tenancy from the record as
                    # it now stands, so a patch that also changes org_id keeps
                    # parent and children consistent.
                    rec.observations = [
                        _build_staging_observation(
                            obs,
                            org_id=rec.org_id,
                            user_id=rec.user_id,
                            actor=payload.updated_by or rec.updated_by,
                        )
                        for obs in (payload.observations or [])
                    ]

                await session.commit()
            except Exception:
                await session.rollback()
                raise

            refreshed = (await session.execute(stmt)).scalars().first()

        logger.info(
            "Staging record updated",
            extra={
                "event": "staging_medical_record.updated",
                "staging_medical_record_id": staging_medical_record_id,
                "fields": sorted(data),
                "staging_observations_replaced": replace_staging_observations,
                "staging_observation_count": len(refreshed.observations),
            },
        )
        return refreshed
