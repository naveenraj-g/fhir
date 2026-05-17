"""add_task_tables

Revision ID: 417a95a117df
Revises: ae364d153462
Create Date: 2026-05-18 02:16:16.694760

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '417a95a117df'
down_revision: Union[str, None] = 'ae364d153462'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_task_status = postgresql.ENUM(
    'draft', 'requested', 'received', 'accepted', 'rejected', 'ready',
    'cancelled', 'in-progress', 'on-hold', 'failed', 'completed', 'entered-in-error',
    name='task_status',
)
_task_intent = postgresql.ENUM(
    'unknown', 'proposal', 'plan', 'order', 'original-order', 'reflex-order',
    'filler-order', 'instance-order', 'option',
    name='task_intent',
)
_task_priority = postgresql.ENUM(
    'routine', 'urgent', 'asap', 'stat',
    name='task_priority',
)
_task_requester_ref = postgresql.ENUM(
    'Device', 'Organization', 'Patient', 'Practitioner', 'PractitionerRole', 'RelatedPerson',
    name='task_requester_reference_type',
)
_task_owner_ref = postgresql.ENUM(
    'Practitioner', 'PractitionerRole', 'Organization', 'CareTeam',
    'HealthcareService', 'Patient', 'Device', 'RelatedPerson',
    name='task_owner_reference_type',
)
_task_location_ref = postgresql.ENUM(
    'Location',
    name='task_location_reference_type',
)
_task_insurance_ref = postgresql.ENUM(
    'Coverage', 'ClaimResponse',
    name='task_insurance_reference_type',
)
_task_relevant_history_ref = postgresql.ENUM(
    'Provenance',
    name='task_relevant_history_reference_type',
)
_task_part_of_ref = postgresql.ENUM(
    'Task',
    name='task_part_of_reference_type',
)
_task_restriction_recipient_ref = postgresql.ENUM(
    'Patient', 'Practitioner', 'PractitionerRole', 'RelatedPerson', 'Group', 'Organization',
    name='task_restriction_recipient_reference_type',
)
_encounter_ref = postgresql.ENUM(name='encounter_reference_type', create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    _task_status.create(bind, checkfirst=True)
    _task_intent.create(bind, checkfirst=True)
    _task_priority.create(bind, checkfirst=True)
    _task_requester_ref.create(bind, checkfirst=True)
    _task_owner_ref.create(bind, checkfirst=True)
    _task_location_ref.create(bind, checkfirst=True)
    _task_insurance_ref.create(bind, checkfirst=True)
    _task_relevant_history_ref.create(bind, checkfirst=True)
    _task_part_of_ref.create(bind, checkfirst=True)
    _task_restriction_recipient_ref.create(bind, checkfirst=True)

    op.execute(
        "CREATE SEQUENCE IF NOT EXISTS task_id_seq START WITH 280000 INCREMENT BY 1"
    )

    op.create_table(
        'task',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('task_id', sa.Integer(), server_default=sa.text("nextval('task_id_seq')"), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('status', postgresql.ENUM('draft', 'requested', 'received', 'accepted', 'rejected', 'ready', 'cancelled', 'in-progress', 'on-hold', 'failed', 'completed', 'entered-in-error', name='task_status', create_type=False), nullable=False),
        sa.Column('intent', postgresql.ENUM('unknown', 'proposal', 'plan', 'order', 'original-order', 'reflex-order', 'filler-order', 'instance-order', 'option', name='task_intent', create_type=False), nullable=False),
        sa.Column('priority', postgresql.ENUM('routine', 'urgent', 'asap', 'stat', name='task_priority', create_type=False), nullable=True),
        sa.Column('status_reason_system', sa.String(), nullable=True),
        sa.Column('status_reason_code', sa.String(), nullable=True),
        sa.Column('status_reason_display', sa.String(), nullable=True),
        sa.Column('status_reason_text', sa.String(), nullable=True),
        sa.Column('business_status_system', sa.String(), nullable=True),
        sa.Column('business_status_code', sa.String(), nullable=True),
        sa.Column('business_status_display', sa.String(), nullable=True),
        sa.Column('business_status_text', sa.String(), nullable=True),
        sa.Column('code_system', sa.String(), nullable=True),
        sa.Column('code_code', sa.String(), nullable=True),
        sa.Column('code_display', sa.String(), nullable=True),
        sa.Column('code_text', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('instantiates_canonical', sa.String(), nullable=True),
        sa.Column('instantiates_uri', sa.String(), nullable=True),
        sa.Column('group_identifier_use', sa.String(), nullable=True),
        sa.Column('group_identifier_system', sa.String(), nullable=True),
        sa.Column('group_identifier_value', sa.String(), nullable=True),
        sa.Column('group_identifier_type_system', sa.String(), nullable=True),
        sa.Column('group_identifier_type_code', sa.String(), nullable=True),
        sa.Column('group_identifier_type_display', sa.String(), nullable=True),
        sa.Column('group_identifier_type_text', sa.String(), nullable=True),
        sa.Column('focus_type', sa.String(), nullable=True),
        sa.Column('focus_id', sa.Integer(), nullable=True),
        sa.Column('focus_display', sa.String(), nullable=True),
        sa.Column('for_type', sa.String(), nullable=True),
        sa.Column('for_id', sa.Integer(), nullable=True),
        sa.Column('for_display', sa.String(), nullable=True),
        sa.Column('encounter_type', postgresql.ENUM('Encounter', name='encounter_reference_type', create_type=False), nullable=True),
        sa.Column('encounter_id', sa.Integer(), nullable=True),
        sa.Column('encounter_display', sa.String(), nullable=True),
        sa.Column('execution_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('execution_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('authored_on', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_modified', sa.DateTime(timezone=True), nullable=True),
        sa.Column('requester_type', postgresql.ENUM('Device', 'Organization', 'Patient', 'Practitioner', 'PractitionerRole', 'RelatedPerson', name='task_requester_reference_type', create_type=False), nullable=True),
        sa.Column('requester_id', sa.Integer(), nullable=True),
        sa.Column('requester_display', sa.String(), nullable=True),
        sa.Column('owner_type', postgresql.ENUM('Practitioner', 'PractitionerRole', 'Organization', 'CareTeam', 'HealthcareService', 'Patient', 'Device', 'RelatedPerson', name='task_owner_reference_type', create_type=False), nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=True),
        sa.Column('owner_display', sa.String(), nullable=True),
        sa.Column('location_type', postgresql.ENUM('Location', name='task_location_reference_type', create_type=False), nullable=True),
        sa.Column('location_id', sa.Integer(), nullable=True),
        sa.Column('location_display', sa.String(), nullable=True),
        sa.Column('reason_code_system', sa.String(), nullable=True),
        sa.Column('reason_code_code', sa.String(), nullable=True),
        sa.Column('reason_code_display', sa.String(), nullable=True),
        sa.Column('reason_code_text', sa.String(), nullable=True),
        sa.Column('reason_reference_type', sa.String(), nullable=True),
        sa.Column('reason_reference_id', sa.Integer(), nullable=True),
        sa.Column('reason_reference_display', sa.String(), nullable=True),
        sa.Column('restriction_repetitions', sa.Integer(), nullable=True),
        sa.Column('restriction_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('restriction_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_task_id'), 'task', ['id'], unique=False)
    op.create_index(op.f('ix_task_org_id'), 'task', ['org_id'], unique=False)
    op.create_index(op.f('ix_task_task_id'), 'task', ['task_id'], unique=True)
    op.create_index(op.f('ix_task_user_id'), 'task', ['user_id'], unique=False)

    op.create_table(
        'task_based_on',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('reference_type', sa.String(), nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['task_id'], ['task.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_task_based_on_task_id'), 'task_based_on', ['task_id'], unique=False)

    op.create_table(
        'task_identifier',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
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
        sa.ForeignKeyConstraint(['task_id'], ['task.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_task_identifier_task_id'), 'task_identifier', ['task_id'], unique=False)

    op.create_table(
        'task_input',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('type_system', sa.String(), nullable=True),
        sa.Column('type_code', sa.String(), nullable=True),
        sa.Column('type_display', sa.String(), nullable=True),
        sa.Column('type_text', sa.String(), nullable=True),
        sa.Column('value_boolean', sa.Boolean(), nullable=True),
        sa.Column('value_code', sa.String(), nullable=True),
        sa.Column('value_date', sa.Date(), nullable=True),
        sa.Column('value_date_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('value_decimal', sa.Numeric(), nullable=True),
        sa.Column('value_integer', sa.Integer(), nullable=True),
        sa.Column('value_string', sa.String(), nullable=True),
        sa.Column('value_uri', sa.String(), nullable=True),
        sa.Column('value_reference_type', sa.String(), nullable=True),
        sa.Column('value_reference_id', sa.Integer(), nullable=True),
        sa.Column('value_reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['task_id'], ['task.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_task_input_task_id'), 'task_input', ['task_id'], unique=False)

    op.create_table(
        'task_insurance',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Coverage', 'ClaimResponse', name='task_insurance_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['task_id'], ['task.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_task_insurance_task_id'), 'task_insurance', ['task_id'], unique=False)

    op.create_table(
        'task_note',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('author_string', sa.String(), nullable=True),
        sa.Column('author_reference_type', sa.String(), nullable=True),
        sa.Column('author_reference_id', sa.Integer(), nullable=True),
        sa.Column('author_reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['task_id'], ['task.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_task_note_task_id'), 'task_note', ['task_id'], unique=False)

    op.create_table(
        'task_output',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('type_system', sa.String(), nullable=True),
        sa.Column('type_code', sa.String(), nullable=True),
        sa.Column('type_display', sa.String(), nullable=True),
        sa.Column('type_text', sa.String(), nullable=True),
        sa.Column('value_boolean', sa.Boolean(), nullable=True),
        sa.Column('value_code', sa.String(), nullable=True),
        sa.Column('value_date', sa.Date(), nullable=True),
        sa.Column('value_date_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('value_decimal', sa.Numeric(), nullable=True),
        sa.Column('value_integer', sa.Integer(), nullable=True),
        sa.Column('value_string', sa.String(), nullable=True),
        sa.Column('value_uri', sa.String(), nullable=True),
        sa.Column('value_reference_type', sa.String(), nullable=True),
        sa.Column('value_reference_id', sa.Integer(), nullable=True),
        sa.Column('value_reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['task_id'], ['task.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_task_output_task_id'), 'task_output', ['task_id'], unique=False)

    op.create_table(
        'task_part_of',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Task', name='task_part_of_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['task_id'], ['task.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_task_part_of_task_id'), 'task_part_of', ['task_id'], unique=False)

    op.create_table(
        'task_performer_type',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['task_id'], ['task.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_task_performer_type_task_id'), 'task_performer_type', ['task_id'], unique=False)

    op.create_table(
        'task_relevant_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Provenance', name='task_relevant_history_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['task_id'], ['task.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_task_relevant_history_task_id'), 'task_relevant_history', ['task_id'], unique=False)

    op.create_table(
        'task_restriction_recipient',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Patient', 'Practitioner', 'PractitionerRole', 'RelatedPerson', 'Group', 'Organization', name='task_restriction_recipient_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['task_id'], ['task.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_task_restriction_recipient_task_id'), 'task_restriction_recipient', ['task_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_task_restriction_recipient_task_id'), table_name='task_restriction_recipient')
    op.drop_table('task_restriction_recipient')
    op.drop_index(op.f('ix_task_relevant_history_task_id'), table_name='task_relevant_history')
    op.drop_table('task_relevant_history')
    op.drop_index(op.f('ix_task_performer_type_task_id'), table_name='task_performer_type')
    op.drop_table('task_performer_type')
    op.drop_index(op.f('ix_task_part_of_task_id'), table_name='task_part_of')
    op.drop_table('task_part_of')
    op.drop_index(op.f('ix_task_output_task_id'), table_name='task_output')
    op.drop_table('task_output')
    op.drop_index(op.f('ix_task_note_task_id'), table_name='task_note')
    op.drop_table('task_note')
    op.drop_index(op.f('ix_task_insurance_task_id'), table_name='task_insurance')
    op.drop_table('task_insurance')
    op.drop_index(op.f('ix_task_input_task_id'), table_name='task_input')
    op.drop_table('task_input')
    op.drop_index(op.f('ix_task_identifier_task_id'), table_name='task_identifier')
    op.drop_table('task_identifier')
    op.drop_index(op.f('ix_task_based_on_task_id'), table_name='task_based_on')
    op.drop_table('task_based_on')
    op.drop_index(op.f('ix_task_user_id'), table_name='task')
    op.drop_index(op.f('ix_task_task_id'), table_name='task')
    op.drop_index(op.f('ix_task_org_id'), table_name='task')
    op.drop_index(op.f('ix_task_id'), table_name='task')
    op.drop_table('task')

    op.execute("DROP SEQUENCE IF EXISTS task_id_seq")

    bind = op.get_bind()
    _task_restriction_recipient_ref.drop(bind, checkfirst=True)
    _task_part_of_ref.drop(bind, checkfirst=True)
    _task_relevant_history_ref.drop(bind, checkfirst=True)
    _task_insurance_ref.drop(bind, checkfirst=True)
    _task_location_ref.drop(bind, checkfirst=True)
    _task_owner_ref.drop(bind, checkfirst=True)
    _task_requester_ref.drop(bind, checkfirst=True)
    _task_priority.drop(bind, checkfirst=True)
    _task_intent.drop(bind, checkfirst=True)
    _task_status.drop(bind, checkfirst=True)
