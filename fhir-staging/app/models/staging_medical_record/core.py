"""The staging record — one source document handed to the AI agent.

Holds three things: where the file is (a flattened FHIR R4 Attachment plus the
filenest handle), what clinical context it belongs to (patient, encounter,
service request, …), and how extraction went (status, error, timestamps). The
Observations the agent pulls out of the file hang off `observations`.

Every column is nullable by design for now. The agent's real output shape isn't
settled yet, and a NOT NULL constraint added early is a migration to undo
later; tightening them once the flow is proven is the cheaper direction.
"""

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    Sequence,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import StagingBase as Base
from app.models.enums import StagingReviewStatus, StagingStatus

staging_medical_record_id_seq = Sequence(
    "staging_medical_record_pub_seq", start=10000, increment=1, metadata=Base.metadata
)


class StagingMedicalRecordModel(Base):
    __tablename__ = "staging_record"

    # `id` is DB-internal and never leaves this service. `staging_medical_record_id` is
    # the public handle every API response and every caller uses.
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    staging_medical_record_id = Column(
        BigInteger,
        staging_medical_record_id_seq,
        server_default=staging_medical_record_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # ── Attachment (flattened FHIR R4 Attachment datatype) ───────────────────
    # https://www.hl7.org/fhir/R4/datatypes.html#Attachment
    # Three of these are what filenest returns as file metadata:
    #   mimetype -> attachment_content_type
    #   name     -> attachment_title
    #   size     -> attachment_size
    attachment_content_type = Column(String, nullable=True)
    attachment_language = Column(String, nullable=True)
    attachment_data = Column(Text, nullable=True)  # base64Binary, inline
    attachment_url = Column(String, nullable=True)
    attachment_size = Column(BigInteger, nullable=True)  # unsignedInt in R4
    attachment_hash = Column(String, nullable=True)  # base64Binary sha1
    attachment_title = Column(String, nullable=True)
    attachment_creation = Column(DateTime(timezone=True), nullable=True)

    # filenest's own opaque handle for the file. Distinct from attachment_url:
    # filenest hands back an id plus metadata, not necessarily a fetchable URL,
    # and the agent needs the id to ask filenest for the bytes.
    file_id = Column(String, nullable=True, index=True)

    # ── Tenancy / ownership ──────────────────────────────────────────────────
    # Plain forwarded input fields, not derived from a token — this service
    # does not authenticate. Same contract as fhir-server's gateway-trusted
    # resources.
    org_id = Column(String, nullable=True, index=True)
    user_id = Column(String, nullable=True, index=True)

    # ── Clinical context ─────────────────────────────────────────────────────
    # Public sequence ids belonging to *fhir-server*, not rows in this
    # database — so no ForeignKey, and nothing local to validate them against.
    patient_id = Column(BigInteger, nullable=True, index=True)
    appointment_id = Column(BigInteger, nullable=True, index=True)
    encounter_id = Column(BigInteger, nullable=True, index=True)
    service_request_id = Column(BigInteger, nullable=True, index=True)
    diagnostic_report_id = Column(BigInteger, nullable=True, index=True)

    # ── Extraction pipeline state ────────────────────────────────────────────
    status = Column(
        Enum(StagingStatus, name="staging_status"),
        nullable=True,
        index=True,
        default=StagingStatus.pending,
    )
    error_message = Column(Text, nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    summary = Column(String, nullable=True)

    # ── Clinician review ──────────────────────────────────────────────────────
    # Separate from `status` above: `status` tracks whether the AGENT finished
    # extracting data; `review_status` tracks whether a CLINICIAN has since
    # accepted, rejected, or asked for a revision of that extracted data. This
    # is the whole reason a "staging" area needs to exist rather than writing
    # extracted Observations straight into fhir-server. `reviewed_by` is a
    # trusted caller-supplied practitioner/user id — same trust model as every
    # other *_id/*_by column in this service (no auth).
    review_status = Column(
        Enum(StagingReviewStatus, name="staging_review_status"),
        nullable=True,
        index=True,
        default=StagingReviewStatus.pending_review,
    )
    reviewed_by = Column(String, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_notes = Column(Text, nullable=True)

    # ── Audit ────────────────────────────────────────────────────────────────
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)

    observations = relationship(
        "StagingObservationModel",
        back_populates="staging_medical_record",
        cascade="all, delete-orphan",
    )
