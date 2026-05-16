"""add_schedule_tables

Revision ID: 102de3e80915
Revises: f08c20d646a2
Create Date: 2026-05-16 14:30:55.954955

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '102de3e80915'
down_revision: Union[str, None] = 'f08c20d646a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_actor_ref_enum = postgresql.ENUM(
    'Patient', 'Practitioner', 'PractitionerRole', 'RelatedPerson',
    'Device', 'HealthcareService', 'Location',
    name='schedule_actor_reference_type',
)


def upgrade() -> None:
    bind = op.get_bind()

    op.execute("CREATE SEQUENCE IF NOT EXISTS schedule_id_seq START WITH 200000 INCREMENT BY 1")

    _actor_ref_enum.create(bind, checkfirst=True)

    op.create_table('schedule',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('schedule_id', sa.Integer(), server_default=sa.text("nextval('schedule_id_seq')"), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_by', sa.String(), nullable=True),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.Column('planning_horizon_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('planning_horizon_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('comment', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_schedule_id'), 'schedule', ['id'], unique=False)
    op.create_index(op.f('ix_schedule_org_id'), 'schedule', ['org_id'], unique=False)
    op.create_index(op.f('ix_schedule_schedule_id'), 'schedule', ['schedule_id'], unique=True)
    op.create_index(op.f('ix_schedule_user_id'), 'schedule', ['user_id'], unique=False)

    op.create_table('schedule_identifier',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('schedule_id', sa.Integer(), nullable=False),
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
    sa.ForeignKeyConstraint(['schedule_id'], ['schedule.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_schedule_identifier_schedule_id'), 'schedule_identifier', ['schedule_id'], unique=False)

    op.create_table('schedule_service_category',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('schedule_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('coding_system', sa.String(), nullable=True),
    sa.Column('coding_code', sa.String(), nullable=True),
    sa.Column('coding_display', sa.String(), nullable=True),
    sa.Column('text', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['schedule_id'], ['schedule.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_schedule_service_category_schedule_id'), 'schedule_service_category', ['schedule_id'], unique=False)

    op.create_table('schedule_service_type',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('schedule_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('coding_system', sa.String(), nullable=True),
    sa.Column('coding_code', sa.String(), nullable=True),
    sa.Column('coding_display', sa.String(), nullable=True),
    sa.Column('text', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['schedule_id'], ['schedule.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_schedule_service_type_schedule_id'), 'schedule_service_type', ['schedule_id'], unique=False)

    op.create_table('schedule_specialty',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('schedule_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('coding_system', sa.String(), nullable=True),
    sa.Column('coding_code', sa.String(), nullable=True),
    sa.Column('coding_display', sa.String(), nullable=True),
    sa.Column('text', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['schedule_id'], ['schedule.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_schedule_specialty_schedule_id'), 'schedule_specialty', ['schedule_id'], unique=False)

    op.create_table('schedule_actor',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('schedule_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('reference_type', postgresql.ENUM(
        'Patient', 'Practitioner', 'PractitionerRole', 'RelatedPerson',
        'Device', 'HealthcareService', 'Location',
        name='schedule_actor_reference_type', create_type=False,
    ), nullable=True),
    sa.Column('reference_id', sa.Integer(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['schedule_id'], ['schedule.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_schedule_actor_schedule_id'), 'schedule_actor', ['schedule_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_schedule_actor_schedule_id'), table_name='schedule_actor')
    op.drop_table('schedule_actor')
    op.drop_index(op.f('ix_schedule_specialty_schedule_id'), table_name='schedule_specialty')
    op.drop_table('schedule_specialty')
    op.drop_index(op.f('ix_schedule_service_type_schedule_id'), table_name='schedule_service_type')
    op.drop_table('schedule_service_type')
    op.drop_index(op.f('ix_schedule_service_category_schedule_id'), table_name='schedule_service_category')
    op.drop_table('schedule_service_category')
    op.drop_index(op.f('ix_schedule_identifier_schedule_id'), table_name='schedule_identifier')
    op.drop_table('schedule_identifier')
    op.drop_index(op.f('ix_schedule_user_id'), table_name='schedule')
    op.drop_index(op.f('ix_schedule_schedule_id'), table_name='schedule')
    op.drop_index(op.f('ix_schedule_org_id'), table_name='schedule')
    op.drop_index(op.f('ix_schedule_id'), table_name='schedule')
    op.drop_table('schedule')

    op.execute("DROP SEQUENCE IF EXISTS schedule_id_seq")

    bind = op.get_bind()
    _actor_ref_enum.drop(bind, checkfirst=True)
