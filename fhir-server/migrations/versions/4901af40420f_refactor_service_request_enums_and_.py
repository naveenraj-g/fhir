"""refactor_service_request_enums_and_identifier_fields

Revision ID: 4901af40420f
Revises: 7838e65a08c5
Create Date: 2026-05-15 20:33:10.779160

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '4901af40420f'
down_revision: Union[str, None] = '7838e65a08c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Declare all new enum types (TitleCase FHIR values)
_based_on_ref = postgresql.ENUM(
    'CarePlan', 'ServiceRequest', 'MedicationRequest',
    name='sr_based_on_ref_type',
)
_replaces_ref = postgresql.ENUM(
    'ServiceRequest',
    name='sr_replaces_ref_type',
)
_reason_ref = postgresql.ENUM(
    'Condition', 'Observation', 'DiagnosticReport', 'DocumentReference',
    name='sr_reason_ref_type',
)
_insurance_ref = postgresql.ENUM(
    'Coverage', 'ClaimResponse',
    name='sr_insurance_ref_type',
)
_location_ref = postgresql.ENUM(
    'Location',
    name='sr_location_ref_type',
)
_specimen_ref = postgresql.ENUM(
    'Specimen',
    name='sr_specimen_ref_type',
)
_relevant_history_ref = postgresql.ENUM(
    'Provenance',
    name='sr_relevant_history_ref_type',
)
_note_author_ref = postgresql.ENUM(
    'Practitioner', 'Patient', 'RelatedPerson', 'Organization',
    name='sr_note_author_ref_type',
)


def upgrade() -> None:
    bind = op.get_bind()

    # ── 1. Main table: new columns ────────────────────────────────────────────
    op.add_column('service_request', sa.Column('as_needed_text', sa.String(), nullable=True))
    op.add_column('service_request', sa.Column('requisition_use', sa.String(), nullable=True))
    op.add_column('service_request', sa.Column('requisition_type_system', sa.String(), nullable=True))
    op.add_column('service_request', sa.Column('requisition_type_code', sa.String(), nullable=True))
    op.add_column('service_request', sa.Column('requisition_type_display', sa.String(), nullable=True))
    op.add_column('service_request', sa.Column('requisition_type_text', sa.String(), nullable=True))
    op.add_column('service_request', sa.Column('requisition_period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('service_request', sa.Column('requisition_period_end', sa.DateTime(timezone=True), nullable=True))
    op.add_column('service_request', sa.Column('requisition_assigner', sa.String(), nullable=True))

    # ── 2. service_request_identifier: new columns ────────────────────────────
    op.add_column('service_request_identifier', sa.Column('type_system', sa.String(), nullable=True))
    op.add_column('service_request_identifier', sa.Column('type_code', sa.String(), nullable=True))
    op.add_column('service_request_identifier', sa.Column('type_display', sa.String(), nullable=True))
    op.add_column('service_request_identifier', sa.Column('type_text', sa.String(), nullable=True))
    op.add_column('service_request_identifier', sa.Column('period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('service_request_identifier', sa.Column('period_end', sa.DateTime(timezone=True), nullable=True))

    # ── 3. service_request_based_on: String → Enum ───────────────────────────
    _based_on_ref.create(bind, checkfirst=True)
    op.alter_column(
        'service_request_based_on', 'reference_type',
        existing_type=sa.VARCHAR(),
        type_=postgresql.ENUM('CarePlan', 'ServiceRequest', 'MedicationRequest',
                              name='sr_based_on_ref_type', create_type=False),
        existing_nullable=True,
        postgresql_using='reference_type::sr_based_on_ref_type',
    )

    # ── 4. service_request_replaces: drop old column, add uniform pattern ─────
    op.drop_column('service_request_replaces', 'replaced_service_request_id')
    _replaces_ref.create(bind, checkfirst=True)
    op.add_column('service_request_replaces', sa.Column(
        'reference_type',
        postgresql.ENUM('ServiceRequest', name='sr_replaces_ref_type', create_type=False),
        nullable=True,
    ))
    op.add_column('service_request_replaces', sa.Column('reference_id', sa.Integer(), nullable=True))

    # ── 5. service_request_reason_reference: String → Enum ───────────────────
    _reason_ref.create(bind, checkfirst=True)
    op.alter_column(
        'service_request_reason_reference', 'reference_type',
        existing_type=sa.VARCHAR(),
        type_=postgresql.ENUM('Condition', 'Observation', 'DiagnosticReport', 'DocumentReference',
                              name='sr_reason_ref_type', create_type=False),
        existing_nullable=True,
        postgresql_using='reference_type::sr_reason_ref_type',
    )

    # ── 6. service_request_insurance: String → Enum ──────────────────────────
    _insurance_ref.create(bind, checkfirst=True)
    op.alter_column(
        'service_request_insurance', 'reference_type',
        existing_type=sa.VARCHAR(),
        type_=postgresql.ENUM('Coverage', 'ClaimResponse',
                              name='sr_insurance_ref_type', create_type=False),
        existing_nullable=True,
        postgresql_using='reference_type::sr_insurance_ref_type',
    )

    # ── 7. service_request_location_reference: String(default="Location") → Enum
    # Existing rows have 'Location' stored; USING cast works directly.
    _location_ref.create(bind, checkfirst=True)
    op.alter_column(
        'service_request_location_reference', 'reference_type',
        existing_type=sa.VARCHAR(),
        type_=postgresql.ENUM('Location', name='sr_location_ref_type', create_type=False),
        existing_nullable=True,
        postgresql_using='reference_type::sr_location_ref_type',
    )

    # ── 8. service_request_specimen: String(default="Specimen") → Enum ───────
    _specimen_ref.create(bind, checkfirst=True)
    op.alter_column(
        'service_request_specimen', 'reference_type',
        existing_type=sa.VARCHAR(),
        type_=postgresql.ENUM('Specimen', name='sr_specimen_ref_type', create_type=False),
        existing_nullable=True,
        postgresql_using='reference_type::sr_specimen_ref_type',
    )

    # ── 9. service_request_relevant_history: String(default="Provenance") → Enum
    _relevant_history_ref.create(bind, checkfirst=True)
    op.alter_column(
        'service_request_relevant_history', 'reference_type',
        existing_type=sa.VARCHAR(),
        type_=postgresql.ENUM('Provenance', name='sr_relevant_history_ref_type', create_type=False),
        existing_nullable=True,
        postgresql_using='reference_type::sr_relevant_history_ref_type',
    )

    # ── 10. service_request_note: String → Enum + rename author_display ──────
    _note_author_ref.create(bind, checkfirst=True)
    op.alter_column(
        'service_request_note', 'author_reference_type',
        existing_type=sa.VARCHAR(),
        type_=postgresql.ENUM('Practitioner', 'Patient', 'RelatedPerson', 'Organization',
                              name='sr_note_author_ref_type', create_type=False),
        existing_nullable=True,
        postgresql_using='author_reference_type::sr_note_author_ref_type',
    )
    # Rename author_display → author_reference_display
    op.alter_column('service_request_note', 'author_display',
                    new_column_name='author_reference_display')


def downgrade() -> None:
    bind = op.get_bind()

    # ── Reverse note changes ──────────────────────────────────────────────────
    op.alter_column('service_request_note', 'author_reference_display',
                    new_column_name='author_display')
    op.alter_column(
        'service_request_note', 'author_reference_type',
        existing_type=postgresql.ENUM('Practitioner', 'Patient', 'RelatedPerson', 'Organization',
                                      name='sr_note_author_ref_type', create_type=False),
        type_=sa.VARCHAR(),
        existing_nullable=True,
    )
    _note_author_ref.drop(bind, checkfirst=True)

    # ── Reverse relevant_history ──────────────────────────────────────────────
    op.alter_column(
        'service_request_relevant_history', 'reference_type',
        existing_type=postgresql.ENUM('Provenance', name='sr_relevant_history_ref_type', create_type=False),
        type_=sa.VARCHAR(),
        existing_nullable=True,
    )
    _relevant_history_ref.drop(bind, checkfirst=True)

    # ── Reverse specimen ──────────────────────────────────────────────────────
    op.alter_column(
        'service_request_specimen', 'reference_type',
        existing_type=postgresql.ENUM('Specimen', name='sr_specimen_ref_type', create_type=False),
        type_=sa.VARCHAR(),
        existing_nullable=True,
    )
    _specimen_ref.drop(bind, checkfirst=True)

    # ── Reverse location_reference ────────────────────────────────────────────
    op.alter_column(
        'service_request_location_reference', 'reference_type',
        existing_type=postgresql.ENUM('Location', name='sr_location_ref_type', create_type=False),
        type_=sa.VARCHAR(),
        existing_nullable=True,
    )
    _location_ref.drop(bind, checkfirst=True)

    # ── Reverse insurance ─────────────────────────────────────────────────────
    op.alter_column(
        'service_request_insurance', 'reference_type',
        existing_type=postgresql.ENUM('Coverage', 'ClaimResponse',
                                      name='sr_insurance_ref_type', create_type=False),
        type_=sa.VARCHAR(),
        existing_nullable=True,
    )
    _insurance_ref.drop(bind, checkfirst=True)

    # ── Reverse reason_reference ──────────────────────────────────────────────
    op.alter_column(
        'service_request_reason_reference', 'reference_type',
        existing_type=postgresql.ENUM('Condition', 'Observation', 'DiagnosticReport', 'DocumentReference',
                                      name='sr_reason_ref_type', create_type=False),
        type_=sa.VARCHAR(),
        existing_nullable=True,
    )
    _reason_ref.drop(bind, checkfirst=True)

    # ── Reverse replaces ──────────────────────────────────────────────────────
    op.drop_column('service_request_replaces', 'reference_id')
    op.drop_column('service_request_replaces', 'reference_type')
    _replaces_ref.drop(bind, checkfirst=True)
    op.add_column('service_request_replaces',
                  sa.Column('replaced_service_request_id', sa.Integer(), nullable=True))

    # ── Reverse based_on ──────────────────────────────────────────────────────
    op.alter_column(
        'service_request_based_on', 'reference_type',
        existing_type=postgresql.ENUM('CarePlan', 'ServiceRequest', 'MedicationRequest',
                                      name='sr_based_on_ref_type', create_type=False),
        type_=sa.VARCHAR(),
        existing_nullable=True,
    )
    _based_on_ref.drop(bind, checkfirst=True)

    # ── Reverse identifier columns ────────────────────────────────────────────
    op.drop_column('service_request_identifier', 'period_end')
    op.drop_column('service_request_identifier', 'period_start')
    op.drop_column('service_request_identifier', 'type_text')
    op.drop_column('service_request_identifier', 'type_display')
    op.drop_column('service_request_identifier', 'type_code')
    op.drop_column('service_request_identifier', 'type_system')

    # ── Reverse main table columns ────────────────────────────────────────────
    op.drop_column('service_request', 'requisition_assigner')
    op.drop_column('service_request', 'requisition_period_end')
    op.drop_column('service_request', 'requisition_period_start')
    op.drop_column('service_request', 'requisition_type_text')
    op.drop_column('service_request', 'requisition_type_display')
    op.drop_column('service_request', 'requisition_type_code')
    op.drop_column('service_request', 'requisition_type_system')
    op.drop_column('service_request', 'requisition_use')
    op.drop_column('service_request', 'as_needed_text')
