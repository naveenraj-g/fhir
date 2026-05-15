"""add_healthcare_service_tables

Revision ID: 7536981d5a01
Revises: 23878e1e1a4e
Create Date: 2026-05-15 23:12:19.523205

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '7536981d5a01'
down_revision: Union[str, None] = '23878e1e1a4e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# New enum types (not yet in the DB)
_location_ref_type = postgresql.ENUM('Location', name='hs_location_ref_type')
_coverage_area_ref_type = postgresql.ENUM('Location', name='hs_coverage_area_ref_type')
_endpoint_ref_type = postgresql.ENUM('Endpoint', name='hs_endpoint_ref_type')

# Shared enum types that already exist — reference only, never create/drop
_contact_point_system = postgresql.ENUM(
    'phone', 'fax', 'email', 'pager', 'url', 'sms', 'other',
    name='contact_point_system', create_type=False,
)
_contact_point_use = postgresql.ENUM(
    'home', 'work', 'temp', 'old', 'mobile',
    name='contact_point_use', create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()

    # ── 0. Create sequence for public ID ──────────────────────────────────────
    op.execute("CREATE SEQUENCE IF NOT EXISTS healthcare_service_id_seq START WITH 150000 INCREMENT BY 1")

    # ── 1. Create new PostgreSQL enum types ───────────────────────────────────
    _location_ref_type.create(bind, checkfirst=True)
    _coverage_area_ref_type.create(bind, checkfirst=True)
    _endpoint_ref_type.create(bind, checkfirst=True)

    # ── 2. Main table ─────────────────────────────────────────────────────────
    op.create_table('healthcare_service',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('healthcare_service_id', sa.Integer(), server_default=sa.text("nextval('healthcare_service_id_seq')"), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True),
        sa.Column('provided_by_id', sa.String(), nullable=True),
        sa.Column('provided_by_display', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('comment', sa.String(), nullable=True),
        sa.Column('extra_details', sa.Text(), nullable=True),
        sa.Column('photo_content_type', sa.String(), nullable=True),
        sa.Column('photo_language', sa.String(), nullable=True),
        sa.Column('photo_data', sa.Text(), nullable=True),
        sa.Column('photo_url', sa.String(), nullable=True),
        sa.Column('photo_size', sa.Integer(), nullable=True),
        sa.Column('photo_hash', sa.String(), nullable=True),
        sa.Column('photo_title', sa.String(), nullable=True),
        sa.Column('photo_creation', sa.DateTime(timezone=True), nullable=True),
        sa.Column('appointment_required', sa.Boolean(), nullable=True),
        sa.Column('availability_exceptions', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_healthcare_service_id'), 'healthcare_service', ['id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_healthcare_service_id'), 'healthcare_service', ['healthcare_service_id'], unique=True)
    op.create_index(op.f('ix_healthcare_service_user_id'), 'healthcare_service', ['user_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_org_id'), 'healthcare_service', ['org_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_name'), 'healthcare_service', ['name'], unique=False)

    # ── 3. Child tables ───────────────────────────────────────────────────────

    op.create_table('healthcare_service_identifier',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('healthcare_service_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('use', sa.String(), nullable=True),
        sa.Column('type_system', sa.String(), nullable=True),
        sa.Column('type_code', sa.String(), nullable=True),
        sa.Column('type_display', sa.String(), nullable=True),
        sa.Column('type_text', sa.String(), nullable=True),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('value', sa.String(), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('assigner', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['healthcare_service_id'], ['healthcare_service.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_healthcare_service_identifier_healthcare_service_id'), 'healthcare_service_identifier', ['healthcare_service_id'], unique=False)

    op.create_table('healthcare_service_category',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('healthcare_service_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['healthcare_service_id'], ['healthcare_service.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_healthcare_service_category_healthcare_service_id'), 'healthcare_service_category', ['healthcare_service_id'], unique=False)

    op.create_table('healthcare_service_type',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('healthcare_service_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['healthcare_service_id'], ['healthcare_service.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_healthcare_service_type_healthcare_service_id'), 'healthcare_service_type', ['healthcare_service_id'], unique=False)

    op.create_table('healthcare_service_specialty',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('healthcare_service_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['healthcare_service_id'], ['healthcare_service.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_healthcare_service_specialty_healthcare_service_id'), 'healthcare_service_specialty', ['healthcare_service_id'], unique=False)

    op.create_table('healthcare_service_location',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('healthcare_service_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Location', name='hs_location_ref_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['healthcare_service_id'], ['healthcare_service.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_healthcare_service_location_healthcare_service_id'), 'healthcare_service_location', ['healthcare_service_id'], unique=False)

    op.create_table('healthcare_service_telecom',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('healthcare_service_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('system', postgresql.ENUM('phone', 'fax', 'email', 'pager', 'url', 'sms', 'other', name='contact_point_system', create_type=False), nullable=True),
        sa.Column('value', sa.String(), nullable=True),
        sa.Column('use', postgresql.ENUM('home', 'work', 'temp', 'old', 'mobile', name='contact_point_use', create_type=False), nullable=True),
        sa.Column('rank', sa.Integer(), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['healthcare_service_id'], ['healthcare_service.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_healthcare_service_telecom_healthcare_service_id'), 'healthcare_service_telecom', ['healthcare_service_id'], unique=False)

    op.create_table('healthcare_service_coverage_area',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('healthcare_service_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Location', name='hs_coverage_area_ref_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['healthcare_service_id'], ['healthcare_service.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_healthcare_service_coverage_area_healthcare_service_id'), 'healthcare_service_coverage_area', ['healthcare_service_id'], unique=False)

    op.create_table('healthcare_service_service_provision_code',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('healthcare_service_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['healthcare_service_id'], ['healthcare_service.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_healthcare_service_service_provision_code_healthcare_service_id'), 'healthcare_service_service_provision_code', ['healthcare_service_id'], unique=False)

    op.create_table('healthcare_service_eligibility',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('healthcare_service_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('code_system', sa.String(), nullable=True),
        sa.Column('code_code', sa.String(), nullable=True),
        sa.Column('code_display', sa.String(), nullable=True),
        sa.Column('code_text', sa.String(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['healthcare_service_id'], ['healthcare_service.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_healthcare_service_eligibility_healthcare_service_id'), 'healthcare_service_eligibility', ['healthcare_service_id'], unique=False)

    op.create_table('healthcare_service_program',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('healthcare_service_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['healthcare_service_id'], ['healthcare_service.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_healthcare_service_program_healthcare_service_id'), 'healthcare_service_program', ['healthcare_service_id'], unique=False)

    op.create_table('healthcare_service_characteristic',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('healthcare_service_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['healthcare_service_id'], ['healthcare_service.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_healthcare_service_characteristic_healthcare_service_id'), 'healthcare_service_characteristic', ['healthcare_service_id'], unique=False)

    op.create_table('healthcare_service_communication',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('healthcare_service_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['healthcare_service_id'], ['healthcare_service.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_healthcare_service_communication_healthcare_service_id'), 'healthcare_service_communication', ['healthcare_service_id'], unique=False)

    op.create_table('healthcare_service_referral_method',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('healthcare_service_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['healthcare_service_id'], ['healthcare_service.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_healthcare_service_referral_method_healthcare_service_id'), 'healthcare_service_referral_method', ['healthcare_service_id'], unique=False)

    op.create_table('healthcare_service_available_time',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('healthcare_service_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('days_of_week', sa.Text(), nullable=True),
        sa.Column('all_day', sa.Boolean(), nullable=True),
        sa.Column('available_start_time', sa.String(), nullable=True),
        sa.Column('available_end_time', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['healthcare_service_id'], ['healthcare_service.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_healthcare_service_available_time_healthcare_service_id'), 'healthcare_service_available_time', ['healthcare_service_id'], unique=False)

    op.create_table('healthcare_service_not_available',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('healthcare_service_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('during_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('during_end', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['healthcare_service_id'], ['healthcare_service.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_healthcare_service_not_available_healthcare_service_id'), 'healthcare_service_not_available', ['healthcare_service_id'], unique=False)

    op.create_table('healthcare_service_endpoint',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('healthcare_service_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Endpoint', name='hs_endpoint_ref_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['healthcare_service_id'], ['healthcare_service.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_healthcare_service_endpoint_healthcare_service_id'), 'healthcare_service_endpoint', ['healthcare_service_id'], unique=False)


def downgrade() -> None:
    bind = op.get_bind()

    # Drop child tables first (FK order)
    op.drop_index(op.f('ix_healthcare_service_endpoint_healthcare_service_id'), table_name='healthcare_service_endpoint')
    op.drop_table('healthcare_service_endpoint')
    op.drop_index(op.f('ix_healthcare_service_not_available_healthcare_service_id'), table_name='healthcare_service_not_available')
    op.drop_table('healthcare_service_not_available')
    op.drop_index(op.f('ix_healthcare_service_available_time_healthcare_service_id'), table_name='healthcare_service_available_time')
    op.drop_table('healthcare_service_available_time')
    op.drop_index(op.f('ix_healthcare_service_referral_method_healthcare_service_id'), table_name='healthcare_service_referral_method')
    op.drop_table('healthcare_service_referral_method')
    op.drop_index(op.f('ix_healthcare_service_communication_healthcare_service_id'), table_name='healthcare_service_communication')
    op.drop_table('healthcare_service_communication')
    op.drop_index(op.f('ix_healthcare_service_characteristic_healthcare_service_id'), table_name='healthcare_service_characteristic')
    op.drop_table('healthcare_service_characteristic')
    op.drop_index(op.f('ix_healthcare_service_program_healthcare_service_id'), table_name='healthcare_service_program')
    op.drop_table('healthcare_service_program')
    op.drop_index(op.f('ix_healthcare_service_eligibility_healthcare_service_id'), table_name='healthcare_service_eligibility')
    op.drop_table('healthcare_service_eligibility')
    op.drop_index(op.f('ix_healthcare_service_service_provision_code_healthcare_service_id'), table_name='healthcare_service_service_provision_code')
    op.drop_table('healthcare_service_service_provision_code')
    op.drop_index(op.f('ix_healthcare_service_coverage_area_healthcare_service_id'), table_name='healthcare_service_coverage_area')
    op.drop_table('healthcare_service_coverage_area')
    op.drop_index(op.f('ix_healthcare_service_telecom_healthcare_service_id'), table_name='healthcare_service_telecom')
    op.drop_table('healthcare_service_telecom')
    op.drop_index(op.f('ix_healthcare_service_location_healthcare_service_id'), table_name='healthcare_service_location')
    op.drop_table('healthcare_service_location')
    op.drop_index(op.f('ix_healthcare_service_specialty_healthcare_service_id'), table_name='healthcare_service_specialty')
    op.drop_table('healthcare_service_specialty')
    op.drop_index(op.f('ix_healthcare_service_type_healthcare_service_id'), table_name='healthcare_service_type')
    op.drop_table('healthcare_service_type')
    op.drop_index(op.f('ix_healthcare_service_category_healthcare_service_id'), table_name='healthcare_service_category')
    op.drop_table('healthcare_service_category')
    op.drop_index(op.f('ix_healthcare_service_identifier_healthcare_service_id'), table_name='healthcare_service_identifier')
    op.drop_table('healthcare_service_identifier')

    # Drop main table and sequence
    op.drop_index(op.f('ix_healthcare_service_name'), table_name='healthcare_service')
    op.drop_index(op.f('ix_healthcare_service_org_id'), table_name='healthcare_service')
    op.drop_index(op.f('ix_healthcare_service_user_id'), table_name='healthcare_service')
    op.drop_index(op.f('ix_healthcare_service_healthcare_service_id'), table_name='healthcare_service')
    op.drop_index(op.f('ix_healthcare_service_id'), table_name='healthcare_service')
    op.drop_table('healthcare_service')
    op.execute("DROP SEQUENCE IF EXISTS healthcare_service_id_seq")

    # Drop new enum types (do NOT drop shared contact_point_* types)
    _endpoint_ref_type.drop(bind, checkfirst=True)
    _coverage_area_ref_type.drop(bind, checkfirst=True)
    _location_ref_type.drop(bind, checkfirst=True)
