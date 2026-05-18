"""add care_plan tables

Revision ID: b08509de3a0b
Revises: 417a95a117df
Create Date: 2026-05-18 04:16:33.225852

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b08509de3a0b'
down_revision: Union[str, None] = '417a95a117df'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ---------------------------------------------------------------------------
# Module-level enum declarations (TitleCase values)
# ---------------------------------------------------------------------------

_care_plan_status = postgresql.ENUM(
    'draft', 'active', 'on-hold', 'revoked', 'completed', 'entered-in-error', 'unknown',
    name='care_plan_status',
)
_care_plan_intent = postgresql.ENUM(
    'proposal', 'plan', 'order', 'option',
    name='care_plan_intent',
)
_care_plan_subject_reference_type = postgresql.ENUM(
    'Patient', 'Group',
    name='care_plan_subject_reference_type',
)
_care_plan_author_reference_type = postgresql.ENUM(
    'Patient', 'Practitioner', 'PractitionerRole', 'Device', 'RelatedPerson', 'Organization', 'CareTeam',
    name='care_plan_author_reference_type',
)
_care_plan_activity_reference_type = postgresql.ENUM(
    'Appointment', 'CommunicationRequest', 'DeviceRequest', 'MedicationRequest',
    'NutritionOrder', 'Task', 'ServiceRequest', 'VisionPrescription', 'RequestGroup',
    name='care_plan_activity_reference_type',
)
_care_plan_detail_activity_status = postgresql.ENUM(
    'not-started', 'scheduled', 'in-progress', 'on-hold', 'completed',
    'cancelled', 'stopped', 'unknown', 'entered-in-error',
    name='care_plan_detail_activity_status',
)
_care_plan_detail_location_reference_type = postgresql.ENUM(
    'Location',
    name='care_plan_detail_location_reference_type',
)
_care_plan_detail_product_reference_type = postgresql.ENUM(
    'Medication', 'Substance',
    name='care_plan_detail_product_reference_type',
)
_care_plan_addresses_reference_type = postgresql.ENUM(
    'Condition',
    name='care_plan_addresses_reference_type',
)
_care_plan_based_on_reference_type = postgresql.ENUM(
    'CarePlan',
    name='care_plan_based_on_reference_type',
)
_care_plan_care_team_reference_type = postgresql.ENUM(
    'CareTeam',
    name='care_plan_care_team_reference_type',
)
_care_plan_contributor_reference_type = postgresql.ENUM(
    'Patient', 'Practitioner', 'PractitionerRole', 'Device', 'RelatedPerson', 'Organization', 'CareTeam',
    name='care_plan_contributor_reference_type',
)
_care_plan_goal_reference_type = postgresql.ENUM(
    'Goal',
    name='care_plan_goal_reference_type',
)
_care_plan_part_of_reference_type = postgresql.ENUM(
    'CarePlan',
    name='care_plan_part_of_reference_type',
)
_care_plan_replaces_reference_type = postgresql.ENUM(
    'CarePlan',
    name='care_plan_replaces_reference_type',
)
_care_plan_detail_goal_reference_type = postgresql.ENUM(
    'Goal',
    name='care_plan_detail_goal_reference_type',
)
_care_plan_detail_performer_reference_type = postgresql.ENUM(
    'Practitioner', 'PractitionerRole', 'Organization', 'RelatedPerson',
    'Patient', 'CareTeam', 'HealthcareService', 'Device',
    name='care_plan_detail_performer_reference_type',
)
_care_plan_detail_reason_reference_type = postgresql.ENUM(
    'Condition', 'Observation', 'DiagnosticReport', 'DocumentReference',
    name='care_plan_detail_reason_reference_type',
)
# Shared — already exists in DB; never create or drop
_encounter_reference_type = postgresql.ENUM(
    'Encounter',
    name='encounter_reference_type',
    create_type=False,
)


def upgrade() -> None:
    # Create sequence
    op.execute("CREATE SEQUENCE IF NOT EXISTS care_plan_id_seq START WITH 290000 INCREMENT BY 1")

    # Create all new enum types
    _care_plan_status.create(op.get_bind(), checkfirst=True)
    _care_plan_intent.create(op.get_bind(), checkfirst=True)
    _care_plan_subject_reference_type.create(op.get_bind(), checkfirst=True)
    _care_plan_author_reference_type.create(op.get_bind(), checkfirst=True)
    _care_plan_activity_reference_type.create(op.get_bind(), checkfirst=True)
    _care_plan_detail_activity_status.create(op.get_bind(), checkfirst=True)
    _care_plan_detail_location_reference_type.create(op.get_bind(), checkfirst=True)
    _care_plan_detail_product_reference_type.create(op.get_bind(), checkfirst=True)
    _care_plan_addresses_reference_type.create(op.get_bind(), checkfirst=True)
    _care_plan_based_on_reference_type.create(op.get_bind(), checkfirst=True)
    _care_plan_care_team_reference_type.create(op.get_bind(), checkfirst=True)
    _care_plan_contributor_reference_type.create(op.get_bind(), checkfirst=True)
    _care_plan_goal_reference_type.create(op.get_bind(), checkfirst=True)
    _care_plan_part_of_reference_type.create(op.get_bind(), checkfirst=True)
    _care_plan_replaces_reference_type.create(op.get_bind(), checkfirst=True)
    _care_plan_detail_goal_reference_type.create(op.get_bind(), checkfirst=True)
    _care_plan_detail_performer_reference_type.create(op.get_bind(), checkfirst=True)
    _care_plan_detail_reason_reference_type.create(op.get_bind(), checkfirst=True)

    op.create_table('care_plan',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('care_plan_id', sa.Integer(), server_default=sa.text("nextval('care_plan_id_seq')"), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('status', postgresql.ENUM('draft', 'active', 'on-hold', 'revoked', 'completed', 'entered-in-error', 'unknown', name='care_plan_status', create_type=False), nullable=False),
    sa.Column('intent', postgresql.ENUM('proposal', 'plan', 'order', 'option', name='care_plan_intent', create_type=False), nullable=False),
    sa.Column('title', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('subject_type', postgresql.ENUM('Patient', 'Group', name='care_plan_subject_reference_type', create_type=False), nullable=True),
    sa.Column('subject_id', sa.Integer(), nullable=True),
    sa.Column('subject_display', sa.String(), nullable=True),
    sa.Column('encounter_type', postgresql.ENUM('Encounter', name='encounter_reference_type', create_type=False), nullable=True),
    sa.Column('encounter_id', sa.Integer(), nullable=True),
    sa.Column('encounter_display', sa.String(), nullable=True),
    sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created', sa.DateTime(timezone=True), nullable=True),
    sa.Column('author_type', postgresql.ENUM('Patient', 'Practitioner', 'PractitionerRole', 'Device', 'RelatedPerson', 'Organization', 'CareTeam', name='care_plan_author_reference_type', create_type=False), nullable=True),
    sa.Column('author_id', sa.Integer(), nullable=True),
    sa.Column('author_display', sa.String(), nullable=True),
    sa.Column('instantiates_canonical', sa.Text(), nullable=True),
    sa.Column('instantiates_uri', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_by', sa.String(), nullable=True),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_care_plan_care_plan_id'), 'care_plan', ['care_plan_id'], unique=True)
    op.create_index(op.f('ix_care_plan_id'), 'care_plan', ['id'], unique=False)
    op.create_index(op.f('ix_care_plan_org_id'), 'care_plan', ['org_id'], unique=False)
    op.create_index(op.f('ix_care_plan_user_id'), 'care_plan', ['user_id'], unique=False)

    op.create_table('care_plan_activity',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('care_plan_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('reference_type', postgresql.ENUM('Appointment', 'CommunicationRequest', 'DeviceRequest', 'MedicationRequest', 'NutritionOrder', 'Task', 'ServiceRequest', 'VisionPrescription', 'RequestGroup', name='care_plan_activity_reference_type', create_type=False), nullable=True),
    sa.Column('reference_id', sa.Integer(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.Column('detail_kind', sa.String(), nullable=True),
    sa.Column('detail_instantiates_canonical', sa.Text(), nullable=True),
    sa.Column('detail_instantiates_uri', sa.Text(), nullable=True),
    sa.Column('detail_code_system', sa.String(), nullable=True),
    sa.Column('detail_code_code', sa.String(), nullable=True),
    sa.Column('detail_code_display', sa.String(), nullable=True),
    sa.Column('detail_code_text', sa.String(), nullable=True),
    sa.Column('detail_status', postgresql.ENUM('not-started', 'scheduled', 'in-progress', 'on-hold', 'completed', 'cancelled', 'stopped', 'unknown', 'entered-in-error', name='care_plan_detail_activity_status', create_type=False), nullable=True),
    sa.Column('detail_status_reason_system', sa.String(), nullable=True),
    sa.Column('detail_status_reason_code', sa.String(), nullable=True),
    sa.Column('detail_status_reason_display', sa.String(), nullable=True),
    sa.Column('detail_status_reason_text', sa.String(), nullable=True),
    sa.Column('detail_do_not_perform', sa.Boolean(), nullable=True),
    sa.Column('detail_scheduled_timing_event', sa.Text(), nullable=True),
    sa.Column('detail_scheduled_timing_code_system', sa.String(), nullable=True),
    sa.Column('detail_scheduled_timing_code_code', sa.String(), nullable=True),
    sa.Column('detail_scheduled_timing_code_display', sa.String(), nullable=True),
    sa.Column('detail_scheduled_timing_code_text', sa.String(), nullable=True),
    sa.Column('detail_scheduled_timing_repeat_count', sa.Integer(), nullable=True),
    sa.Column('detail_scheduled_timing_repeat_count_max', sa.Integer(), nullable=True),
    sa.Column('detail_scheduled_timing_repeat_duration', sa.Numeric(), nullable=True),
    sa.Column('detail_scheduled_timing_repeat_duration_max', sa.Numeric(), nullable=True),
    sa.Column('detail_scheduled_timing_repeat_duration_unit', sa.String(), nullable=True),
    sa.Column('detail_scheduled_timing_repeat_frequency', sa.Integer(), nullable=True),
    sa.Column('detail_scheduled_timing_repeat_frequency_max', sa.Integer(), nullable=True),
    sa.Column('detail_scheduled_timing_repeat_period', sa.Numeric(), nullable=True),
    sa.Column('detail_scheduled_timing_repeat_period_max', sa.Numeric(), nullable=True),
    sa.Column('detail_scheduled_timing_repeat_period_unit', sa.String(), nullable=True),
    sa.Column('detail_scheduled_timing_repeat_day_of_week', sa.Text(), nullable=True),
    sa.Column('detail_scheduled_timing_repeat_time_of_day', sa.Text(), nullable=True),
    sa.Column('detail_scheduled_timing_repeat_when', sa.Text(), nullable=True),
    sa.Column('detail_scheduled_timing_repeat_offset', sa.Integer(), nullable=True),
    sa.Column('detail_scheduled_timing_repeat_bounds_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('detail_scheduled_timing_repeat_bounds_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('detail_scheduled_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('detail_scheduled_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('detail_scheduled_string', sa.String(), nullable=True),
    sa.Column('detail_location_type', postgresql.ENUM('Location', name='care_plan_detail_location_reference_type', create_type=False), nullable=True),
    sa.Column('detail_location_id', sa.Integer(), nullable=True),
    sa.Column('detail_location_display', sa.String(), nullable=True),
    sa.Column('detail_product_codeable_concept_system', sa.String(), nullable=True),
    sa.Column('detail_product_codeable_concept_code', sa.String(), nullable=True),
    sa.Column('detail_product_codeable_concept_display', sa.String(), nullable=True),
    sa.Column('detail_product_codeable_concept_text', sa.String(), nullable=True),
    sa.Column('detail_product_reference_type', postgresql.ENUM('Medication', 'Substance', name='care_plan_detail_product_reference_type', create_type=False), nullable=True),
    sa.Column('detail_product_reference_id', sa.Integer(), nullable=True),
    sa.Column('detail_product_reference_display', sa.String(), nullable=True),
    sa.Column('detail_daily_amount_value', sa.Numeric(), nullable=True),
    sa.Column('detail_daily_amount_unit', sa.String(), nullable=True),
    sa.Column('detail_daily_amount_system', sa.String(), nullable=True),
    sa.Column('detail_daily_amount_code', sa.String(), nullable=True),
    sa.Column('detail_quantity_value', sa.Numeric(), nullable=True),
    sa.Column('detail_quantity_unit', sa.String(), nullable=True),
    sa.Column('detail_quantity_system', sa.String(), nullable=True),
    sa.Column('detail_quantity_code', sa.String(), nullable=True),
    sa.Column('detail_description', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['care_plan_id'], ['care_plan.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_care_plan_activity_care_plan_id'), 'care_plan_activity', ['care_plan_id'], unique=False)

    op.create_table('care_plan_addresses',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('care_plan_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('reference_type', postgresql.ENUM('Condition', name='care_plan_addresses_reference_type', create_type=False), nullable=True),
    sa.Column('reference_id', sa.Integer(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['care_plan_id'], ['care_plan.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_care_plan_addresses_care_plan_id'), 'care_plan_addresses', ['care_plan_id'], unique=False)

    op.create_table('care_plan_based_on',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('care_plan_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('reference_type', postgresql.ENUM('CarePlan', name='care_plan_based_on_reference_type', create_type=False), nullable=True),
    sa.Column('reference_id', sa.Integer(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['care_plan_id'], ['care_plan.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_care_plan_based_on_care_plan_id'), 'care_plan_based_on', ['care_plan_id'], unique=False)

    op.create_table('care_plan_care_team',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('care_plan_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('reference_type', postgresql.ENUM('CareTeam', name='care_plan_care_team_reference_type', create_type=False), nullable=True),
    sa.Column('reference_id', sa.Integer(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['care_plan_id'], ['care_plan.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_care_plan_care_team_care_plan_id'), 'care_plan_care_team', ['care_plan_id'], unique=False)

    op.create_table('care_plan_category',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('care_plan_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('coding_system', sa.String(), nullable=True),
    sa.Column('coding_code', sa.String(), nullable=True),
    sa.Column('coding_display', sa.String(), nullable=True),
    sa.Column('text', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['care_plan_id'], ['care_plan.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_care_plan_category_care_plan_id'), 'care_plan_category', ['care_plan_id'], unique=False)

    op.create_table('care_plan_contributor',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('care_plan_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('reference_type', postgresql.ENUM('Patient', 'Practitioner', 'PractitionerRole', 'Device', 'RelatedPerson', 'Organization', 'CareTeam', name='care_plan_contributor_reference_type', create_type=False), nullable=True),
    sa.Column('reference_id', sa.Integer(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['care_plan_id'], ['care_plan.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_care_plan_contributor_care_plan_id'), 'care_plan_contributor', ['care_plan_id'], unique=False)

    op.create_table('care_plan_goal',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('care_plan_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('reference_type', postgresql.ENUM('Goal', name='care_plan_goal_reference_type', create_type=False), nullable=True),
    sa.Column('reference_id', sa.Integer(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['care_plan_id'], ['care_plan.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_care_plan_goal_care_plan_id'), 'care_plan_goal', ['care_plan_id'], unique=False)

    op.create_table('care_plan_identifier',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('care_plan_id', sa.Integer(), nullable=False),
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
    sa.ForeignKeyConstraint(['care_plan_id'], ['care_plan.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_care_plan_identifier_care_plan_id'), 'care_plan_identifier', ['care_plan_id'], unique=False)

    op.create_table('care_plan_note',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('care_plan_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('time', sa.DateTime(timezone=True), nullable=True),
    sa.Column('author_string', sa.String(), nullable=True),
    sa.Column('author_reference_type', sa.String(), nullable=True),
    sa.Column('author_reference_id', sa.Integer(), nullable=True),
    sa.Column('author_reference_display', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['care_plan_id'], ['care_plan.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_care_plan_note_care_plan_id'), 'care_plan_note', ['care_plan_id'], unique=False)

    op.create_table('care_plan_part_of',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('care_plan_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('reference_type', postgresql.ENUM('CarePlan', name='care_plan_part_of_reference_type', create_type=False), nullable=True),
    sa.Column('reference_id', sa.Integer(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['care_plan_id'], ['care_plan.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_care_plan_part_of_care_plan_id'), 'care_plan_part_of', ['care_plan_id'], unique=False)

    op.create_table('care_plan_replaces',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('care_plan_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('reference_type', postgresql.ENUM('CarePlan', name='care_plan_replaces_reference_type', create_type=False), nullable=True),
    sa.Column('reference_id', sa.Integer(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['care_plan_id'], ['care_plan.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_care_plan_replaces_care_plan_id'), 'care_plan_replaces', ['care_plan_id'], unique=False)

    op.create_table('care_plan_supporting_info',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('care_plan_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('reference_type', sa.String(), nullable=True),
    sa.Column('reference_id', sa.Integer(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['care_plan_id'], ['care_plan.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_care_plan_supporting_info_care_plan_id'), 'care_plan_supporting_info', ['care_plan_id'], unique=False)

    op.create_table('care_plan_activity_detail_goal',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('activity_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('reference_type', postgresql.ENUM('Goal', name='care_plan_detail_goal_reference_type', create_type=False), nullable=True),
    sa.Column('reference_id', sa.Integer(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['activity_id'], ['care_plan_activity.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_care_plan_activity_detail_goal_activity_id'), 'care_plan_activity_detail_goal', ['activity_id'], unique=False)

    op.create_table('care_plan_activity_detail_performer',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('activity_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('reference_type', postgresql.ENUM('Practitioner', 'PractitionerRole', 'Organization', 'RelatedPerson', 'Patient', 'CareTeam', 'HealthcareService', 'Device', name='care_plan_detail_performer_reference_type', create_type=False), nullable=True),
    sa.Column('reference_id', sa.Integer(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['activity_id'], ['care_plan_activity.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_care_plan_activity_detail_performer_activity_id'), 'care_plan_activity_detail_performer', ['activity_id'], unique=False)

    op.create_table('care_plan_activity_detail_reason_code',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('activity_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('coding_system', sa.String(), nullable=True),
    sa.Column('coding_code', sa.String(), nullable=True),
    sa.Column('coding_display', sa.String(), nullable=True),
    sa.Column('text', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['activity_id'], ['care_plan_activity.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_care_plan_activity_detail_reason_code_activity_id'), 'care_plan_activity_detail_reason_code', ['activity_id'], unique=False)

    op.create_table('care_plan_activity_detail_reason_ref',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('activity_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('reference_type', postgresql.ENUM('Condition', 'Observation', 'DiagnosticReport', 'DocumentReference', name='care_plan_detail_reason_reference_type', create_type=False), nullable=True),
    sa.Column('reference_id', sa.Integer(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['activity_id'], ['care_plan_activity.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_care_plan_activity_detail_reason_ref_activity_id'), 'care_plan_activity_detail_reason_ref', ['activity_id'], unique=False)

    op.create_table('care_plan_activity_outcome_cc',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('activity_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('coding_system', sa.String(), nullable=True),
    sa.Column('coding_code', sa.String(), nullable=True),
    sa.Column('coding_display', sa.String(), nullable=True),
    sa.Column('text', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['activity_id'], ['care_plan_activity.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_care_plan_activity_outcome_cc_activity_id'), 'care_plan_activity_outcome_cc', ['activity_id'], unique=False)

    op.create_table('care_plan_activity_outcome_ref',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('activity_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('reference_type', sa.String(), nullable=True),
    sa.Column('reference_id', sa.Integer(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['activity_id'], ['care_plan_activity.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_care_plan_activity_outcome_ref_activity_id'), 'care_plan_activity_outcome_ref', ['activity_id'], unique=False)

    op.create_table('care_plan_activity_progress',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('activity_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('time', sa.DateTime(timezone=True), nullable=True),
    sa.Column('author_string', sa.String(), nullable=True),
    sa.Column('author_reference_type', sa.String(), nullable=True),
    sa.Column('author_reference_id', sa.Integer(), nullable=True),
    sa.Column('author_reference_display', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['activity_id'], ['care_plan_activity.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_care_plan_activity_progress_activity_id'), 'care_plan_activity_progress', ['activity_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_care_plan_activity_progress_activity_id'), table_name='care_plan_activity_progress')
    op.drop_table('care_plan_activity_progress')
    op.drop_index(op.f('ix_care_plan_activity_outcome_ref_activity_id'), table_name='care_plan_activity_outcome_ref')
    op.drop_table('care_plan_activity_outcome_ref')
    op.drop_index(op.f('ix_care_plan_activity_outcome_cc_activity_id'), table_name='care_plan_activity_outcome_cc')
    op.drop_table('care_plan_activity_outcome_cc')
    op.drop_index(op.f('ix_care_plan_activity_detail_reason_ref_activity_id'), table_name='care_plan_activity_detail_reason_ref')
    op.drop_table('care_plan_activity_detail_reason_ref')
    op.drop_index(op.f('ix_care_plan_activity_detail_reason_code_activity_id'), table_name='care_plan_activity_detail_reason_code')
    op.drop_table('care_plan_activity_detail_reason_code')
    op.drop_index(op.f('ix_care_plan_activity_detail_performer_activity_id'), table_name='care_plan_activity_detail_performer')
    op.drop_table('care_plan_activity_detail_performer')
    op.drop_index(op.f('ix_care_plan_activity_detail_goal_activity_id'), table_name='care_plan_activity_detail_goal')
    op.drop_table('care_plan_activity_detail_goal')
    op.drop_index(op.f('ix_care_plan_supporting_info_care_plan_id'), table_name='care_plan_supporting_info')
    op.drop_table('care_plan_supporting_info')
    op.drop_index(op.f('ix_care_plan_replaces_care_plan_id'), table_name='care_plan_replaces')
    op.drop_table('care_plan_replaces')
    op.drop_index(op.f('ix_care_plan_part_of_care_plan_id'), table_name='care_plan_part_of')
    op.drop_table('care_plan_part_of')
    op.drop_index(op.f('ix_care_plan_note_care_plan_id'), table_name='care_plan_note')
    op.drop_table('care_plan_note')
    op.drop_index(op.f('ix_care_plan_identifier_care_plan_id'), table_name='care_plan_identifier')
    op.drop_table('care_plan_identifier')
    op.drop_index(op.f('ix_care_plan_goal_care_plan_id'), table_name='care_plan_goal')
    op.drop_table('care_plan_goal')
    op.drop_index(op.f('ix_care_plan_contributor_care_plan_id'), table_name='care_plan_contributor')
    op.drop_table('care_plan_contributor')
    op.drop_index(op.f('ix_care_plan_category_care_plan_id'), table_name='care_plan_category')
    op.drop_table('care_plan_category')
    op.drop_index(op.f('ix_care_plan_care_team_care_plan_id'), table_name='care_plan_care_team')
    op.drop_table('care_plan_care_team')
    op.drop_index(op.f('ix_care_plan_based_on_care_plan_id'), table_name='care_plan_based_on')
    op.drop_table('care_plan_based_on')
    op.drop_index(op.f('ix_care_plan_addresses_care_plan_id'), table_name='care_plan_addresses')
    op.drop_table('care_plan_addresses')
    op.drop_index(op.f('ix_care_plan_activity_care_plan_id'), table_name='care_plan_activity')
    op.drop_table('care_plan_activity')
    op.drop_index(op.f('ix_care_plan_user_id'), table_name='care_plan')
    op.drop_index(op.f('ix_care_plan_org_id'), table_name='care_plan')
    op.drop_index(op.f('ix_care_plan_id'), table_name='care_plan')
    op.drop_index(op.f('ix_care_plan_care_plan_id'), table_name='care_plan')
    op.drop_table('care_plan')

    op.execute("DROP SEQUENCE IF EXISTS care_plan_id_seq")

    # Drop new enum types (not encounter_reference_type — shared)
    _care_plan_detail_reason_reference_type.drop(op.get_bind(), checkfirst=True)
    _care_plan_detail_performer_reference_type.drop(op.get_bind(), checkfirst=True)
    _care_plan_detail_goal_reference_type.drop(op.get_bind(), checkfirst=True)
    _care_plan_replaces_reference_type.drop(op.get_bind(), checkfirst=True)
    _care_plan_part_of_reference_type.drop(op.get_bind(), checkfirst=True)
    _care_plan_goal_reference_type.drop(op.get_bind(), checkfirst=True)
    _care_plan_contributor_reference_type.drop(op.get_bind(), checkfirst=True)
    _care_plan_care_team_reference_type.drop(op.get_bind(), checkfirst=True)
    _care_plan_based_on_reference_type.drop(op.get_bind(), checkfirst=True)
    _care_plan_addresses_reference_type.drop(op.get_bind(), checkfirst=True)
    _care_plan_detail_product_reference_type.drop(op.get_bind(), checkfirst=True)
    _care_plan_detail_location_reference_type.drop(op.get_bind(), checkfirst=True)
    _care_plan_detail_activity_status.drop(op.get_bind(), checkfirst=True)
    _care_plan_activity_reference_type.drop(op.get_bind(), checkfirst=True)
    _care_plan_author_reference_type.drop(op.get_bind(), checkfirst=True)
    _care_plan_subject_reference_type.drop(op.get_bind(), checkfirst=True)
    _care_plan_intent.drop(op.get_bind(), checkfirst=True)
    _care_plan_status.drop(op.get_bind(), checkfirst=True)
