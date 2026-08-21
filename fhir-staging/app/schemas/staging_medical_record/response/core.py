"""Response schemas for a staging record.

Plain snake_case only — this service has no FHIR wire format, so there is no
camelCase twin and no Bundle. These models exist to document the OpenAPI
contract; the routers return JSONResponse directly (see the `_responses.py`
constants), so nothing here validates or filters a real response at runtime.
"""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .staging_observation import PlainStagingObservationResponse


class PlainStagingMedicalRecordResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int = Field(
        ..., description="Public staging_medical_record_id. The internal PK is never exposed."
    )

    # ── Attachment (flattened FHIR R4 Attachment) ────────────────────────────
    attachment_content_type: Optional[str] = None
    attachment_language: Optional[str] = None
    attachment_data: Optional[str] = None
    attachment_url: Optional[str] = None
    attachment_size: Optional[int] = None
    attachment_hash: Optional[str] = None
    attachment_title: Optional[str] = None
    attachment_creation: Optional[str] = None

    file_id: Optional[str] = Field(None, description="filenest's opaque file id.")

    # ── Tenancy / ownership ──────────────────────────────────────────────────
    org_id: Optional[str] = None
    user_id: Optional[str] = None

    # ── Clinical context (public ids in fhir-server) ─────────────────────────
    patient_id: Optional[int] = None
    appointment_id: Optional[int] = None
    encounter_id: Optional[int] = None
    service_request_id: Optional[int] = None
    diagnostic_report_id: Optional[int] = None

    # ── Extraction pipeline state ────────────────────────────────────────────
    status: Optional[str] = Field(
        None, description="pending | processing | completed | failed"
    )
    error_message: Optional[str] = None
    processed_at: Optional[str] = None
    summary: Optional[str] = None

    # ── Clinician review ──────────────────────────────────────────────────────
    review_status: Optional[str] = Field(
        None, description="pending_review | accepted | rejected | needs_revision"
    )
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    review_notes: Optional[str] = None

    # ── Audit ────────────────────────────────────────────────────────────────
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    observations: Optional[List[PlainStagingObservationResponse]] = Field(
        None, description="Observations the agent extracted from this document."
    )


class PaginatedStagingMedicalRecordResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    total: Optional[int] = Field(
        None,
        description=(
            "Total matching rows. Null when the request passed "
            "total_mode=none, which skips the COUNT(*) entirely."
        ),
    )
    limit: int = Field(..., description="Page size that was applied.")
    offset: int = Field(..., description="Number of rows skipped.")
    data: List[PlainStagingMedicalRecordResponse] = Field(..., description="The current page.")
