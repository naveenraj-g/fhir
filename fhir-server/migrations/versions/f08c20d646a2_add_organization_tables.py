"""add_organization_tables

Revision ID: f08c20d646a2
Revises: fe8491c09f90
Create Date: 2026-05-16 14:24:25.710076

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f08c20d646a2'
down_revision: Union[str, None] = 'fe8491c09f90'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# organization_reference_type is a shared type — never create/drop here
_endpoint_ref_enum = postgresql.ENUM('Endpoint', name='organization_endpoint_ref_type')


def upgrade() -> None:
    bind = op.get_bind()

    op.execute("CREATE SEQUENCE IF NOT EXISTS organization_id_seq START WITH 190000 INCREMENT BY 1")

    _endpoint_ref_enum.create(bind, checkfirst=True)

    op.create_table('organization',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('organization_id', sa.Integer(), server_default=sa.text("nextval('organization_id_seq')"), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_by', sa.String(), nullable=True),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('partof_type', postgresql.ENUM('Organization', name='organization_reference_type', create_type=False), nullable=True),
    sa.Column('partof_id', sa.Integer(), nullable=True),
    sa.Column('partof_display', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organization_id'), 'organization', ['id'], unique=False)
    op.create_index(op.f('ix_organization_org_id'), 'organization', ['org_id'], unique=False)
    op.create_index(op.f('ix_organization_organization_id'), 'organization', ['organization_id'], unique=True)
    op.create_index(op.f('ix_organization_user_id'), 'organization', ['user_id'], unique=False)

    op.create_table('organization_identifier',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('organization_id', sa.Integer(), nullable=False),
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
    sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organization_identifier_organization_id'), 'organization_identifier', ['organization_id'], unique=False)

    op.create_table('organization_type',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('organization_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('coding_system', sa.String(), nullable=True),
    sa.Column('coding_code', sa.String(), nullable=True),
    sa.Column('coding_display', sa.String(), nullable=True),
    sa.Column('text', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organization_type_organization_id'), 'organization_type', ['organization_id'], unique=False)

    op.create_table('organization_alias',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('organization_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('value', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organization_alias_organization_id'), 'organization_alias', ['organization_id'], unique=False)

    op.create_table('organization_telecom',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('organization_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('system', sa.String(), nullable=True),
    sa.Column('value', sa.String(), nullable=True),
    sa.Column('use', sa.String(), nullable=True),
    sa.Column('rank', sa.Integer(), nullable=True),
    sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organization_telecom_organization_id'), 'organization_telecom', ['organization_id'], unique=False)

    op.create_table('organization_address',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('organization_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('use', sa.String(), nullable=True),
    sa.Column('type', sa.String(), nullable=True),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('line', sa.Text(), nullable=True),
    sa.Column('city', sa.String(), nullable=True),
    sa.Column('district', sa.String(), nullable=True),
    sa.Column('state', sa.String(), nullable=True),
    sa.Column('postal_code', sa.String(), nullable=True),
    sa.Column('country', sa.String(), nullable=True),
    sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organization_address_organization_id'), 'organization_address', ['organization_id'], unique=False)

    op.create_table('organization_contact',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('organization_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('purpose_system', sa.String(), nullable=True),
    sa.Column('purpose_code', sa.String(), nullable=True),
    sa.Column('purpose_display', sa.String(), nullable=True),
    sa.Column('purpose_text', sa.String(), nullable=True),
    sa.Column('name_use', sa.String(), nullable=True),
    sa.Column('name_text', sa.String(), nullable=True),
    sa.Column('name_family', sa.String(), nullable=True),
    sa.Column('name_given', sa.Text(), nullable=True),
    sa.Column('name_prefix', sa.Text(), nullable=True),
    sa.Column('name_suffix', sa.Text(), nullable=True),
    sa.Column('name_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('name_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('address_use', sa.String(), nullable=True),
    sa.Column('address_type', sa.String(), nullable=True),
    sa.Column('address_text', sa.String(), nullable=True),
    sa.Column('address_line', sa.Text(), nullable=True),
    sa.Column('address_city', sa.String(), nullable=True),
    sa.Column('address_district', sa.String(), nullable=True),
    sa.Column('address_state', sa.String(), nullable=True),
    sa.Column('address_postal_code', sa.String(), nullable=True),
    sa.Column('address_country', sa.String(), nullable=True),
    sa.Column('address_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('address_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organization_contact_organization_id'), 'organization_contact', ['organization_id'], unique=False)

    op.create_table('organization_contact_telecom',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('contact_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('system', sa.String(), nullable=True),
    sa.Column('value', sa.String(), nullable=True),
    sa.Column('use', sa.String(), nullable=True),
    sa.Column('rank', sa.Integer(), nullable=True),
    sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['contact_id'], ['organization_contact.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organization_contact_telecom_contact_id'), 'organization_contact_telecom', ['contact_id'], unique=False)

    op.create_table('organization_endpoint',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('organization_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('reference_type', postgresql.ENUM('Endpoint', name='organization_endpoint_ref_type', create_type=False), nullable=True),
    sa.Column('reference_id', sa.Integer(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organization_endpoint_organization_id'), 'organization_endpoint', ['organization_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_organization_contact_telecom_contact_id'), table_name='organization_contact_telecom')
    op.drop_table('organization_contact_telecom')
    op.drop_index(op.f('ix_organization_endpoint_organization_id'), table_name='organization_endpoint')
    op.drop_table('organization_endpoint')
    op.drop_index(op.f('ix_organization_contact_organization_id'), table_name='organization_contact')
    op.drop_table('organization_contact')
    op.drop_index(op.f('ix_organization_address_organization_id'), table_name='organization_address')
    op.drop_table('organization_address')
    op.drop_index(op.f('ix_organization_telecom_organization_id'), table_name='organization_telecom')
    op.drop_table('organization_telecom')
    op.drop_index(op.f('ix_organization_alias_organization_id'), table_name='organization_alias')
    op.drop_table('organization_alias')
    op.drop_index(op.f('ix_organization_type_organization_id'), table_name='organization_type')
    op.drop_table('organization_type')
    op.drop_index(op.f('ix_organization_identifier_organization_id'), table_name='organization_identifier')
    op.drop_table('organization_identifier')
    op.drop_index(op.f('ix_organization_user_id'), table_name='organization')
    op.drop_index(op.f('ix_organization_organization_id'), table_name='organization')
    op.drop_index(op.f('ix_organization_org_id'), table_name='organization')
    op.drop_index(op.f('ix_organization_id'), table_name='organization')
    op.drop_table('organization')

    op.execute("DROP SEQUENCE IF EXISTS organization_id_seq")

    bind = op.get_bind()
    _endpoint_ref_enum.drop(bind, checkfirst=True)
