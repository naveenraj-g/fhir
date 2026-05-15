"""patient_contact_role_additional_name_address

Revision ID: 3fe34d49a2a1
Revises: 8d6f48e4ac7e
Create Date: 2026-05-15 14:08:58.932753

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '3fe34d49a2a1'
down_revision: Union[str, None] = '8d6f48e4ac7e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Existing PostgreSQL enum types — create_type=False prevents redundant CREATE TYPE.
_address_use = postgresql.ENUM('home', 'work', 'temp', 'old', 'billing', name='address_use', create_type=False)
_address_type = postgresql.ENUM('postal', 'physical', 'both', name='address_type', create_type=False)
_human_name_use = postgresql.ENUM('usual', 'official', 'temp', 'nickname', 'anonymous', 'old', 'maiden', name='human_name_use', create_type=False)


def upgrade() -> None:
    op.create_table(
        'patient_contact_role',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('contact_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['contact_id'], ['patient_contact.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_patient_contact_role_contact_id'), 'patient_contact_role', ['contact_id'], unique=False)

    op.create_table(
        'patient_contact_additional_name',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('contact_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('use', _human_name_use, nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('family', sa.String(), nullable=True),
        sa.Column('given', sa.Text(), nullable=True),
        sa.Column('prefix', sa.Text(), nullable=True),
        sa.Column('suffix', sa.Text(), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['contact_id'], ['patient_contact.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_patient_contact_additional_name_contact_id'), 'patient_contact_additional_name', ['contact_id'], unique=False)

    op.create_table(
        'patient_contact_additional_address',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('contact_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('use', _address_use, nullable=True),
        sa.Column('type', _address_type, nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('line', sa.Text(), nullable=True),
        sa.Column('city', sa.String(), nullable=True),
        sa.Column('district', sa.String(), nullable=True),
        sa.Column('state', sa.String(), nullable=True),
        sa.Column('postal_code', sa.String(), nullable=True),
        sa.Column('country', sa.String(), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['contact_id'], ['patient_contact.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_patient_contact_additional_address_contact_id'), 'patient_contact_additional_address', ['contact_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_patient_contact_additional_address_contact_id'), table_name='patient_contact_additional_address')
    op.drop_table('patient_contact_additional_address')
    op.drop_index(op.f('ix_patient_contact_additional_name_contact_id'), table_name='patient_contact_additional_name')
    op.drop_table('patient_contact_additional_name')
    op.drop_index(op.f('ix_patient_contact_role_contact_id'), table_name='patient_contact_role')
    op.drop_table('patient_contact_role')
