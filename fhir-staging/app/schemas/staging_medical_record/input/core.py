"""Create and patch schemas for a staging record.

Both accept the extracted `observations` list inline — observations are not
separately addressable in this API, so the staging record is the only unit of
write. See StagingMedicalRecordPatchSchema's docstring for the replace semantics.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import StagingReviewStatus, StagingStatus

from .staging_observation import StagingObservationInput

_ATTACHMENT_DESCRIPTIONS = {
    "attachment_content_type": (
        "Mime type of the content, with charset etc. This is filenest's "
        "`mimetype` (e.g. 'application/pdf')."
    ),
    "attachment_language": "Human language of the content (BCP-47, e.g. 'en-US').",
    "attachment_data": "Inline base64-encoded data. Usually left empty — the bytes live in filenest.",
    "attachment_url": "URI where the data can be found.",
    "attachment_size": "Number of bytes of content. This is filenest's `size`.",
    "attachment_hash": "Base64-encoded SHA-1 hash of the data, for integrity checking.",
    "attachment_title": "Label to display in place of the data. This is filenest's `name`.",
    "attachment_creation": "Date the attachment was first created.",
}


class _StagingMedicalRecordFields(BaseModel):
    """Every writable column, all optional — shared by create and patch.

    Create and patch take exactly the same field set here because nothing on
    this table is immutable: a record can be re-pointed at a different file or
    re-associated with a different encounter as the agent learns more. The two
    schemas differ only in their staging_observation semantics and their examples.
    """

    # ── Attachment (flattened FHIR R4 Attachment) ────────────────────────────
    attachment_content_type: Optional[str] = Field(
        None, description=_ATTACHMENT_DESCRIPTIONS["attachment_content_type"]
    )
    attachment_language: Optional[str] = Field(
        None, description=_ATTACHMENT_DESCRIPTIONS["attachment_language"]
    )
    attachment_data: Optional[str] = Field(
        None, description=_ATTACHMENT_DESCRIPTIONS["attachment_data"]
    )
    attachment_url: Optional[str] = Field(
        None, description=_ATTACHMENT_DESCRIPTIONS["attachment_url"]
    )
    attachment_size: Optional[int] = Field(
        None, ge=0, description=_ATTACHMENT_DESCRIPTIONS["attachment_size"]
    )
    attachment_hash: Optional[str] = Field(
        None, description=_ATTACHMENT_DESCRIPTIONS["attachment_hash"]
    )
    attachment_title: Optional[str] = Field(
        None, description=_ATTACHMENT_DESCRIPTIONS["attachment_title"]
    )
    attachment_creation: Optional[datetime] = Field(
        None, description=_ATTACHMENT_DESCRIPTIONS["attachment_creation"]
    )

    file_id: Optional[str] = Field(
        None,
        description=(
            "filenest's opaque id for the file. This is what the agent hands "
            "back to filenest to fetch the bytes; the name/mimetype/size that "
            "come with it belong in the attachment_* fields above."
        ),
    )

    # ── Tenancy / ownership ──────────────────────────────────────────────────
    org_id: Optional[str] = Field(
        None,
        description=(
            "Owning organization. A plain forwarded field — this service does "
            "not authenticate, so it is trusted as given."
        ),
    )
    user_id: Optional[str] = Field(None, description="Owning end user.")

    # ── Clinical context ─────────────────────────────────────────────────────
    # Public sequence ids from fhir-server. Nothing in this database to check
    # them against, so they are accepted as given.
    patient_id: Optional[int] = Field(
        None, description="Public patient_id in fhir-server (e.g. 10001)."
    )
    appointment_id: Optional[int] = Field(
        None, description="Public appointment_id in fhir-server (e.g. 40001)."
    )
    encounter_id: Optional[int] = Field(
        None, description="Public encounter_id in fhir-server (e.g. 20001)."
    )
    service_request_id: Optional[int] = Field(
        None,
        description=(
            "Public service_request_id in fhir-server (e.g. 80001) — the order "
            "this medical record was produced against."
        ),
    )
    diagnostic_report_id: Optional[int] = Field(
        None, description="Public diagnostic_report_id in fhir-server (e.g. 110001)."
    )

    # ── Extraction pipeline state ────────────────────────────────────────────
    status: Optional[StagingStatus] = Field(
        None,
        description=(
            "Where this record is in the pipeline. Defaults to 'pending' on "
            "create. Query it with GET ?status=pending to get the agent's "
            "work queue."
        ),
    )
    error_message: Optional[str] = Field(
        None, description="Why extraction failed. Set alongside status='failed'."
    )
    processed_at: Optional[datetime] = Field(
        None, description="When the agent finished processing this record."
    )
    summary: Optional[str] = Field(
        None, description="Agent-written summary of the document's contents."
    )


class StagingMedicalRecordCreateSchema(_StagingMedicalRecordFields):
    """Registers a source document for extraction.

    Typically posted with the file details and clinical context but no
    `observations` — the agent fills those in later via PATCH. Status defaults
    to 'pending' when omitted, which is what puts the record on the queue.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "file_id": "f_01HQ8X2K9Z",
                "attachment_title": "cbc-panel-2026-08-01.pdf",
                "attachment_content_type": "application/pdf",
                "attachment_size": 248193,
                "org_id": "org-uuid-456",
                "user_id": "user-uuid-123",
                "patient_id": 10001,
                "encounter_id": 20001,
                "service_request_id": 80001,
                "status": "pending",
                "created_by": "agent-intake",
            }
        },
    )

    created_by: Optional[str] = Field(
        None, description="Acting user or system that created this record."
    )

    observations: Optional[List[StagingObservationInput]] = Field(
        None,
        description=(
            "Extracted observations. Usually omitted at create time — the "
            "document has not been processed yet."
        ),
    )


