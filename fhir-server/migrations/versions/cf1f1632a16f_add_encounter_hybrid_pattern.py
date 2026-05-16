"""add_encounter_hybrid_pattern

Revision ID: cf1f1632a16f
Revises: 004f6197e7ca
Create Date: 2026-05-17 00:03:30.370571

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'cf1f1632a16f'
down_revision: Union[str, None] = '004f6197e7ca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_encounter_ref_type = postgresql.ENUM('Encounter', name='encounter_reference_type')


def upgrade() -> None:
    _encounter_ref_type.create(op.get_bind(), checkfirst=True)

    # ── observation_identifier (detected as missing table) ────────────────────
    op.create_table(
        'observation_identifier',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('observation_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('use', sa.String(), nullable=True),
        sa.Column('type_system', sa.String(), nullable=True),
        sa.Column('type_code', sa.String(), nullable=True),
        sa.Column('type_display', sa.String(), nullable=True),
        sa.Column('type_text', sa.String(), nullable=True),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('value', sa.String(), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('assigner', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['observation_id'], ['observation.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_observation_identifier_observation_id'),
        'observation_identifier', ['observation_id'], unique=False,
    )

    # ── encounter_type + encounter_display on FK-based models ─────────────────
    _enc_col = postgresql.ENUM('Encounter', name='encounter_reference_type', create_type=False)

    op.add_column('appointment', sa.Column('encounter_type', _enc_col, nullable=True))
    op.add_column('appointment', sa.Column('encounter_display', sa.String(), nullable=True))

    op.add_column('condition', sa.Column('encounter_type', _enc_col, nullable=True))
    op.add_column('condition', sa.Column('encounter_display', sa.String(), nullable=True))

    op.add_column('device_request', sa.Column('encounter_type', _enc_col, nullable=True))
    op.add_column('device_request', sa.Column('encounter_display', sa.String(), nullable=True))

    op.add_column('diagnostic_report', sa.Column('encounter_type', _enc_col, nullable=True))
    op.add_column('diagnostic_report', sa.Column('encounter_display', sa.String(), nullable=True))

    op.add_column('medication_request', sa.Column('encounter_type', _enc_col, nullable=True))
    op.add_column('medication_request', sa.Column('encounter_display', sa.String(), nullable=True))

    op.add_column('procedure', sa.Column('encounter_type', _enc_col, nullable=True))
    op.add_column('procedure', sa.Column('encounter_display', sa.String(), nullable=True))

    op.add_column('questionnaire_response', sa.Column('encounter_type', _enc_col, nullable=True))
    op.add_column('questionnaire_response', sa.Column('encounter_display', sa.String(), nullable=True))

    op.add_column('service_request', sa.Column('encounter_type', _enc_col, nullable=True))
    op.add_column('service_request', sa.Column('encounter_display', sa.String(), nullable=True))

    # ── observation: convert stored public encounter_id → internal encounter.id ─
    # Existing rows store encounter.encounter_id (public); FK targets encounter.id (internal PK).
    op.execute(
        "UPDATE observation SET encounter_id = e.id "
        "FROM encounter e "
        "WHERE observation.encounter_id = e.encounter_id "
        "AND observation.encounter_id IS NOT NULL"
    )
    op.create_index(op.f('ix_observation_encounter_id'), 'observation', ['encounter_id'], unique=False)
    op.create_foreign_key(None, 'observation', 'encounter', ['encounter_id'], ['id'])

    # ── claim_item_encounter: FK + index on reference_id ─────────────────────
    # Existing rows store encounter.encounter_id (public); convert to internal PK first.
    op.execute(
        "UPDATE claim_item_encounter SET reference_id = e.id "
        "FROM encounter e "
        "WHERE claim_item_encounter.reference_id = e.encounter_id "
        "AND claim_item_encounter.reference_id IS NOT NULL"
    )
    op.create_index(op.f('ix_claim_item_encounter_reference_id'), 'claim_item_encounter', ['reference_id'], unique=False)
    op.create_foreign_key(None, 'claim_item_encounter', 'encounter', ['reference_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint(None, 'claim_item_encounter', type_='foreignkey')
    op.drop_index(op.f('ix_claim_item_encounter_reference_id'), table_name='claim_item_encounter')

    op.drop_constraint(None, 'observation', type_='foreignkey')
    op.drop_index(op.f('ix_observation_encounter_id'), table_name='observation')

    op.drop_column('service_request', 'encounter_display')
    op.drop_column('service_request', 'encounter_type')
    op.drop_column('questionnaire_response', 'encounter_display')
    op.drop_column('questionnaire_response', 'encounter_type')
    op.drop_column('procedure', 'encounter_display')
    op.drop_column('procedure', 'encounter_type')
    op.drop_column('medication_request', 'encounter_display')
    op.drop_column('medication_request', 'encounter_type')
    op.drop_column('diagnostic_report', 'encounter_display')
    op.drop_column('diagnostic_report', 'encounter_type')
    op.drop_column('device_request', 'encounter_display')
    op.drop_column('device_request', 'encounter_type')
    op.drop_column('condition', 'encounter_display')
    op.drop_column('condition', 'encounter_type')
    op.drop_column('appointment', 'encounter_display')
    op.drop_column('appointment', 'encounter_type')

    op.drop_index(op.f('ix_observation_identifier_observation_id'), table_name='observation_identifier')
    op.drop_table('observation_identifier')

    _encounter_ref_type.drop(op.get_bind(), checkfirst=True)
