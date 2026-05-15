"""refactor_device_request_enums_and_identifier_fields

Revision ID: 74f166a2b077
Revises: 60bbcdee864b
Create Date: 2026-05-15 22:54:41.294324

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '74f166a2b077'
down_revision: Union[str, None] = '60bbcdee864b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_code_ref_type = postgresql.ENUM('Device', name='dr_code_ref_type')
_insurance_ref_type = postgresql.ENUM('Coverage', 'ClaimResponse', name='dr_insurance_ref_type')
_note_author_ref_type = postgresql.ENUM(
    'Practitioner', 'Patient', 'RelatedPerson', 'Organization',
    name='dr_note_author_ref_type',
)
_reason_ref_type = postgresql.ENUM(
    'Condition', 'Observation', 'DiagnosticReport', 'DocumentReference',
    name='dr_reason_ref_type',
)
_relevant_history_ref_type = postgresql.ENUM('Provenance', name='dr_relevant_history_ref_type')


def upgrade() -> None:
    bind = op.get_bind()

    # ── 1. device_request: add missing groupIdentifier Identifier columns ─────
    op.add_column('device_request', sa.Column('group_identifier_type_system', sa.String(), nullable=True))
    op.add_column('device_request', sa.Column('group_identifier_type_code', sa.String(), nullable=True))
    op.add_column('device_request', sa.Column('group_identifier_type_display', sa.String(), nullable=True))
    op.add_column('device_request', sa.Column('group_identifier_type_text', sa.String(), nullable=True))
    op.add_column('device_request', sa.Column('group_identifier_period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('device_request', sa.Column('group_identifier_period_end', sa.DateTime(timezone=True), nullable=True))
    op.add_column('device_request', sa.Column('group_identifier_assigner', sa.String(), nullable=True))

    # ── 2. device_request: code_reference_type VARCHAR → Enum ────────────────
    _code_ref_type.create(bind, checkfirst=True)
    op.alter_column(
        'device_request', 'code_reference_type',
        existing_type=sa.VARCHAR(),
        type_=postgresql.ENUM('Device', name='dr_code_ref_type', create_type=False),
        existing_nullable=True,
        postgresql_using='code_reference_type::dr_code_ref_type',
    )

    # ── 3. device_request_identifier: add type_text ───────────────────────────
    op.add_column('device_request_identifier', sa.Column('type_text', sa.String(), nullable=True))

    # ── 4. device_request_insurance: reference_type VARCHAR → Enum ───────────
    _insurance_ref_type.create(bind, checkfirst=True)
    op.alter_column(
        'device_request_insurance', 'reference_type',
        existing_type=sa.VARCHAR(),
        type_=postgresql.ENUM('Coverage', 'ClaimResponse', name='dr_insurance_ref_type', create_type=False),
        existing_nullable=True,
        postgresql_using='reference_type::dr_insurance_ref_type',
    )

    # ── 5. device_request_note: author_reference_type VARCHAR → Enum ─────────
    _note_author_ref_type.create(bind, checkfirst=True)
    op.alter_column(
        'device_request_note', 'author_reference_type',
        existing_type=sa.VARCHAR(),
        type_=postgresql.ENUM(
            'Practitioner', 'Patient', 'RelatedPerson', 'Organization',
            name='dr_note_author_ref_type', create_type=False,
        ),
        existing_nullable=True,
        postgresql_using='author_reference_type::dr_note_author_ref_type',
    )

    # ── 6. device_request_note: rename author_display → author_reference_display
    op.alter_column('device_request_note', 'author_display',
                    new_column_name='author_reference_display')

    # ── 7. device_request_reason_reference: reference_type VARCHAR → Enum ─────
    _reason_ref_type.create(bind, checkfirst=True)
    op.alter_column(
        'device_request_reason_reference', 'reference_type',
        existing_type=sa.VARCHAR(),
        type_=postgresql.ENUM(
            'Condition', 'Observation', 'DiagnosticReport', 'DocumentReference',
            name='dr_reason_ref_type', create_type=False,
        ),
        existing_nullable=True,
        postgresql_using='reference_type::dr_reason_ref_type',
    )

    # ── 8. device_request_relevant_history: reference_type VARCHAR → Enum ─────
    _relevant_history_ref_type.create(bind, checkfirst=True)
    op.alter_column(
        'device_request_relevant_history', 'reference_type',
        existing_type=sa.VARCHAR(),
        type_=postgresql.ENUM('Provenance', name='dr_relevant_history_ref_type', create_type=False),
        existing_nullable=True,
        postgresql_using='reference_type::dr_relevant_history_ref_type',
    )


def downgrade() -> None:
    bind = op.get_bind()

    # ── Reverse relevant_history enum ─────────────────────────────────────────
    op.alter_column(
        'device_request_relevant_history', 'reference_type',
        existing_type=postgresql.ENUM('Provenance', name='dr_relevant_history_ref_type', create_type=False),
        type_=sa.VARCHAR(),
        existing_nullable=True,
    )
    _relevant_history_ref_type.drop(bind, checkfirst=True)

    # ── Reverse reason_reference enum ─────────────────────────────────────────
    op.alter_column(
        'device_request_reason_reference', 'reference_type',
        existing_type=postgresql.ENUM(
            'Condition', 'Observation', 'DiagnosticReport', 'DocumentReference',
            name='dr_reason_ref_type', create_type=False,
        ),
        type_=sa.VARCHAR(),
        existing_nullable=True,
    )
    _reason_ref_type.drop(bind, checkfirst=True)

    # ── Reverse note rename ───────────────────────────────────────────────────
    op.alter_column('device_request_note', 'author_reference_display',
                    new_column_name='author_display')

    # ── Reverse note author_reference_type enum ───────────────────────────────
    op.alter_column(
        'device_request_note', 'author_reference_type',
        existing_type=postgresql.ENUM(
            'Practitioner', 'Patient', 'RelatedPerson', 'Organization',
            name='dr_note_author_ref_type', create_type=False,
        ),
        type_=sa.VARCHAR(),
        existing_nullable=True,
    )
    _note_author_ref_type.drop(bind, checkfirst=True)

    # ── Reverse insurance enum ────────────────────────────────────────────────
    op.alter_column(
        'device_request_insurance', 'reference_type',
        existing_type=postgresql.ENUM('Coverage', 'ClaimResponse', name='dr_insurance_ref_type', create_type=False),
        type_=sa.VARCHAR(),
        existing_nullable=True,
    )
    _insurance_ref_type.drop(bind, checkfirst=True)

    # ── Reverse identifier type_text ──────────────────────────────────────────
    op.drop_column('device_request_identifier', 'type_text')

    # ── Reverse code_reference_type enum ─────────────────────────────────────
    op.alter_column(
        'device_request', 'code_reference_type',
        existing_type=postgresql.ENUM('Device', name='dr_code_ref_type', create_type=False),
        type_=sa.VARCHAR(),
        existing_nullable=True,
    )
    _code_ref_type.drop(bind, checkfirst=True)

    # ── Reverse groupIdentifier columns ──────────────────────────────────────
    op.drop_column('device_request', 'group_identifier_assigner')
    op.drop_column('device_request', 'group_identifier_period_end')
    op.drop_column('device_request', 'group_identifier_period_start')
    op.drop_column('device_request', 'group_identifier_type_text')
    op.drop_column('device_request', 'group_identifier_type_display')
    op.drop_column('device_request', 'group_identifier_type_code')
    op.drop_column('device_request', 'group_identifier_type_system')
