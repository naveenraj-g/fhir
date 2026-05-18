"""add_specimen_tables

Revision ID: 21ff251274d9
Revises: 2afa0e63f0a3
Create Date: 2026-05-18 18:16:33.653559

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '21ff251274d9'
down_revision: Union[str, None] = '2afa0e63f0a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# New enum types for Specimen
_specimen_status = postgresql.ENUM(
    'available', 'unavailable', 'unsatisfactory', 'entered-in-error',
    name='specimen_status',
)
_specimen_subject_ref = postgresql.ENUM(
    'Patient', 'Group', 'Device', 'Substance', 'Location',
    name='specimen_subject_reference_type',
)
_specimen_collector_ref = postgresql.ENUM(
    'Practitioner', 'PractitionerRole',
    name='specimen_collector_reference_type',
)
_specimen_parent_ref = postgresql.ENUM(
    'Specimen',
    name='specimen_parent_reference_type',
)
_specimen_request_ref = postgresql.ENUM(
    'ServiceRequest',
    name='specimen_request_reference_type',
)
_specimen_processing_additive_ref = postgresql.ENUM(
    'Substance',
    name='specimen_processing_additive_reference_type',
)
_specimen_container_additive_ref = postgresql.ENUM(
    'Substance',
    name='specimen_container_additive_reference_type',
)


def upgrade() -> None:
    bind = op.get_bind()
    _specimen_status.create(bind, checkfirst=True)
    _specimen_subject_ref.create(bind, checkfirst=True)
    _specimen_collector_ref.create(bind, checkfirst=True)
    _specimen_parent_ref.create(bind, checkfirst=True)
    _specimen_request_ref.create(bind, checkfirst=True)
    _specimen_processing_additive_ref.create(bind, checkfirst=True)
    _specimen_container_additive_ref.create(bind, checkfirst=True)

    op.execute("CREATE SEQUENCE IF NOT EXISTS specimen_id_seq START WITH 310000 INCREMENT BY 1")

    op.create_table('specimen',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('specimen_id', sa.Integer(), server_default=sa.text("nextval('specimen_id_seq')"), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('status', postgresql.ENUM('available', 'unavailable', 'unsatisfactory', 'entered-in-error', name='specimen_status', create_type=False), nullable=True),
        sa.Column('type_system', sa.String(), nullable=True),
        sa.Column('type_code', sa.String(), nullable=True),
        sa.Column('type_display', sa.String(), nullable=True),
        sa.Column('type_text', sa.String(), nullable=True),
        sa.Column('subject_type', postgresql.ENUM('Patient', 'Group', 'Device', 'Substance', 'Location', name='specimen_subject_reference_type', create_type=False), nullable=True),
        sa.Column('subject_id', sa.Integer(), nullable=True),
        sa.Column('subject_display', sa.String(), nullable=True),
        sa.Column('received_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('accession_identifier_use', sa.String(), nullable=True),
        sa.Column('accession_identifier_type_system', sa.String(), nullable=True),
        sa.Column('accession_identifier_type_code', sa.String(), nullable=True),
        sa.Column('accession_identifier_type_display', sa.String(), nullable=True),
        sa.Column('accession_identifier_type_text', sa.String(), nullable=True),
        sa.Column('accession_identifier_system', sa.String(), nullable=True),
        sa.Column('accession_identifier_value', sa.String(), nullable=True),
        sa.Column('accession_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('accession_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('accession_identifier_assigner', sa.String(), nullable=True),
        sa.Column('collection_collector_type', postgresql.ENUM('Practitioner', 'PractitionerRole', name='specimen_collector_reference_type', create_type=False), nullable=True),
        sa.Column('collection_collector_id', sa.Integer(), nullable=True),
        sa.Column('collection_collector_display', sa.String(), nullable=True),
        sa.Column('collection_collected_datetime', sa.DateTime(timezone=True), nullable=True),
        sa.Column('collection_collected_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('collection_collected_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('collection_duration_value', sa.Numeric(), nullable=True),
        sa.Column('collection_duration_unit', sa.String(), nullable=True),
        sa.Column('collection_duration_system', sa.String(), nullable=True),
        sa.Column('collection_duration_code', sa.String(), nullable=True),
        sa.Column('collection_quantity_value', sa.Numeric(), nullable=True),
        sa.Column('collection_quantity_unit', sa.String(), nullable=True),
        sa.Column('collection_quantity_system', sa.String(), nullable=True),
        sa.Column('collection_quantity_code', sa.String(), nullable=True),
        sa.Column('collection_method_system', sa.String(), nullable=True),
        sa.Column('collection_method_code', sa.String(), nullable=True),
        sa.Column('collection_method_display', sa.String(), nullable=True),
        sa.Column('collection_method_text', sa.String(), nullable=True),
        sa.Column('collection_body_site_system', sa.String(), nullable=True),
        sa.Column('collection_body_site_code', sa.String(), nullable=True),
        sa.Column('collection_body_site_display', sa.String(), nullable=True),
        sa.Column('collection_body_site_text', sa.String(), nullable=True),
        sa.Column('collection_fasting_status_cc_system', sa.String(), nullable=True),
        sa.Column('collection_fasting_status_cc_code', sa.String(), nullable=True),
        sa.Column('collection_fasting_status_cc_display', sa.String(), nullable=True),
        sa.Column('collection_fasting_status_cc_text', sa.String(), nullable=True),
        sa.Column('collection_fasting_status_duration_value', sa.Numeric(), nullable=True),
        sa.Column('collection_fasting_status_duration_unit', sa.String(), nullable=True),
        sa.Column('collection_fasting_status_duration_system', sa.String(), nullable=True),
        sa.Column('collection_fasting_status_duration_code', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_specimen_id'), 'specimen', ['id'], unique=False)
    op.create_index(op.f('ix_specimen_org_id'), 'specimen', ['org_id'], unique=False)
    op.create_index(op.f('ix_specimen_specimen_id'), 'specimen', ['specimen_id'], unique=True)
    op.create_index(op.f('ix_specimen_user_id'), 'specimen', ['user_id'], unique=False)

    op.create_table('specimen_condition',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('specimen_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['specimen_id'], ['specimen.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_specimen_condition_specimen_id'), 'specimen_condition', ['specimen_id'], unique=False)

    op.create_table('specimen_container',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('specimen_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('type_system', sa.String(), nullable=True),
        sa.Column('type_code', sa.String(), nullable=True),
        sa.Column('type_display', sa.String(), nullable=True),
        sa.Column('type_text', sa.String(), nullable=True),
        sa.Column('capacity_value', sa.Numeric(), nullable=True),
        sa.Column('capacity_unit', sa.String(), nullable=True),
        sa.Column('capacity_system', sa.String(), nullable=True),
        sa.Column('capacity_code', sa.String(), nullable=True),
        sa.Column('specimen_quantity_value', sa.Numeric(), nullable=True),
        sa.Column('specimen_quantity_unit', sa.String(), nullable=True),
        sa.Column('specimen_quantity_system', sa.String(), nullable=True),
        sa.Column('specimen_quantity_code', sa.String(), nullable=True),
        sa.Column('additive_cc_system', sa.String(), nullable=True),
        sa.Column('additive_cc_code', sa.String(), nullable=True),
        sa.Column('additive_cc_display', sa.String(), nullable=True),
        sa.Column('additive_cc_text', sa.String(), nullable=True),
        sa.Column('additive_reference_type', postgresql.ENUM('Substance', name='specimen_container_additive_reference_type', create_type=False), nullable=True),
        sa.Column('additive_reference_id', sa.Integer(), nullable=True),
        sa.Column('additive_reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['specimen_id'], ['specimen.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_specimen_container_specimen_id'), 'specimen_container', ['specimen_id'], unique=False)

    op.create_table('specimen_identifier',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('specimen_id', sa.Integer(), nullable=False),
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
        sa.ForeignKeyConstraint(['specimen_id'], ['specimen.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_specimen_identifier_specimen_id'), 'specimen_identifier', ['specimen_id'], unique=False)

    op.create_table('specimen_note',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('specimen_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('author_string', sa.String(), nullable=True),
        sa.Column('author_reference_type', sa.String(), nullable=True),
        sa.Column('author_reference_id', sa.Integer(), nullable=True),
        sa.Column('author_reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['specimen_id'], ['specimen.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_specimen_note_specimen_id'), 'specimen_note', ['specimen_id'], unique=False)

    op.create_table('specimen_parent',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('specimen_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Specimen', name='specimen_parent_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['specimen_id'], ['specimen.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_specimen_parent_specimen_id'), 'specimen_parent', ['specimen_id'], unique=False)

    op.create_table('specimen_processing',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('specimen_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('procedure_system', sa.String(), nullable=True),
        sa.Column('procedure_code', sa.String(), nullable=True),
        sa.Column('procedure_display', sa.String(), nullable=True),
        sa.Column('procedure_text', sa.String(), nullable=True),
        sa.Column('time_datetime', sa.DateTime(timezone=True), nullable=True),
        sa.Column('time_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('time_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['specimen_id'], ['specimen.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_specimen_processing_specimen_id'), 'specimen_processing', ['specimen_id'], unique=False)

    op.create_table('specimen_request',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('specimen_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('ServiceRequest', name='specimen_request_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['specimen_id'], ['specimen.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_specimen_request_specimen_id'), 'specimen_request', ['specimen_id'], unique=False)

    op.create_table('specimen_container_identifier',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('container_id', sa.Integer(), nullable=False),
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
        sa.ForeignKeyConstraint(['container_id'], ['specimen_container.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_specimen_container_identifier_container_id'), 'specimen_container_identifier', ['container_id'], unique=False)

    op.create_table('specimen_processing_additive',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('processing_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Substance', name='specimen_processing_additive_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['processing_id'], ['specimen_processing.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_specimen_processing_additive_processing_id'), 'specimen_processing_additive', ['processing_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_specimen_processing_additive_processing_id'), table_name='specimen_processing_additive')
    op.drop_table('specimen_processing_additive')
    op.drop_index(op.f('ix_specimen_container_identifier_container_id'), table_name='specimen_container_identifier')
    op.drop_table('specimen_container_identifier')
    op.drop_index(op.f('ix_specimen_request_specimen_id'), table_name='specimen_request')
    op.drop_table('specimen_request')
    op.drop_index(op.f('ix_specimen_processing_specimen_id'), table_name='specimen_processing')
    op.drop_table('specimen_processing')
    op.drop_index(op.f('ix_specimen_parent_specimen_id'), table_name='specimen_parent')
    op.drop_table('specimen_parent')
    op.drop_index(op.f('ix_specimen_note_specimen_id'), table_name='specimen_note')
    op.drop_table('specimen_note')
    op.drop_index(op.f('ix_specimen_identifier_specimen_id'), table_name='specimen_identifier')
    op.drop_table('specimen_identifier')
    op.drop_index(op.f('ix_specimen_container_specimen_id'), table_name='specimen_container')
    op.drop_table('specimen_container')
    op.drop_index(op.f('ix_specimen_condition_specimen_id'), table_name='specimen_condition')
    op.drop_table('specimen_condition')
    op.drop_index(op.f('ix_specimen_user_id'), table_name='specimen')
    op.drop_index(op.f('ix_specimen_specimen_id'), table_name='specimen')
    op.drop_index(op.f('ix_specimen_org_id'), table_name='specimen')
    op.drop_index(op.f('ix_specimen_id'), table_name='specimen')
    op.drop_table('specimen')

    op.execute("DROP SEQUENCE IF EXISTS specimen_id_seq")

    bind = op.get_bind()
    _specimen_container_additive_ref.drop(bind, checkfirst=True)
    _specimen_processing_additive_ref.drop(bind, checkfirst=True)
    _specimen_request_ref.drop(bind, checkfirst=True)
    _specimen_parent_ref.drop(bind, checkfirst=True)
    _specimen_collector_ref.drop(bind, checkfirst=True)
    _specimen_subject_ref.drop(bind, checkfirst=True)
    _specimen_status.drop(bind, checkfirst=True)
