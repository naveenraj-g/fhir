"""Serialize a StagingMedicalRecordModel to the plain snake_case dict the API returns.

`id` is the PUBLIC staging_medical_record_id, never the internal PK — that column does
not leave this service. Same convention as fhir-server's plain mappers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.serializers.staging_observation import to_plain_staging_observation

if TYPE_CHECKING:
    from app.models.staging_medical_record.core import StagingMedicalRecordModel


def to_plain_staging_medical_record(rec: "StagingMedicalRecordModel") -> dict:
    return {
        "id": rec.staging_medical_record_id,
        # Attachment (flattened FHIR R4 Attachment)
        "attachment_content_type": rec.attachment_content_type,
        "attachment_language": rec.attachment_language,
        "attachment_data": rec.attachment_data,
        "attachment_url": rec.attachment_url,
        "attachment_size": rec.attachment_size,
        "attachment_hash": rec.attachment_hash,
        "attachment_title": rec.attachment_title,
        "attachment_creation": (
            rec.attachment_creation.isoformat() if rec.attachment_creation else None
        ),
        "file_id": rec.file_id,
        # Tenancy / ownership
        "org_id": rec.org_id,
        "user_id": rec.user_id,
        # Clinical context — public ids in fhir-server
        "patient_id": rec.patient_id,
        "appointment_id": rec.appointment_id,
        "encounter_id": rec.encounter_id,
        "service_request_id": rec.service_request_id,
        "diagnostic_report_id": rec.diagnostic_report_id,
        # Extraction pipeline state
        "status": rec.status.value if rec.status else None,
        "error_message": rec.error_message,
        "processed_at": rec.processed_at.isoformat() if rec.processed_at else None,
        "summary": rec.summary,
        # Clinician review
        "review_status": rec.review_status.value if rec.review_status else None,
        "reviewed_by": rec.reviewed_by,
        "reviewed_at": rec.reviewed_at.isoformat() if rec.reviewed_at else None,
        "review_notes": rec.review_notes,
        # Audit
        "created_at": rec.created_at.isoformat() if rec.created_at else None,
        "updated_at": rec.updated_at.isoformat() if rec.updated_at else None,
        "created_by": rec.created_by,
        "updated_by": rec.updated_by,
        # An empty list and "not extracted yet" are different states, and the
        # difference is the whole point of this table — so [] stays [], not None.
        "observations": [
            to_plain_staging_observation(o, staging_medical_record_id=rec.staging_medical_record_id)
            for o in rec.observations
        ],
    }
