"""add immunization tables

Revision ID: a03e90d011a7
Revises: b76fa05a80cc
Create Date: 2026-05-18 19:11:14.268904

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a03e90d011a7'
down_revision: Union[str, None] = 'b76fa05a80cc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_immunization_status = postgresql.ENUM(
    'completed', 'entered-in-error', 'not-done',
    name='immunization_status',
)
_immunization_patient_reference_type = postgresql.ENUM(
    'Patient',
    name='immunization_patient_reference_type',
)
_immunization_location_reference_type = postgresql.ENUM(
    'Location',
    name='immunization_location_reference_type',
)
_immunization_performer_actor_reference_type = postgresql.ENUM(
    'Practitioner', 'PractitionerRole', 'Organization',
    name='immunization_performer_actor_reference_type',
)
_immunization_reason_reference_type = postgresql.ENUM(
    'Condition', 'Observation', 'DiagnosticReport',
    name='immunization_reason_reference_type',
)
_immunization_reaction_detail_reference_type = postgresql.ENUM(
    'Observation',
    name='immunization_reaction_detail_reference_type',
)


def upgrade() -> None:
    _immunization_status.create(op.get_bind(), checkfirst=True)
    _immunization_patient_reference_type.create(op.get_bind(), checkfirst=True)
    _immunization_location_reference_type.create(op.get_bind(), checkfirst=True)
    _immunization_performer_actor_reference_type.create(op.get_bind(), checkfirst=True)
    _immunization_reason_reference_type.create(op.get_bind(), checkfirst=True)
    _immunization_reaction_detail_reference_type.create(op.get_bind(), checkfirst=True)

    op.execute("CREATE SEQUENCE IF NOT EXISTS immunization_id_seq START 330000 INCREMENT 1")

    op.create_table('immunization',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('immunization_id', sa.Integer(), server_default=sa.text("nextval('immunization_id_seq')"), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('status', postgresql.ENUM('completed', 'entered-in-error', 'not-done', name='immunization_status', create_type=False), nullable=False),
    sa.Column('status_reason_system', sa.String(), nullable=True),
    sa.Column('status_reason_code', sa.String(), nullable=True),
    sa.Column('status_reason_display', sa.String(), nullable=True),
    sa.Column('status_reason_text', sa.String(), nullable=True),
    sa.Column('vaccine_code_system', sa.String(), nullable=True),
    sa.Column('vaccine_code_code', sa.String(), nullable=True),
    sa.Column('vaccine_code_display', sa.String(), nullable=True),
    sa.Column('vaccine_code_text', sa.String(), nullable=True),
    sa.Column('patient_type', postgresql.ENUM('Patient', name='immunization_patient_reference_type', create_type=False), nullable=True),
    sa.Column('patient_id', sa.Integer(), nullable=True),
    sa.Column('patient_display', sa.String(), nullable=True),
    sa.Column('encounter_type', postgresql.ENUM('Encounter', name='encounter_reference_type', create_type=False), nullable=True),
    sa.Column('encounter_id', sa.Integer(), nullable=True),
    sa.Column('encounter_display', sa.String(), nullable=True),
    sa.Column('occurrence_datetime', sa.DateTime(timezone=True), nullable=True),
    sa.Column('occurrence_string', sa.String(), nullable=True),
    sa.Column('recorded', sa.DateTime(timezone=True), nullable=True),
    sa.Column('primary_source', sa.Boolean(), nullable=True),
    sa.Column('report_origin_system', sa.String(), nullable=True),
    sa.Column('report_origin_code', sa.String(), nullable=True),
    sa.Column('report_origin_display', sa.String(), nullable=True),
    sa.Column('report_origin_text', sa.String(), nullable=True),
    sa.Column('location_type', postgresql.ENUM('Location', name='immunization_location_reference_type', create_type=False), nullable=True),
    sa.Column('location_id', sa.Integer(), nullable=True),
    sa.Column('location_display', sa.String(), nullable=True),
    sa.Column('manufacturer_type', postgresql.ENUM('Organization', name='organization_reference_type', create_type=False), nullable=True),
    sa.Column('manufacturer_id', sa.Integer(), nullable=True),
    sa.Column('manufacturer_display', sa.String(), nullable=True),
    sa.Column('lot_number', sa.String(), nullable=True),
    sa.Column('expiration_date', sa.Date(), nullable=True),
    sa.Column('site_system', sa.String(), nullable=True),
    sa.Column('site_code', sa.String(), nullable=True),
    sa.Column('site_display', sa.String(), nullable=True),
    sa.Column('site_text', sa.String(), nullable=True),
    sa.Column('route_system', sa.String(), nullable=True),
    sa.Column('route_code', sa.String(), nullable=True),
    sa.Column('route_display', sa.String(), nullable=True),
    sa.Column('route_text', sa.String(), nullable=True),
    sa.Column('dose_quantity_value', sa.Numeric(), nullable=True),
    sa.Column('dose_quantity_unit', sa.String(), nullable=True),
    sa.Column('dose_quantity_system', sa.String(), nullable=True),
    sa.Column('dose_quantity_code', sa.String(), nullable=True),
    sa.Column('is_subpotent', sa.Boolean(), nullable=True),
    sa.Column('funding_source_system', sa.String(), nullable=True),
    sa.Column('funding_source_code', sa.String(), nullable=True),
    sa.Column('funding_source_display', sa.String(), nullable=True),
    sa.Column('funding_source_text', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_by', sa.String(), nullable=True),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['manufacturer_id'], ['organization.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_id'), 'immunization', ['id'], unique=False)
    op.create_index(op.f('ix_immunization_immunization_id'), 'immunization', ['immunization_id'], unique=True)
    op.create_index(op.f('ix_immunization_manufacturer_id'), 'immunization', ['manufacturer_id'], unique=False)
    op.create_index(op.f('ix_immunization_org_id'), 'immunization', ['org_id'], unique=False)
    op.create_index(op.f('ix_immunization_user_id'), 'immunization', ['user_id'], unique=False)

    op.create_table('immunization_education',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('immunization_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('document_type', sa.String(), nullable=True),
    sa.Column('reference', sa.String(), nullable=True),
    sa.Column('publication_date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('presentation_date', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['immunization_id'], ['immunization.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_education_immunization_id'), 'immunization_education', ['immunization_id'], unique=False)

    op.create_table('immunization_identifier',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('immunization_id', sa.Integer(), nullable=False),
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
    sa.ForeignKeyConstraint(['immunization_id'], ['immunization.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_identifier_immunization_id'), 'immunization_identifier', ['immunization_id'], unique=False)

    op.create_table('immunization_note',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('immunization_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('time', sa.DateTime(timezone=True), nullable=True),
    sa.Column('author_string', sa.String(), nullable=True),
    sa.Column('author_reference_type', sa.String(), nullable=True),
    sa.Column('author_reference_id', sa.Integer(), nullable=True),
    sa.Column('author_reference_display', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['immunization_id'], ['immunization.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_note_immunization_id'), 'immunization_note', ['immunization_id'], unique=False)

    op.create_table('immunization_performer',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('immunization_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('function_system', sa.String(), nullable=True),
    sa.Column('function_code', sa.String(), nullable=True),
    sa.Column('function_display', sa.String(), nullable=True),
    sa.Column('function_text', sa.String(), nullable=True),
    sa.Column('reference_type', postgresql.ENUM('Practitioner', 'PractitionerRole', 'Organization', name='immunization_performer_actor_reference_type', create_type=False), nullable=True),
    sa.Column('reference_id', sa.Integer(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['immunization_id'], ['immunization.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_performer_immunization_id'), 'immunization_performer', ['immunization_id'], unique=False)

    op.create_table('immunization_program_eligibility',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('immunization_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('coding_system', sa.String(), nullable=True),
    sa.Column('coding_code', sa.String(), nullable=True),
    sa.Column('coding_display', sa.String(), nullable=True),
    sa.Column('text', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['immunization_id'], ['immunization.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_program_eligibility_immunization_id'), 'immunization_program_eligibility', ['immunization_id'], unique=False)

    op.create_table('immunization_protocol_applied',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('immunization_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('series', sa.String(), nullable=True),
    sa.Column('authority_type', postgresql.ENUM('Organization', name='organization_reference_type', create_type=False), nullable=True),
    sa.Column('authority_id', sa.Integer(), nullable=True),
    sa.Column('authority_display', sa.String(), nullable=True),
    sa.Column('dose_number_positive_int', sa.Integer(), nullable=True),
    sa.Column('dose_number_string', sa.String(), nullable=True),
    sa.Column('series_doses_positive_int', sa.Integer(), nullable=True),
    sa.Column('series_doses_string', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['immunization_id'], ['immunization.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_protocol_applied_immunization_id'), 'immunization_protocol_applied', ['immunization_id'], unique=False)

    op.create_table('immunization_reaction',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('immunization_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('detail_type', postgresql.ENUM('Observation', name='immunization_reaction_detail_reference_type', create_type=False), nullable=True),
    sa.Column('detail_id', sa.Integer(), nullable=True),
    sa.Column('detail_display', sa.String(), nullable=True),
    sa.Column('reported', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['immunization_id'], ['immunization.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_reaction_immunization_id'), 'immunization_reaction', ['immunization_id'], unique=False)

    op.create_table('immunization_reason_code',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('immunization_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('coding_system', sa.String(), nullable=True),
    sa.Column('coding_code', sa.String(), nullable=True),
    sa.Column('coding_display', sa.String(), nullable=True),
    sa.Column('text', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['immunization_id'], ['immunization.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_reason_code_immunization_id'), 'immunization_reason_code', ['immunization_id'], unique=False)

    op.create_table('immunization_reason_reference',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('immunization_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('reference_type', postgresql.ENUM('Condition', 'Observation', 'DiagnosticReport', name='immunization_reason_reference_type', create_type=False), nullable=True),
    sa.Column('reference_id', sa.Integer(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['immunization_id'], ['immunization.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_reason_reference_immunization_id'), 'immunization_reason_reference', ['immunization_id'], unique=False)

    op.create_table('immunization_subpotent_reason',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('immunization_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('coding_system', sa.String(), nullable=True),
    sa.Column('coding_code', sa.String(), nullable=True),
    sa.Column('coding_display', sa.String(), nullable=True),
    sa.Column('text', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['immunization_id'], ['immunization.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_subpotent_reason_immunization_id'), 'immunization_subpotent_reason', ['immunization_id'], unique=False)

    op.create_table('immunization_protocol_applied_target_disease',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('protocol_applied_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('coding_system', sa.String(), nullable=True),
    sa.Column('coding_code', sa.String(), nullable=True),
    sa.Column('coding_display', sa.String(), nullable=True),
    sa.Column('text', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['protocol_applied_id'], ['immunization_protocol_applied.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_protocol_applied_target_disease_protocol_applied_id'), 'immunization_protocol_applied_target_disease', ['protocol_applied_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_immunization_protocol_applied_target_disease_protocol_applied_id'), table_name='immunization_protocol_applied_target_disease')
    op.drop_table('immunization_protocol_applied_target_disease')
    op.drop_index(op.f('ix_immunization_subpotent_reason_immunization_id'), table_name='immunization_subpotent_reason')
    op.drop_table('immunization_subpotent_reason')
    op.drop_index(op.f('ix_immunization_reason_reference_immunization_id'), table_name='immunization_reason_reference')
    op.drop_table('immunization_reason_reference')
    op.drop_index(op.f('ix_immunization_reason_code_immunization_id'), table_name='immunization_reason_code')
    op.drop_table('immunization_reason_code')
    op.drop_index(op.f('ix_immunization_reaction_immunization_id'), table_name='immunization_reaction')
    op.drop_table('immunization_reaction')
    op.drop_index(op.f('ix_immunization_protocol_applied_immunization_id'), table_name='immunization_protocol_applied')
    op.drop_table('immunization_protocol_applied')
    op.drop_index(op.f('ix_immunization_program_eligibility_immunization_id'), table_name='immunization_program_eligibility')
    op.drop_table('immunization_program_eligibility')
    op.drop_index(op.f('ix_immunization_performer_immunization_id'), table_name='immunization_performer')
    op.drop_table('immunization_performer')
    op.drop_index(op.f('ix_immunization_note_immunization_id'), table_name='immunization_note')
    op.drop_table('immunization_note')
    op.drop_index(op.f('ix_immunization_identifier_immunization_id'), table_name='immunization_identifier')
    op.drop_table('immunization_identifier')
    op.drop_index(op.f('ix_immunization_education_immunization_id'), table_name='immunization_education')
    op.drop_table('immunization_education')
    op.drop_index(op.f('ix_immunization_user_id'), table_name='immunization')
    op.drop_index(op.f('ix_immunization_org_id'), table_name='immunization')
    op.drop_index(op.f('ix_immunization_manufacturer_id'), table_name='immunization')
    op.drop_index(op.f('ix_immunization_immunization_id'), table_name='immunization')
    op.drop_index(op.f('ix_immunization_id'), table_name='immunization')
    op.drop_table('immunization')
    op.execute("DROP SEQUENCE IF EXISTS immunization_id_seq")

    _immunization_reaction_detail_reference_type.drop(op.get_bind(), checkfirst=True)
    _immunization_reason_reference_type.drop(op.get_bind(), checkfirst=True)
    _immunization_performer_actor_reference_type.drop(op.get_bind(), checkfirst=True)
    _immunization_location_reference_type.drop(op.get_bind(), checkfirst=True)
    _immunization_patient_reference_type.drop(op.get_bind(), checkfirst=True)
    _immunization_status.drop(op.get_bind(), checkfirst=True)
