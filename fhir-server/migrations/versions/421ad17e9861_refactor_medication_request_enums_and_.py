"""refactor_medication_request_enums_and_identifier_fields

Revision ID: 421ad17e9861
Revises: 4901af40420f
Create Date: 2026-05-15 21:07:56.088869

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '421ad17e9861'
down_revision: Union[str, None] = '4901af40420f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Declare all new enum types (TitleCase FHIR values)
_medication_ref = postgresql.ENUM('Medication', name='mr_medication_ref_type')
_prior_prescription = postgresql.ENUM('MedicationRequest', name='mr_prior_prescription_type')
_dispense_performer = postgresql.ENUM('Organization', name='mr_dispense_performer_type')
_based_on_ref = postgresql.ENUM(
    'CarePlan', 'MedicationRequest', 'ServiceRequest', 'ImmunizationRecommendation',
    name='mr_based_on_ref_type',
)
_reason_ref = postgresql.ENUM('Condition', 'Observation', name='mr_reason_ref_type')
_insurance_ref = postgresql.ENUM('Coverage', 'ClaimResponse', name='mr_insurance_ref_type')
_note_author_ref = postgresql.ENUM(
    'Practitioner', 'Patient', 'RelatedPerson', 'Organization',
    name='mr_note_author_ref_type',
)
_detected_issue_ref = postgresql.ENUM('DetectedIssue', name='mr_detected_issue_ref_type')
_event_history_ref = postgresql.ENUM('Provenance', name='mr_event_history_ref_type')


def upgrade() -> None:
    bind = op.get_bind()

    # ── 1. Main table: new columns ─────────────────────────────────────────────
    op.add_column('medication_request', sa.Column('group_identifier_use', sa.String(), nullable=True))
    op.add_column('medication_request', sa.Column('group_identifier_type_system', sa.String(), nullable=True))
    op.add_column('medication_request', sa.Column('group_identifier_type_code', sa.String(), nullable=True))
    op.add_column('medication_request', sa.Column('group_identifier_type_display', sa.String(), nullable=True))
    op.add_column('medication_request', sa.Column('group_identifier_type_text', sa.String(), nullable=True))
    op.add_column('medication_request', sa.Column('group_identifier_period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('medication_request', sa.Column('group_identifier_period_end', sa.DateTime(timezone=True), nullable=True))
    op.add_column('medication_request', sa.Column('group_identifier_assigner', sa.String(), nullable=True))
    op.add_column('medication_request', sa.Column('substitution_allowed_text', sa.String(), nullable=True))

    # prior_prescription_type — new column (no existing data to cast)
    _prior_prescription.create(bind, checkfirst=True)
    op.add_column('medication_request', sa.Column(
        'prior_prescription_type',
        postgresql.ENUM('MedicationRequest', name='mr_prior_prescription_type', create_type=False),
        nullable=True,
    ))

    # dispense_performer_type — new column (no existing data to cast)
    _dispense_performer.create(bind, checkfirst=True)
    op.add_column('medication_request', sa.Column(
        'dispense_performer_type',
        postgresql.ENUM('Organization', name='mr_dispense_performer_type', create_type=False),
        nullable=True,
    ))

    # ── 2. medication_reference_type: String(default="Medication") → Enum ─────
    # Existing rows have 'Medication' stored; USING cast works directly.
    _medication_ref.create(bind, checkfirst=True)
    op.alter_column(
        'medication_request', 'medication_reference_type',
        existing_type=sa.VARCHAR(),
        type_=postgresql.ENUM('Medication', name='mr_medication_ref_type', create_type=False),
        existing_nullable=True,
        postgresql_using='medication_reference_type::mr_medication_ref_type',
    )

    # ── 3. medication_request_identifier: new columns ─────────────────────────
    op.add_column('medication_request_identifier', sa.Column('type_system', sa.String(), nullable=True))
    op.add_column('medication_request_identifier', sa.Column('type_code', sa.String(), nullable=True))
    op.add_column('medication_request_identifier', sa.Column('type_display', sa.String(), nullable=True))
    op.add_column('medication_request_identifier', sa.Column('type_text', sa.String(), nullable=True))
    op.add_column('medication_request_identifier', sa.Column('period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('medication_request_identifier', sa.Column('period_end', sa.DateTime(timezone=True), nullable=True))

    # ── 4. medication_request_based_on: String → Enum ────────────────────────
    _based_on_ref.create(bind, checkfirst=True)
    op.alter_column(
        'medication_request_based_on', 'reference_type',
        existing_type=sa.VARCHAR(),
        type_=postgresql.ENUM(
            'CarePlan', 'MedicationRequest', 'ServiceRequest', 'ImmunizationRecommendation',
            name='mr_based_on_ref_type', create_type=False,
        ),
        existing_nullable=True,
        postgresql_using='reference_type::mr_based_on_ref_type',
    )

    # ── 5. medication_request_reason_reference: String → Enum ────────────────
    _reason_ref.create(bind, checkfirst=True)
    op.alter_column(
        'medication_request_reason_reference', 'reference_type',
        existing_type=sa.VARCHAR(),
        type_=postgresql.ENUM('Condition', 'Observation', name='mr_reason_ref_type', create_type=False),
        existing_nullable=True,
        postgresql_using='reference_type::mr_reason_ref_type',
    )

    # ── 6. medication_request_insurance: String → Enum ────────────────────────
    _insurance_ref.create(bind, checkfirst=True)
    op.alter_column(
        'medication_request_insurance', 'reference_type',
        existing_type=sa.VARCHAR(),
        type_=postgresql.ENUM('Coverage', 'ClaimResponse', name='mr_insurance_ref_type', create_type=False),
        existing_nullable=True,
        postgresql_using='reference_type::mr_insurance_ref_type',
    )

    # ── 7. medication_request_note: String → Enum + rename author_display ─────
    _note_author_ref.create(bind, checkfirst=True)
    op.alter_column(
        'medication_request_note', 'author_reference_type',
        existing_type=sa.VARCHAR(),
        type_=postgresql.ENUM(
            'Practitioner', 'Patient', 'RelatedPerson', 'Organization',
            name='mr_note_author_ref_type', create_type=False,
        ),
        existing_nullable=True,
        postgresql_using='author_reference_type::mr_note_author_ref_type',
    )
    op.alter_column('medication_request_note', 'author_display',
                    new_column_name='author_reference_display')

    # ── 8. medication_request_dosage_instruction: new column ──────────────────
    op.add_column('medication_request_dosage_instruction', sa.Column('as_needed_text', sa.String(), nullable=True))

    # ── 9. medication_request_detected_issue: String(default="DetectedIssue") → Enum
    _detected_issue_ref.create(bind, checkfirst=True)
    op.alter_column(
        'medication_request_detected_issue', 'reference_type',
        existing_type=sa.VARCHAR(),
        type_=postgresql.ENUM('DetectedIssue', name='mr_detected_issue_ref_type', create_type=False),
        existing_nullable=True,
        postgresql_using='reference_type::mr_detected_issue_ref_type',
    )

    # ── 10. medication_request_event_history: String(default="Provenance") → Enum
    _event_history_ref.create(bind, checkfirst=True)
    op.alter_column(
        'medication_request_event_history', 'reference_type',
        existing_type=sa.VARCHAR(),
        type_=postgresql.ENUM('Provenance', name='mr_event_history_ref_type', create_type=False),
        existing_nullable=True,
        postgresql_using='reference_type::mr_event_history_ref_type',
    )


def downgrade() -> None:
    bind = op.get_bind()

    # ── Reverse event_history ─────────────────────────────────────────────────
    op.alter_column(
        'medication_request_event_history', 'reference_type',
        existing_type=postgresql.ENUM('Provenance', name='mr_event_history_ref_type', create_type=False),
        type_=sa.VARCHAR(),
        existing_nullable=True,
    )
    _event_history_ref.drop(bind, checkfirst=True)

    # ── Reverse detected_issue ────────────────────────────────────────────────
    op.alter_column(
        'medication_request_detected_issue', 'reference_type',
        existing_type=postgresql.ENUM('DetectedIssue', name='mr_detected_issue_ref_type', create_type=False),
        type_=sa.VARCHAR(),
        existing_nullable=True,
    )
    _detected_issue_ref.drop(bind, checkfirst=True)

    # ── Reverse dosage as_needed_text ─────────────────────────────────────────
    op.drop_column('medication_request_dosage_instruction', 'as_needed_text')

    # ── Reverse note ──────────────────────────────────────────────────────────
    op.alter_column('medication_request_note', 'author_reference_display',
                    new_column_name='author_display')
    op.alter_column(
        'medication_request_note', 'author_reference_type',
        existing_type=postgresql.ENUM(
            'Practitioner', 'Patient', 'RelatedPerson', 'Organization',
            name='mr_note_author_ref_type', create_type=False,
        ),
        type_=sa.VARCHAR(),
        existing_nullable=True,
    )
    _note_author_ref.drop(bind, checkfirst=True)

    # ── Reverse insurance ─────────────────────────────────────────────────────
    op.alter_column(
        'medication_request_insurance', 'reference_type',
        existing_type=postgresql.ENUM('Coverage', 'ClaimResponse', name='mr_insurance_ref_type', create_type=False),
        type_=sa.VARCHAR(),
        existing_nullable=True,
    )
    _insurance_ref.drop(bind, checkfirst=True)

    # ── Reverse reason_reference ──────────────────────────────────────────────
    op.alter_column(
        'medication_request_reason_reference', 'reference_type',
        existing_type=postgresql.ENUM('Condition', 'Observation', name='mr_reason_ref_type', create_type=False),
        type_=sa.VARCHAR(),
        existing_nullable=True,
    )
    _reason_ref.drop(bind, checkfirst=True)

    # ── Reverse based_on ──────────────────────────────────────────────────────
    op.alter_column(
        'medication_request_based_on', 'reference_type',
        existing_type=postgresql.ENUM(
            'CarePlan', 'MedicationRequest', 'ServiceRequest', 'ImmunizationRecommendation',
            name='mr_based_on_ref_type', create_type=False,
        ),
        type_=sa.VARCHAR(),
        existing_nullable=True,
    )
    _based_on_ref.drop(bind, checkfirst=True)

    # ── Reverse identifier columns ─────────────────────────────────────────────
    op.drop_column('medication_request_identifier', 'period_end')
    op.drop_column('medication_request_identifier', 'period_start')
    op.drop_column('medication_request_identifier', 'type_text')
    op.drop_column('medication_request_identifier', 'type_display')
    op.drop_column('medication_request_identifier', 'type_code')
    op.drop_column('medication_request_identifier', 'type_system')

    # ── Reverse medication_reference_type ──────────────────────────────────────
    op.alter_column(
        'medication_request', 'medication_reference_type',
        existing_type=postgresql.ENUM('Medication', name='mr_medication_ref_type', create_type=False),
        type_=sa.VARCHAR(),
        existing_nullable=True,
    )
    _medication_ref.drop(bind, checkfirst=True)

    # ── Reverse main table new columns ─────────────────────────────────────────
    op.drop_column('medication_request', 'dispense_performer_type')
    _dispense_performer.drop(bind, checkfirst=True)
    op.drop_column('medication_request', 'prior_prescription_type')
    _prior_prescription.drop(bind, checkfirst=True)
    op.drop_column('medication_request', 'substitution_allowed_text')
    op.drop_column('medication_request', 'group_identifier_assigner')
    op.drop_column('medication_request', 'group_identifier_period_end')
    op.drop_column('medication_request', 'group_identifier_period_start')
    op.drop_column('medication_request', 'group_identifier_type_text')
    op.drop_column('medication_request', 'group_identifier_type_display')
    op.drop_column('medication_request', 'group_identifier_type_code')
    op.drop_column('medication_request', 'group_identifier_type_system')
    op.drop_column('medication_request', 'group_identifier_use')
