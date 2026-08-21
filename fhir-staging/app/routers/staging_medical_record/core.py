from datetime import datetime

from fastapi import APIRouter, Depends, Path, Query, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.di.dependencies.staging_medical_record import (
    get_staging_medical_record_service,
)
from app.models.enums import StagingStatus
from app.schemas.staging_medical_record.input import (
    StagingMedicalRecordCreateSchema,
    StagingMedicalRecordPatchSchema,
    StagingReviewInput,
)
from app.services.staging_medical_record import StagingMedicalRecordService

from ._responses import (
    _DELETE_204,
    _ERR_NOT_FOUND,
    _ERR_VALIDATION,
    _LIST_200,
    _SINGLE_200,
    _SINGLE_201,
)

router = APIRouter()

logger = get_logger(__name__)


# ── Create ─────────────────────────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_staging_medical_record",
    summary="Register a source document for extraction",
    description=(
        "Records one medical-record document that an AI agent should process. "
        "Carries the filenest file handle and its metadata (flattened into the "
        "FHIR R4 Attachment fields), plus the clinical context the document "
        "belongs to — patient, encounter, and the service request it was "
        "produced against.\n\n"
        "`status` defaults to `pending`, which is what places the record on the "
        "agent's work queue (`GET /staging-records?status=pending`). "
        "`observations` may be supplied here but is normally omitted: the "
        "document has not been read yet."
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_staging_medical_record(
    payload: StagingMedicalRecordCreateSchema,
    staging_medical_record_service: StagingMedicalRecordService = Depends(
        get_staging_medical_record_service
    ),
):
    logger.info(
        "Register a source document for extraction",
        extra={"event": "route.create_staging_medical_record"},
    )
    log_payload(logger, "staging_medical_record.create.payload", payload)
    rec = await staging_medical_record_service.create_staging_medical_record(payload)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=jsonable_encoder(staging_medical_record_service._to_plain(rec)),
    )


# ── Read ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_staging_medical_records",
    summary="List staging records",
    description=(
        "Paginated, filtered and sorted. Every filter is an exact match except "
        "`attachment_title` (case-insensitive substring) and the "
        "`created_after`/`created_before` range, which is inclusive on both "
        "ends.\n\n"
        "The agent's work queue is `?status=pending`. Pass `total_mode=none` to "
        "skip the COUNT(*) when only the current page is needed — `total` then "
        "comes back null.\n\n"
        "Observations come back nested on every row; they are not themselves a "
        "query surface."
    ),
    responses=_LIST_200,
)
async def list_staging_medical_records(
    params: ListParams = Depends(),
    org_id: str | None = Query(None, description="Exact match on owning organization."),
    user_id: str | None = Query(None, description="Exact match on owning end user."),
    # `status` would shadow fastapi.status, which this module imports — hence
    # the rename plus alias, so the query-string name the caller sees is
    # still `status`.
    staging_status: StagingStatus | None = Query(
        None,
        alias="status",
        description="pending | processing | completed | failed.",
    ),
    file_id: str | None = Query(None, description="Exact match on filenest's file id."),
    patient_id: int | None = Query(None, ge=1, description="Public patient_id."),
    appointment_id: int | None = Query(
        None, ge=1, description="Public appointment_id."
    ),
    encounter_id: int | None = Query(None, ge=1, description="Public encounter_id."),
    service_request_id: int | None = Query(
        None, ge=1, description="Public service_request_id."
    ),
    diagnostic_report_id: int | None = Query(
        None, ge=1, description="Public diagnostic_report_id."
    ),
    attachment_title: str | None = Query(
        None, description="Case-insensitive substring match on the file name."
    ),
    created_after: datetime | None = Query(
        None, description="Inclusive lower bound on created_at."
    ),
    created_before: datetime | None = Query(
        None, description="Inclusive upper bound on created_at."
    ),
    staging_medical_record_service: StagingMedicalRecordService = Depends(
        get_staging_medical_record_service
    ),
):
    logger.info(
        "List staging records",
        extra={"event": "route.list_staging_medical_records"},
    )
    rows, total = await staging_medical_record_service.list_staging_medical_records(
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
        limit=params.limit,
        offset=params.offset,
        sort=params.sort,
        total_mode=params.total_mode,
    )
    return JSONResponse(
        content=jsonable_encoder(
            {
                "total": total,
                "limit": params.limit,
                "offset": params.offset,
                "data": [staging_medical_record_service._to_plain(r) for r in rows],
            }
        )
    )


