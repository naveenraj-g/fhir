from enum import Enum


class EncounterReferenceType(str, Enum):
    """Shared enum for any FHIR field whose only allowed reference type is
    Encounter. Stored as DB type name 'encounter_reference_type'.

    Note this service creates the type itself — fhir-server declares the same
    column with `create_type=False` because there several resources share one
    PostgreSQL type and only the first migration may create it. Here only
    Observation uses it, in this service's own database, so there is nothing to
    coordinate with and the plain form is correct.
    """

    Encounter = "Encounter"


class StagingStatus(str, Enum):
    """Where a staging record is in the extraction pipeline.

    Not a FHIR element — this is this service's own workflow state, and what
    makes `GET /staging-records?status=pending` a usable work queue for the
    agent. It also separates "extracted, found nothing" (completed with zero
    observations) from "blew up" (failed, with error_message set), which a
    nullable observations list alone cannot express.
    """

    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class StagingReviewStatus(str, Enum):
    """Clinician sign-off state — independent of the pipeline's `status`.

    A record can be pipeline-`completed` (the agent finished extracting data)
    while still `pending_review` (no clinician has looked at it yet). Two
    separate columns rather than one combined state machine, because "did
    extraction succeed" and "did a human accept the result" are different
    questions asked by different callers (the agent vs. a doctor/practitioner
    reviewing the staged data before anything is promoted).
    """

    pending_review = "pending_review"
    accepted = "accepted"
    rejected = "rejected"
    needs_revision = "needs_revision"
