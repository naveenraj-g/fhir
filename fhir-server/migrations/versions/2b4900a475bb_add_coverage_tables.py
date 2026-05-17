"""add_coverage_tables

Revision ID: 2b4900a475bb
Revises: 7217e5427dc8
Create Date: 2026-05-17 19:22:10.722955

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '2b4900a475bb'
down_revision: Union[str, None] = '7217e5427dc8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# New enum types owned by this migration
_coverage_status = postgresql.ENUM(
    'active', 'cancelled', 'draft', 'entered-in-error',
    name='coverage_status',
)
_coverage_policy_holder_ref = postgresql.ENUM(
    'Patient', 'RelatedPerson', 'Organization',
    name='coverage_policy_holder_reference_type',
)
_coverage_subscriber_ref = postgresql.ENUM(
    'Patient', 'RelatedPerson',
    name='coverage_subscriber_reference_type',
)
_coverage_beneficiary_ref = postgresql.ENUM(
    'Patient',
    name='coverage_beneficiary_reference_type',
)
_coverage_payor_ref = postgresql.ENUM(
    'Organization', 'Patient', 'RelatedPerson',
    name='coverage_payor_reference_type',
)
_coverage_contract_ref = postgresql.ENUM(
    'Contract',
    name='coverage_contract_reference_type',
)


def upgrade() -> None:
    bind = op.get_bind()

    # Create sequence
    op.execute("CREATE SEQUENCE IF NOT EXISTS coverage_id_seq START WITH 240000 INCREMENT BY 1")

    # Create enum types
    _coverage_status.create(bind, checkfirst=True)
    _coverage_policy_holder_ref.create(bind, checkfirst=True)
    _coverage_subscriber_ref.create(bind, checkfirst=True)
    _coverage_beneficiary_ref.create(bind, checkfirst=True)
    _coverage_payor_ref.create(bind, checkfirst=True)
    _coverage_contract_ref.create(bind, checkfirst=True)

    op.create_table('coverage',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('coverage_id', sa.Integer(), server_default=sa.text("nextval('coverage_id_seq')"), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('status', postgresql.ENUM('active', 'cancelled', 'draft', 'entered-in-error', name='coverage_status', create_type=False), nullable=False),
        sa.Column('type_system', sa.String(), nullable=True),
        sa.Column('type_code', sa.String(), nullable=True),
        sa.Column('type_display', sa.String(), nullable=True),
        sa.Column('type_text', sa.String(), nullable=True),
        sa.Column('policy_holder_type', postgresql.ENUM('Patient', 'RelatedPerson', 'Organization', name='coverage_policy_holder_reference_type', create_type=False), nullable=True),
        sa.Column('policy_holder_id', sa.Integer(), nullable=True),
        sa.Column('policy_holder_display', sa.String(), nullable=True),
        sa.Column('subscriber_type', postgresql.ENUM('Patient', 'RelatedPerson', name='coverage_subscriber_reference_type', create_type=False), nullable=True),
        sa.Column('subscriber_id', sa.Integer(), nullable=True),
        sa.Column('subscriber_display', sa.String(), nullable=True),
        sa.Column('subscriber_id_value', sa.String(), nullable=True),
        sa.Column('beneficiary_type', postgresql.ENUM('Patient', name='coverage_beneficiary_reference_type', create_type=False), nullable=False),
        sa.Column('beneficiary_id', sa.Integer(), nullable=False),
        sa.Column('beneficiary_display', sa.String(), nullable=True),
        sa.Column('dependent', sa.String(), nullable=True),
        sa.Column('relationship_system', sa.String(), nullable=True),
        sa.Column('relationship_code', sa.String(), nullable=True),
        sa.Column('relationship_display', sa.String(), nullable=True),
        sa.Column('relationship_text', sa.String(), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('order', sa.Integer(), nullable=True),
        sa.Column('network', sa.String(), nullable=True),
        sa.Column('subrogation', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_coverage_coverage_id'), 'coverage', ['coverage_id'], unique=True)
    op.create_index(op.f('ix_coverage_id'), 'coverage', ['id'], unique=False)
    op.create_index(op.f('ix_coverage_org_id'), 'coverage', ['org_id'], unique=False)
    op.create_index(op.f('ix_coverage_user_id'), 'coverage', ['user_id'], unique=False)

    op.create_table('coverage_class',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('coverage_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('type_system', sa.String(), nullable=True),
        sa.Column('type_code', sa.String(), nullable=True),
        sa.Column('type_display', sa.String(), nullable=True),
        sa.Column('type_text', sa.String(), nullable=True),
        sa.Column('value', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['coverage_id'], ['coverage.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_coverage_class_coverage_id'), 'coverage_class', ['coverage_id'], unique=False)

    op.create_table('coverage_contract',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('coverage_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Contract', name='coverage_contract_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['coverage_id'], ['coverage.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_coverage_contract_coverage_id'), 'coverage_contract', ['coverage_id'], unique=False)

    op.create_table('coverage_cost_to_beneficiary',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('coverage_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('type_system', sa.String(), nullable=True),
        sa.Column('type_code', sa.String(), nullable=True),
        sa.Column('type_display', sa.String(), nullable=True),
        sa.Column('type_text', sa.String(), nullable=True),
        sa.Column('value_quantity_value', sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column('value_quantity_unit', sa.String(), nullable=True),
        sa.Column('value_quantity_system', sa.String(), nullable=True),
        sa.Column('value_quantity_code', sa.String(), nullable=True),
        sa.Column('value_money_value', sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column('value_money_currency', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['coverage_id'], ['coverage.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_coverage_cost_to_beneficiary_coverage_id'), 'coverage_cost_to_beneficiary', ['coverage_id'], unique=False)

    op.create_table('coverage_identifier',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('coverage_id', sa.Integer(), nullable=False),
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
        sa.ForeignKeyConstraint(['coverage_id'], ['coverage.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_coverage_identifier_coverage_id'), 'coverage_identifier', ['coverage_id'], unique=False)

    op.create_table('coverage_payor',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('coverage_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Organization', 'Patient', 'RelatedPerson', name='coverage_payor_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['coverage_id'], ['coverage.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_coverage_payor_coverage_id'), 'coverage_payor', ['coverage_id'], unique=False)

    op.create_table('coverage_cost_to_beneficiary_exception',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('cost_to_beneficiary_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('type_system', sa.String(), nullable=True),
        sa.Column('type_code', sa.String(), nullable=True),
        sa.Column('type_display', sa.String(), nullable=True),
        sa.Column('type_text', sa.String(), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['cost_to_beneficiary_id'], ['coverage_cost_to_beneficiary.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_coverage_cost_to_beneficiary_exception_cost_to_beneficiary_id'), 'coverage_cost_to_beneficiary_exception', ['cost_to_beneficiary_id'], unique=False)


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_index(op.f('ix_coverage_cost_to_beneficiary_exception_cost_to_beneficiary_id'), table_name='coverage_cost_to_beneficiary_exception')
    op.drop_table('coverage_cost_to_beneficiary_exception')
    op.drop_index(op.f('ix_coverage_payor_coverage_id'), table_name='coverage_payor')
    op.drop_table('coverage_payor')
    op.drop_index(op.f('ix_coverage_identifier_coverage_id'), table_name='coverage_identifier')
    op.drop_table('coverage_identifier')
    op.drop_index(op.f('ix_coverage_cost_to_beneficiary_coverage_id'), table_name='coverage_cost_to_beneficiary')
    op.drop_table('coverage_cost_to_beneficiary')
    op.drop_index(op.f('ix_coverage_contract_coverage_id'), table_name='coverage_contract')
    op.drop_table('coverage_contract')
    op.drop_index(op.f('ix_coverage_class_coverage_id'), table_name='coverage_class')
    op.drop_table('coverage_class')
    op.drop_index(op.f('ix_coverage_user_id'), table_name='coverage')
    op.drop_index(op.f('ix_coverage_org_id'), table_name='coverage')
    op.drop_index(op.f('ix_coverage_id'), table_name='coverage')
    op.drop_index(op.f('ix_coverage_coverage_id'), table_name='coverage')
    op.drop_table('coverage')

    # Drop sequence
    op.execute("DROP SEQUENCE IF EXISTS coverage_id_seq")

    # Drop new enum types
    _coverage_status.drop(bind, checkfirst=True)
    _coverage_policy_holder_ref.drop(bind, checkfirst=True)
    _coverage_subscriber_ref.drop(bind, checkfirst=True)
    _coverage_beneficiary_ref.drop(bind, checkfirst=True)
    _coverage_payor_ref.drop(bind, checkfirst=True)
    _coverage_contract_ref.drop(bind, checkfirst=True)