class StagingMedicalRecordPatchSchema(_StagingMedicalRecordFields):
    """Partial update. Only the fields actually present in the body are applied.

    This is the call the agent makes when it finishes: status, processed_at,
    and the observations it pulled out of the file.

    ⚠️ `observations` is REPLACE, not append. Sending the key at all deletes
    every existing staging_observation on this record and inserts what you sent;
    sending `[]` deletes them all. Omit the key entirely to leave them
    untouched. That distinction is what `exclude_unset=True` buys — an omitted
    key and an explicit `[]` are different requests.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "status": "completed",
                "processed_at": "2026-08-13T10:15:00Z",
                "updated_by": "agent-extractor",
                "observations": [
                    {
                        "status": "final",
                        "code_system": "http://loinc.org",
                        "code_code": "718-7",
                        "code_display": "Hemoglobin [Mass/volume] in Blood",
                        "subject": "Patient/10001",
                        "effective_date_time": "2026-08-01T09:00:00Z",
                        "value_quantity_value": 13.5,
                        "value_quantity_unit": "g/dL",
                        "value_quantity_system": "http://unitsofmeasure.org",
                        "value_quantity_code": "g/dL",
                        "category": [
                            {
                                "coding_system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                "coding_code": "laboratory",
                                "coding_display": "Laboratory",
                            }
                        ],
                        "reference_range": [
                            {
                                "low_value": 13.0,
                                "low_unit": "g/dL",
                                "high_value": 17.0,
                                "high_unit": "g/dL",
                                "text": "13.0-17.0 g/dL",
                            }
                        ],
                    }
                ],
            }
        },
    )

    updated_by: Optional[str] = Field(
        None, description="Acting user or system applying this update."
    )

    observations: Optional[List[StagingObservationInput]] = Field(
        None,
        description=(
            "Replaces the record's entire observation list. Omit to leave the "
            "existing observations alone; send [] to clear them."
        ),
    )


class StagingReviewInput(BaseModel):
    """A clinician's accept/reject/needs-revision decision on this record's
    extracted data.

    Deliberately a separate schema from StagingMedicalRecordPatchSchema above,
    all the way down to its own repository method and router endpoint — the
    agent pipeline and a doctor/practitioner reviewing the result are two
    different callers writing two different kinds of fact, and collapsing them
    into one PATCH body would let an agent retry accidentally overwrite a
    clinician's review (or vice versa).
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "review_status": "accepted",
                "reviewed_by": "practitioner-42",
                "review_notes": "Values look consistent with the prior panel.",
            }
        },
    )

    review_status: StagingReviewStatus = Field(
        ..., description="accepted | rejected | needs_revision | pending_review."
    )
    reviewed_by: Optional[str] = Field(
        None, description="Acting practitioner or user id. Trusted as given — no auth."
    )
    review_notes: Optional[str] = Field(
        None, description="Free-text comment, most useful on rejected/needs_revision."
    )
