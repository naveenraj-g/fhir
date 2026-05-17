"""add_allergy_intolerance_tables

Revision ID: a5c4e11ebbb3
Revises: 1f89d47009a2
Create Date: 2026-05-17 20:16:18.297196

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a5c4e11ebbb3'
down_revision: Union[str, None] = '1f89d47009a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ai_type = postgresql.ENUM('allergy', 'intolerance', name='allergy_intolerance_type')
_ai_criticality = postgresql.ENUM('low', 'high', 'unable-to-assess', name='allergy_intolerance_criticality')
_ai_patient_ref = postgresql.ENUM('Patient', name='allergy_intolerance_patient_reference_type')
_ai_participant_ref = postgresql.ENUM(
    'Practitioner', 'PractitionerRole', 'Patient', 'RelatedPerson',
    name='allergy_intolerance_participant_reference_type',
)
_ai_category_code = postgresql.ENUM(
    'food', 'medication', 'environment', 'biologic',
    name='allergy_intolerance_category_code',
)
_ai_reaction_severity = postgresql.ENUM('mild', 'moderate', 'severe', name='allergy_intolerance_reaction_severity')

# Shared type — already exists, never create/drop
_encounter_ref = postgresql.ENUM(name='encounter_reference_type', create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    _ai_type.create(bind, checkfirst=True)
    _ai_criticality.create(bind, checkfirst=True)
    _ai_patient_ref.create(bind, checkfirst=True)
    _ai_participant_ref.create(bind, checkfirst=True)
    _ai_category_code.create(bind, checkfirst=True)
    _ai_reaction_severity.create(bind, checkfirst=True)

    op.execute(
        "CREATE SEQUENCE IF NOT EXISTS allergy_intolerance_id_seq START WITH 260000 INCREMENT BY 1"
    )

    op.create_table(
        'allergy_intolerance',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('allergy_intolerance_id', sa.Integer(), server_default=sa.text("nextval('allergy_intolerance_id_seq')"), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('clinical_status_system', sa.String(), nullable=True),
        sa.Column('clinical_status_code', sa.String(), nullable=True),
        sa.Column('clinical_status_display', sa.String(), nullable=True),
        sa.Column('clinical_status_text', sa.String(), nullable=True),
        sa.Column('verification_status_system', sa.String(), nullable=True),
        sa.Column('verification_status_code', sa.String(), nullable=True),
        sa.Column('verification_status_display', sa.String(), nullable=True),
        sa.Column('verification_status_text', sa.String(), nullable=True),
        sa.Column('type', postgresql.ENUM('allergy', 'intolerance', name='allergy_intolerance_type', create_type=False), nullable=True),
        sa.Column('criticality', postgresql.ENUM('low', 'high', 'unable-to-assess', name='allergy_intolerance_criticality', create_type=False), nullable=True),
        sa.Column('code_system', sa.String(), nullable=True),
        sa.Column('code_code', sa.String(), nullable=True),
        sa.Column('code_display', sa.String(), nullable=True),
        sa.Column('code_text', sa.String(), nullable=True),
        sa.Column('patient_type', postgresql.ENUM('Patient', name='allergy_intolerance_patient_reference_type', create_type=False), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('patient_display', sa.String(), nullable=True),
        sa.Column('encounter_type', postgresql.ENUM(name='encounter_reference_type', create_type=False), nullable=True),
        sa.Column('encounter_id', sa.Integer(), nullable=True),
        sa.Column('encounter_display', sa.String(), nullable=True),
        sa.Column('onset_date_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('onset_age_value', sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column('onset_age_comparator', sa.String(), nullable=True),
        sa.Column('onset_age_unit', sa.String(), nullable=True),
        sa.Column('onset_age_system', sa.String(), nullable=True),
        sa.Column('onset_age_code', sa.String(), nullable=True),
        sa.Column('onset_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('onset_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('onset_range_low_value', sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column('onset_range_low_unit', sa.String(), nullable=True),
        sa.Column('onset_range_low_system', sa.String(), nullable=True),
        sa.Column('onset_range_low_code', sa.String(), nullable=True),
        sa.Column('onset_range_high_value', sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column('onset_range_high_unit', sa.String(), nullable=True),
        sa.Column('onset_range_high_system', sa.String(), nullable=True),
        sa.Column('onset_range_high_code', sa.String(), nullable=True),
        sa.Column('onset_string', sa.String(), nullable=True),
        sa.Column('recorded_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('recorder_type', postgresql.ENUM('Practitioner', 'PractitionerRole', 'Patient', 'RelatedPerson', name='allergy_intolerance_participant_reference_type', create_type=False), nullable=True),
        sa.Column('recorder_id', sa.Integer(), nullable=True),
        sa.Column('recorder_display', sa.String(), nullable=True),
        sa.Column('asserter_type', postgresql.ENUM('Practitioner', 'PractitionerRole', 'Patient', 'RelatedPerson', name='allergy_intolerance_participant_reference_type', create_type=False), nullable=True),
        sa.Column('asserter_id', sa.Integer(), nullable=True),
        sa.Column('asserter_display', sa.String(), nullable=True),
        sa.Column('last_occurrence', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_allergy_intolerance_allergy_intolerance_id'), 'allergy_intolerance', ['allergy_intolerance_id'], unique=True)
    op.create_index(op.f('ix_allergy_intolerance_id'), 'allergy_intolerance', ['id'], unique=False)
    op.create_index(op.f('ix_allergy_intolerance_org_id'), 'allergy_intolerance', ['org_id'], unique=False)
    op.create_index(op.f('ix_allergy_intolerance_user_id'), 'allergy_intolerance', ['user_id'], unique=False)

    op.create_table(
        'allergy_intolerance_category',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('allergy_intolerance_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('category', postgresql.ENUM('food', 'medication', 'environment', 'biologic', name='allergy_intolerance_category_code', create_type=False), nullable=False),
        sa.ForeignKeyConstraint(['allergy_intolerance_id'], ['allergy_intolerance.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_allergy_intolerance_category_allergy_intolerance_id'), 'allergy_intolerance_category', ['allergy_intolerance_id'], unique=False)

    op.create_table(
        'allergy_intolerance_identifier',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('allergy_intolerance_id', sa.Integer(), nullable=False),
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
        sa.ForeignKeyConstraint(['allergy_intolerance_id'], ['allergy_intolerance.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_allergy_intolerance_identifier_allergy_intolerance_id'), 'allergy_intolerance_identifier', ['allergy_intolerance_id'], unique=False)

    op.create_table(
        'allergy_intolerance_note',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('allergy_intolerance_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('author_string', sa.String(), nullable=True),
        sa.Column('author_reference_type', sa.String(), nullable=True),
        sa.Column('author_reference_id', sa.Integer(), nullable=True),
        sa.Column('author_reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['allergy_intolerance_id'], ['allergy_intolerance.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_allergy_intolerance_note_allergy_intolerance_id'), 'allergy_intolerance_note', ['allergy_intolerance_id'], unique=False)

    op.create_table(
        'allergy_intolerance_reaction',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('allergy_intolerance_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('substance_system', sa.String(), nullable=True),
        sa.Column('substance_code', sa.String(), nullable=True),
        sa.Column('substance_display', sa.String(), nullable=True),
        sa.Column('substance_text', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('onset', sa.DateTime(timezone=True), nullable=True),
        sa.Column('severity', postgresql.ENUM('mild', 'moderate', 'severe', name='allergy_intolerance_reaction_severity', create_type=False), nullable=True),
        sa.Column('exposure_route_system', sa.String(), nullable=True),
        sa.Column('exposure_route_code', sa.String(), nullable=True),
        sa.Column('exposure_route_display', sa.String(), nullable=True),
        sa.Column('exposure_route_text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['allergy_intolerance_id'], ['allergy_intolerance.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_allergy_intolerance_reaction_allergy_intolerance_id'), 'allergy_intolerance_reaction', ['allergy_intolerance_id'], unique=False)

    op.create_table(
        'allergy_intolerance_reaction_manifestation',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('reaction_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['reaction_id'], ['allergy_intolerance_reaction.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_allergy_intolerance_reaction_manifestation_reaction_id'), 'allergy_intolerance_reaction_manifestation', ['reaction_id'], unique=False)

    op.create_table(
        'allergy_intolerance_reaction_note',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('reaction_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('author_string', sa.String(), nullable=True),
        sa.Column('author_reference_type', sa.String(), nullable=True),
        sa.Column('author_reference_id', sa.Integer(), nullable=True),
        sa.Column('author_reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['reaction_id'], ['allergy_intolerance_reaction.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_allergy_intolerance_reaction_note_reaction_id'), 'allergy_intolerance_reaction_note', ['reaction_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_allergy_intolerance_reaction_note_reaction_id'), table_name='allergy_intolerance_reaction_note')
    op.drop_table('allergy_intolerance_reaction_note')
    op.drop_index(op.f('ix_allergy_intolerance_reaction_manifestation_reaction_id'), table_name='allergy_intolerance_reaction_manifestation')
    op.drop_table('allergy_intolerance_reaction_manifestation')
    op.drop_index(op.f('ix_allergy_intolerance_reaction_allergy_intolerance_id'), table_name='allergy_intolerance_reaction')
    op.drop_table('allergy_intolerance_reaction')
    op.drop_index(op.f('ix_allergy_intolerance_note_allergy_intolerance_id'), table_name='allergy_intolerance_note')
    op.drop_table('allergy_intolerance_note')
    op.drop_index(op.f('ix_allergy_intolerance_identifier_allergy_intolerance_id'), table_name='allergy_intolerance_identifier')
    op.drop_table('allergy_intolerance_identifier')
    op.drop_index(op.f('ix_allergy_intolerance_category_allergy_intolerance_id'), table_name='allergy_intolerance_category')
    op.drop_table('allergy_intolerance_category')
    op.drop_index(op.f('ix_allergy_intolerance_user_id'), table_name='allergy_intolerance')
    op.drop_index(op.f('ix_allergy_intolerance_org_id'), table_name='allergy_intolerance')
    op.drop_index(op.f('ix_allergy_intolerance_id'), table_name='allergy_intolerance')
    op.drop_index(op.f('ix_allergy_intolerance_allergy_intolerance_id'), table_name='allergy_intolerance')
    op.drop_table('allergy_intolerance')

    op.execute("DROP SEQUENCE IF EXISTS allergy_intolerance_id_seq")

    bind = op.get_bind()
    _ai_reaction_severity.drop(bind, checkfirst=True)
    _ai_category_code.drop(bind, checkfirst=True)
    _ai_participant_ref.drop(bind, checkfirst=True)
    _ai_patient_ref.drop(bind, checkfirst=True)
    _ai_criticality.drop(bind, checkfirst=True)
    _ai_type.drop(bind, checkfirst=True)
