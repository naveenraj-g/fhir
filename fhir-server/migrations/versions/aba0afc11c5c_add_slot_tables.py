"""add_slot_tables

Revision ID: aba0afc11c5c
Revises: cf1f1632a16f
Create Date: 2026-05-17 10:22:12.822543

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'aba0afc11c5c'
down_revision: Union[str, None] = 'cf1f1632a16f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_slot_schedule_reference_type = postgresql.ENUM(
    'Schedule',
    name='slot_schedule_reference_type',
)
_slot_status = postgresql.ENUM(
    'busy',
    'free',
    'busy-unavailable',
    'busy-tentative',
    'entered-in-error',
    name='slot_status',
)
# shared — already exists in DB
_identifier_use = postgresql.ENUM(
    'usual', 'official', 'temp', 'secondary', 'old',
    name='identifier_use',
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    _slot_schedule_reference_type.create(bind, checkfirst=True)
    _slot_status.create(bind, checkfirst=True)

    op.execute("CREATE SEQUENCE IF NOT EXISTS slot_id_seq START WITH 220000 INCREMENT BY 1")

    op.create_table(
        'slot',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('slot_id', sa.Integer(), server_default=sa.text("nextval('slot_id_seq')"), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('schedule_type', postgresql.ENUM('Schedule', name='slot_schedule_reference_type', create_type=False), nullable=True),
        sa.Column('schedule_fk_id', sa.Integer(), nullable=True),
        sa.Column('schedule_display', sa.String(), nullable=True),
        sa.Column('status', postgresql.ENUM('busy', 'free', 'busy-unavailable', 'busy-tentative', 'entered-in-error', name='slot_status', create_type=False), nullable=False),
        sa.Column('start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('appointment_type_system', sa.String(), nullable=True),
        sa.Column('appointment_type_code', sa.String(), nullable=True),
        sa.Column('appointment_type_display', sa.String(), nullable=True),
        sa.Column('appointment_type_text', sa.String(), nullable=True),
        sa.Column('overbooked', sa.Boolean(), nullable=True),
        sa.Column('comment', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['schedule_fk_id'], ['schedule.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_slot_id'), 'slot', ['id'], unique=False)
    op.create_index(op.f('ix_slot_org_id'), 'slot', ['org_id'], unique=False)
    op.create_index(op.f('ix_slot_schedule_fk_id'), 'slot', ['schedule_fk_id'], unique=False)
    op.create_index(op.f('ix_slot_slot_id'), 'slot', ['slot_id'], unique=True)
    op.create_index(op.f('ix_slot_user_id'), 'slot', ['user_id'], unique=False)

    op.create_table(
        'slot_identifier',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('slot_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('type_system', sa.String(), nullable=True),
        sa.Column('type_code', sa.String(), nullable=True),
        sa.Column('type_display', sa.String(), nullable=True),
        sa.Column('type_text', sa.String(), nullable=True),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('value', sa.String(), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('assigner', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['slot_id'], ['slot.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_slot_identifier_slot_id'), 'slot_identifier', ['slot_id'], unique=False)

    op.create_table(
        'slot_service_category',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('slot_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['slot_id'], ['slot.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_slot_service_category_slot_id'), 'slot_service_category', ['slot_id'], unique=False)

    op.create_table(
        'slot_service_type',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('slot_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['slot_id'], ['slot.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_slot_service_type_slot_id'), 'slot_service_type', ['slot_id'], unique=False)

    op.create_table(
        'slot_specialty',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('slot_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['slot_id'], ['slot.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_slot_specialty_slot_id'), 'slot_specialty', ['slot_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_slot_specialty_slot_id'), table_name='slot_specialty')
    op.drop_table('slot_specialty')
    op.drop_index(op.f('ix_slot_service_type_slot_id'), table_name='slot_service_type')
    op.drop_table('slot_service_type')
    op.drop_index(op.f('ix_slot_service_category_slot_id'), table_name='slot_service_category')
    op.drop_table('slot_service_category')
    op.drop_index(op.f('ix_slot_identifier_slot_id'), table_name='slot_identifier')
    op.drop_table('slot_identifier')
    op.drop_index(op.f('ix_slot_user_id'), table_name='slot')
    op.drop_index(op.f('ix_slot_slot_id'), table_name='slot')
    op.drop_index(op.f('ix_slot_schedule_fk_id'), table_name='slot')
    op.drop_index(op.f('ix_slot_org_id'), table_name='slot')
    op.drop_index(op.f('ix_slot_id'), table_name='slot')
    op.drop_table('slot')

    op.execute("DROP SEQUENCE IF EXISTS slot_id_seq")

    bind = op.get_bind()
    _slot_status.drop(bind, checkfirst=True)
    _slot_schedule_reference_type.drop(bind, checkfirst=True)