@router.get(
    "/{staging_record_id}",
    operation_id="get_staging_medical_record_by_id",
    summary="Retrieve a staging record by public staging_record_id",
    description=(
        "Returns the record with its full staging_observation tree nested — including "
        "each staging_observation's components, reference ranges and codings."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_staging_medical_record(
    staging_record_id: int = Path(
        ..., ge=1, description="Public staging record identifier."
    ),
    staging_medical_record_service: StagingMedicalRecordService = Depends(
        get_staging_medical_record_service
    ),
):
    logger.info(
        "Retrieve a staging record by public staging_record_id",
        extra={
            "event": "route.get_staging_medical_record_by_id",
            "staging_record_id": staging_record_id,
        },
    )
    rec = await staging_medical_record_service.get_staging_medical_record(
        staging_record_id
    )
    return JSONResponse(
        content=jsonable_encoder(staging_medical_record_service._to_plain(rec))
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{staging_record_id}",
    operation_id="patch_staging_medical_record",
    summary="Update a staging record, and write back extracted observations",
    description=(
        "Applies only the fields present in the request body. This is the call "
        "the agent makes when it finishes: `status`, `processed_at`, and the "
        "`observations` it pulled out of the file — or `status: failed` with an "
        "`error_message`.\n\n"
        "⚠️ `observations` REPLACES the whole list. Sending the key deletes "
        "every existing staging_observation on this record and inserts what you sent; "
        "sending `[]` clears them. Omit the key entirely to leave them "
        "untouched — an omitted key and an explicit `[]` are different requests."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_staging_medical_record(
    payload: StagingMedicalRecordPatchSchema,
    staging_record_id: int = Path(
        ..., ge=1, description="Public staging record identifier."
    ),
    staging_medical_record_service: StagingMedicalRecordService = Depends(
        get_staging_medical_record_service
    ),
):
    logger.info(
        "Update a staging record",
        extra={
            "event": "route.patch_staging_medical_record",
            "staging_record_id": staging_record_id,
        },
    )
    log_payload(logger, "staging_medical_record.patch.payload", payload)
    rec = await staging_medical_record_service.patch_staging_medical_record(
        staging_record_id, payload
    )
    return JSONResponse(
        content=jsonable_encoder(staging_medical_record_service._to_plain(rec))
    )


# ── Review ─────────────────────────────────────────────────────────────────────


@router.patch(
    "/{staging_record_id}/review",
    operation_id="review_staging_medical_record",
    summary="Record a clinician's review decision",
    description=(
        "A doctor/practitioner accepts, rejects, or flags this record's "
        "extracted data as needing revision. Deliberately separate from the "
        "generic PATCH above — this is the clinician's write path, not the "
        "agent pipeline's. `reviewed_at` is always set server-side to the "
        "moment this request is processed."
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def review_staging_medical_record(
    payload: StagingReviewInput,
    staging_record_id: int = Path(
        ..., ge=1, description="Public staging record identifier."
    ),
    staging_medical_record_service: StagingMedicalRecordService = Depends(
        get_staging_medical_record_service
    ),
):
    logger.info(
        "Record a clinician's review decision",
        extra={
            "event": "route.review_staging_medical_record",
            "staging_record_id": staging_record_id,
        },
    )
    log_payload(logger, "staging_medical_record.review.payload", payload)
    rec = await staging_medical_record_service.review_staging_medical_record(
        staging_record_id, payload
    )
    return JSONResponse(
        content=jsonable_encoder(staging_medical_record_service._to_plain(rec))
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{staging_record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_staging_medical_record",
    summary="Delete a staging record",
    description=(
        "Removes the record and, by cascade, every staging_observation extracted from "
        "it. There is no soft-delete: this is a staging area, and a record that "
        "should not be promoted should not linger."
    ),
    responses={**_DELETE_204, **_ERR_NOT_FOUND},
)
async def delete_staging_medical_record(
    staging_record_id: int = Path(
        ..., ge=1, description="Public staging record identifier."
    ),
    staging_medical_record_service: StagingMedicalRecordService = Depends(
        get_staging_medical_record_service
    ),
):
    logger.info(
        "Delete a staging record",
        extra={
            "event": "route.delete_staging_medical_record",
            "staging_record_id": staging_record_id,
        },
    )
    await staging_medical_record_service.delete_staging_medical_record(
        staging_record_id
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
