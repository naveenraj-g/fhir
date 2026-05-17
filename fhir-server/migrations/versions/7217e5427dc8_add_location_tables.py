"""add_location_tables

Revision ID: 7217e5427dc8
Revises: eccaa97a802e
Create Date: 2026-05-17 18:54:38.075797

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '7217e5427dc8'
down_revision: Union[str, None] = 'eccaa97a802e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# New enum types owned by this migration
_location_status = postgresql.ENUM('active', 'suspended', 'inactive', name='location_status')
_location_mode = postgresql.ENUM('instance', 'kind', name='location_mode')
_location_part_of_ref_type = postgresql.ENUM('Location', name='location_part_of_reference_type')
_location_endpoint_ref_type = postgresql.ENUM('Endpoint', name='location_endpoint_reference_type')

# Shared enum types — already exist, never re-create or drop
_org_ref_type = postgresql.ENUM('Organization', name='organization_reference_type', create_type=False)
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

    # Create sequence
    op.execute("CREATE SEQUENCE IF NOT EXISTS location_id_seq START WITH 230000 INCREMENT BY 1")

    # Create new enum types
    _location_status.create(bind, checkfirst=True)
    _location_mode.create(bind, checkfirst=True)
    _location_part_of_ref_type.create(bind, checkfirst=True)
    _location_endpoint_ref_type.create(bind, checkfirst=True)

    op.create_table('location',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('location_id', sa.Integer(), server_default=sa.text("nextval('location_id_seq')"), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('status', postgresql.ENUM('active', 'suspended', 'inactive', name='location_status', create_type=False), nullable=True),
        sa.Column('operational_status_system', sa.String(), nullable=True),
        sa.Column('operational_status_code', sa.String(), nullable=True),
        sa.Column('operational_status_display', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('mode', postgresql.ENUM('instance', 'kind', name='location_mode', create_type=False), nullable=True),
        sa.Column('address_use', sa.String(), nullable=True),
        sa.Column('address_type', sa.String(), nullable=True),
        sa.Column('address_text', sa.Text(), nullable=True),
        sa.Column('address_line', sa.Text(), nullable=True),
        sa.Column('address_city', sa.String(), nullable=True),
        sa.Column('address_district', sa.String(), nullable=True),
        sa.Column('address_state', sa.String(), nullable=True),
        sa.Column('address_postal_code', sa.String(), nullable=True),
        sa.Column('address_country', sa.String(), nullable=True),
        sa.Column('address_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('address_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('physical_type_system', sa.String(), nullable=True),
        sa.Column('physical_type_code', sa.String(), nullable=True),
        sa.Column('physical_type_display', sa.String(), nullable=True),
        sa.Column('physical_type_text', sa.String(), nullable=True),
        sa.Column('managing_organization_type', postgresql.ENUM('Organization', name='organization_reference_type', create_type=False), nullable=True),
        sa.Column('managing_organization_id', sa.Integer(), nullable=True),
        sa.Column('managing_organization_display', sa.String(), nullable=True),
        sa.Column('part_of_type', postgresql.ENUM('Location', name='location_part_of_reference_type', create_type=False), nullable=True),
        sa.Column('part_of_id', sa.Integer(), nullable=True),
        sa.Column('part_of_display', sa.String(), nullable=True),
        sa.Column('availability_exceptions', sa.Text(), nullable=True),
        sa.Column('position_longitude', sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column('position_latitude', sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column('position_altitude', sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_location_id'), 'location', ['id'], unique=False)
    op.create_index(op.f('ix_location_location_id'), 'location', ['location_id'], unique=True)
    op.create_index(op.f('ix_location_name'), 'location', ['name'], unique=False)
    op.create_index(op.f('ix_location_org_id'), 'location', ['org_id'], unique=False)
    op.create_index(op.f('ix_location_user_id'), 'location', ['user_id'], unique=False)

    op.create_table('location_alias',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('alias', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['location_id'], ['location.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_location_alias_location_id'), 'location_alias', ['location_id'], unique=False)

    op.create_table('location_endpoint',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Endpoint', name='location_endpoint_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['location_id'], ['location.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_location_endpoint_location_id'), 'location_endpoint', ['location_id'], unique=False)

    op.create_table('location_hours_of_operation',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('days_of_week', sa.Text(), nullable=True),
        sa.Column('all_day', sa.Boolean(), nullable=True),
        sa.Column('opening_time', sa.String(), nullable=True),
        sa.Column('closing_time', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['location_id'], ['location.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_location_hours_of_operation_location_id'), 'location_hours_of_operation', ['location_id'], unique=False)

    op.create_table('location_identifier',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=False),
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
        sa.ForeignKeyConstraint(['location_id'], ['location.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_location_identifier_location_id'), 'location_identifier', ['location_id'], unique=False)

    op.create_table('location_telecom',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('system', postgresql.ENUM('phone', 'fax', 'email', 'pager', 'url', 'sms', 'other', name='contact_point_system', create_type=False), nullable=True),
        sa.Column('value', sa.String(), nullable=True),
        sa.Column('use', postgresql.ENUM('home', 'work', 'temp', 'old', 'mobile', name='contact_point_use', create_type=False), nullable=True),
        sa.Column('rank', sa.Integer(), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['location_id'], ['location.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_location_telecom_location_id'), 'location_telecom', ['location_id'], unique=False)

    op.create_table('location_type',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['location_id'], ['location.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_location_type_location_id'), 'location_type', ['location_id'], unique=False)


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_index(op.f('ix_location_type_location_id'), table_name='location_type')
    op.drop_table('location_type')
    op.drop_index(op.f('ix_location_telecom_location_id'), table_name='location_telecom')
    op.drop_table('location_telecom')
    op.drop_index(op.f('ix_location_identifier_location_id'), table_name='location_identifier')
    op.drop_table('location_identifier')
    op.drop_index(op.f('ix_location_hours_of_operation_location_id'), table_name='location_hours_of_operation')
    op.drop_table('location_hours_of_operation')
    op.drop_index(op.f('ix_location_endpoint_location_id'), table_name='location_endpoint')
    op.drop_table('location_endpoint')
    op.drop_index(op.f('ix_location_alias_location_id'), table_name='location_alias')
    op.drop_table('location_alias')
    op.drop_index(op.f('ix_location_user_id'), table_name='location')
    op.drop_index(op.f('ix_location_org_id'), table_name='location')
    op.drop_index(op.f('ix_location_name'), table_name='location')
    op.drop_index(op.f('ix_location_location_id'), table_name='location')
    op.drop_index(op.f('ix_location_id'), table_name='location')
    op.drop_table('location')

    # Drop sequence
    op.execute("DROP SEQUENCE IF EXISTS location_id_seq")

    # Drop new enum types (never drop shared types)
    _location_status.drop(bind, checkfirst=True)
    _location_mode.drop(bind, checkfirst=True)
    _location_part_of_ref_type.drop(bind, checkfirst=True)
    _location_endpoint_ref_type.drop(bind, checkfirst=True)
