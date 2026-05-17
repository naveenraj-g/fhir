"""add_medication_tables

Revision ID: 1f89d47009a2
Revises: 2b4900a475bb
Create Date: 2026-05-17 20:04:45.534144

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '1f89d47009a2'
down_revision: Union[str, None] = '2b4900a475bb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# New enum types owned by this migration
_medication_status = postgresql.ENUM(
    'active', 'inactive', 'entered-in-error',
    name='medication_status',
)
_medication_ingredient_item_ref = postgresql.ENUM(
    'Substance', 'Medication',
    name='medication_ingredient_item_reference_type',
)


def upgrade() -> None:
    bind = op.get_bind()

    # Create sequence
    op.execute("CREATE SEQUENCE IF NOT EXISTS medication_id_seq START WITH 250000 INCREMENT BY 1")

    # Create new enum types
    _medication_status.create(bind, checkfirst=True)
    _medication_ingredient_item_ref.create(bind, checkfirst=True)
    # organization_reference_type is shared — create_type=False, never create/drop here

    op.create_table('medication',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('medication_id', sa.Integer(), server_default=sa.text("nextval('medication_id_seq')"), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('code_system', sa.String(), nullable=True),
        sa.Column('code_code', sa.String(), nullable=True),
        sa.Column('code_display', sa.String(), nullable=True),
        sa.Column('code_text', sa.String(), nullable=True),
        sa.Column('status', postgresql.ENUM('active', 'inactive', 'entered-in-error', name='medication_status', create_type=False), nullable=True),
        sa.Column('manufacturer_type', postgresql.ENUM('Organization', name='organization_reference_type', create_type=False), nullable=True),
        sa.Column('manufacturer_id', sa.Integer(), nullable=True),
        sa.Column('manufacturer_display', sa.String(), nullable=True),
        sa.Column('form_system', sa.String(), nullable=True),
        sa.Column('form_code', sa.String(), nullable=True),
        sa.Column('form_display', sa.String(), nullable=True),
        sa.Column('form_text', sa.String(), nullable=True),
        sa.Column('amount_numerator_value', sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column('amount_numerator_unit', sa.String(), nullable=True),
        sa.Column('amount_numerator_system', sa.String(), nullable=True),
        sa.Column('amount_numerator_code', sa.String(), nullable=True),
        sa.Column('amount_denominator_value', sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column('amount_denominator_unit', sa.String(), nullable=True),
        sa.Column('amount_denominator_system', sa.String(), nullable=True),
        sa.Column('amount_denominator_code', sa.String(), nullable=True),
        sa.Column('batch_lot_number', sa.String(), nullable=True),
        sa.Column('batch_expiration_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_medication_id'), 'medication', ['id'], unique=False)
    op.create_index(op.f('ix_medication_medication_id'), 'medication', ['medication_id'], unique=True)
    op.create_index(op.f('ix_medication_org_id'), 'medication', ['org_id'], unique=False)
    op.create_index(op.f('ix_medication_user_id'), 'medication', ['user_id'], unique=False)

    op.create_table('medication_identifier',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('medication_id', sa.Integer(), nullable=False),
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
        sa.ForeignKeyConstraint(['medication_id'], ['medication.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_medication_identifier_medication_id'), 'medication_identifier', ['medication_id'], unique=False)

    op.create_table('medication_ingredient',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('medication_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('item_codeable_concept_system', sa.String(), nullable=True),
        sa.Column('item_codeable_concept_code', sa.String(), nullable=True),
        sa.Column('item_codeable_concept_display', sa.String(), nullable=True),
        sa.Column('item_codeable_concept_text', sa.String(), nullable=True),
        sa.Column('item_reference_type', postgresql.ENUM('Substance', 'Medication', name='medication_ingredient_item_reference_type', create_type=False), nullable=True),
        sa.Column('item_reference_id', sa.Integer(), nullable=True),
        sa.Column('item_reference_display', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('strength_numerator_value', sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column('strength_numerator_unit', sa.String(), nullable=True),
        sa.Column('strength_numerator_system', sa.String(), nullable=True),
        sa.Column('strength_numerator_code', sa.String(), nullable=True),
        sa.Column('strength_denominator_value', sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column('strength_denominator_unit', sa.String(), nullable=True),
        sa.Column('strength_denominator_system', sa.String(), nullable=True),
        sa.Column('strength_denominator_code', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['medication_id'], ['medication.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_medication_ingredient_medication_id'), 'medication_ingredient', ['medication_id'], unique=False)


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_index(op.f('ix_medication_ingredient_medication_id'), table_name='medication_ingredient')
    op.drop_table('medication_ingredient')
    op.drop_index(op.f('ix_medication_identifier_medication_id'), table_name='medication_identifier')
    op.drop_table('medication_identifier')
    op.drop_index(op.f('ix_medication_user_id'), table_name='medication')
    op.drop_index(op.f('ix_medication_org_id'), table_name='medication')
    op.drop_index(op.f('ix_medication_medication_id'), table_name='medication')
    op.drop_index(op.f('ix_medication_id'), table_name='medication')
    op.drop_table('medication')

    # Drop sequence
    op.execute("DROP SEQUENCE IF EXISTS medication_id_seq")

    # Drop new enum types (not organization_reference_type — it is shared)
    _medication_status.drop(bind, checkfirst=True)
    _medication_ingredient_item_ref.drop(bind, checkfirst=True)
