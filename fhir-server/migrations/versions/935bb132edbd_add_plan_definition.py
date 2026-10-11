"""add plan_definition

Revision ID: 935bb132edbd
Revises: cdec5c0664e5
Create Date: 2026-10-10 19:46:01.751249

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '935bb132edbd'
down_revision: Union[str, None] = 'cdec5c0664e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    postgresql.ENUM('draft', 'active', 'retired', 'unknown', name='plan_definition_status').create(op.get_bind(), checkfirst=True)
    postgresql.ENUM('Group', name='plan_definition_group_ref_type').create(op.get_bind(), checkfirst=True)
    postgresql.ENUM('routine', 'urgent', 'asap', 'stat', name='plan_definition_action_priority').create(op.get_bind(), checkfirst=True)
    postgresql.ENUM('visual_group', 'logical_group', 'sentence_group', name='plan_definition_grouping_behavior').create(op.get_bind(), checkfirst=True)
    postgresql.ENUM('any', 'all', 'all_or_none', 'exactly_one', 'at_most_one', 'one_or_more', name='plan_definition_selection_behavior').create(op.get_bind(), checkfirst=True)
    postgresql.ENUM('must', 'could', 'must_unless_documented', name='plan_definition_required_behavior').create(op.get_bind(), checkfirst=True)
    postgresql.ENUM('yes', 'no', name='plan_definition_precheck_behavior').create(op.get_bind(), checkfirst=True)
    postgresql.ENUM('single', 'multiple', name='plan_definition_cardinality_behavior').create(op.get_bind(), checkfirst=True)
    postgresql.ENUM('contact', 'author', 'editor', 'reviewer', 'endorser', name='plan_definition_contact_kind').create(op.get_bind(), checkfirst=True)
    postgresql.ENUM('PlanDefinition', 'ResearchStudy', 'InsurancePlan', 'HealthcareService', 'Group', 'Location', 'Organization', name='plan_definition_use_context_ref_type').create(op.get_bind(), checkfirst=True)
    postgresql.ENUM('applicability', 'start', 'stop', name='plan_definition_condition_kind').create(op.get_bind(), checkfirst=True)
    postgresql.ENUM('patient', 'practitioner', 'related_person', 'device', name='plan_definition_participant_type').create(op.get_bind(), checkfirst=True)
    postgresql.ENUM('before_start', 'before', 'before_end', 'concurrent_with_start', 'concurrent', 'concurrent_with_end', 'after_start', 'after', 'after_end', name='plan_definition_relationship_type').create(op.get_bind(), checkfirst=True)
    postgresql.ENUM('named_event', 'periodic', 'data_changed', 'data_added', 'data_modified', 'data_removed', 'data_accessed', 'data_access_ended', name='plan_definition_trigger_type').create(op.get_bind(), checkfirst=True)
    postgresql.ENUM('Schedule', name='plan_definition_schedule_ref_type').create(op.get_bind(), checkfirst=True)
    postgresql.ENUM('plan', 'goal', 'action', name='plan_definition_related_artifact_scope').create(op.get_bind(), checkfirst=True)
    postgresql.ENUM('documentation', 'justification', 'citation', 'predecessor', 'successor', 'derived_from', 'depends_on', 'composed_of', name='plan_definition_related_artifact_type').create(op.get_bind(), checkfirst=True)
    postgresql.ENUM('input', 'output', 'trigger', name='plan_definition_dr_role').create(op.get_bind(), checkfirst=True)
    postgresql.ENUM('ascending', 'descending', name='plan_definition_sort_direction').create(op.get_bind(), checkfirst=True)
    op.execute('CREATE SEQUENCE IF NOT EXISTS plan_definition_pub_seq START 400000 INCREMENT 1')
    op.create_table('plan_definition',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('plan_definition_id', sa.Integer(), server_default=sa.text("nextval('plan_definition_pub_seq')"), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('url', sa.String(), nullable=True),
    sa.Column('version', sa.String(), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('title', sa.String(), nullable=True),
    sa.Column('subtitle', sa.String(), nullable=True),
    sa.Column('status', postgresql.ENUM('draft', 'active', 'retired', 'unknown', name='plan_definition_status', create_type=False), nullable=False),
    sa.Column('experimental', sa.Boolean(), nullable=True),
    sa.Column('date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('publisher', sa.String(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('purpose', sa.Text(), nullable=True),
    sa.Column('usage', sa.Text(), nullable=True),
    sa.Column('copyright', sa.Text(), nullable=True),
    sa.Column('approval_date', sa.Date(), nullable=True),
    sa.Column('last_review_date', sa.Date(), nullable=True),
    sa.Column('type_system', sa.String(), nullable=True),
    sa.Column('type_code', sa.String(), nullable=True),
    sa.Column('type_display', sa.String(), nullable=True),
    sa.Column('type_text', sa.String(), nullable=True),
    sa.Column('subject_cc_system', sa.String(), nullable=True),
    sa.Column('subject_cc_code', sa.String(), nullable=True),
    sa.Column('subject_cc_display', sa.String(), nullable=True),
    sa.Column('subject_cc_text', sa.String(), nullable=True),
    sa.Column('subject_reference_type', postgresql.ENUM('Group', name='plan_definition_group_ref_type', create_type=False), nullable=True),
    sa.Column('subject_reference_id', sa.Integer(), nullable=True),
    sa.Column('subject_reference_display', sa.String(), nullable=True),
    sa.Column('effective_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('effective_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_by', sa.String(), nullable=True),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_date'), 'plan_definition', ['date'], unique=False)
    op.create_index(op.f('ix_plan_definition_id'), 'plan_definition', ['id'], unique=False)
    op.create_index(op.f('ix_plan_definition_name'), 'plan_definition', ['name'], unique=False)
    op.create_index(op.f('ix_plan_definition_org_id'), 'plan_definition', ['org_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_plan_definition_id'), 'plan_definition', ['plan_definition_id'], unique=True)
    op.create_index(op.f('ix_plan_definition_status'), 'plan_definition', ['status'], unique=False)
    op.create_index(op.f('ix_plan_definition_subject_reference_id'), 'plan_definition', ['subject_reference_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_type_code'), 'plan_definition', ['type_code'], unique=False)
    op.create_index(op.f('ix_plan_definition_url'), 'plan_definition', ['url'], unique=False)
    op.create_index(op.f('ix_plan_definition_user_id'), 'plan_definition', ['user_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_version'), 'plan_definition', ['version'], unique=False)
    op.create_table('plan_definition_action',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('plan_definition_id', sa.Integer(), nullable=False),
    sa.Column('parent_action_id', sa.Integer(), nullable=True),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.Column('element_id', sa.String(), nullable=True),
    sa.Column('prefix', sa.String(), nullable=True),
    sa.Column('title', sa.String(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('text_equivalent', sa.Text(), nullable=True),
    sa.Column('priority', postgresql.ENUM('routine', 'urgent', 'asap', 'stat', name='plan_definition_action_priority', create_type=False), nullable=True),
    sa.Column('subject_cc_system', sa.String(), nullable=True),
    sa.Column('subject_cc_code', sa.String(), nullable=True),
    sa.Column('subject_cc_display', sa.String(), nullable=True),
    sa.Column('subject_cc_text', sa.String(), nullable=True),
    sa.Column('subject_reference_type', postgresql.ENUM('Group', name='plan_definition_group_ref_type', create_type=False), nullable=True),
    sa.Column('subject_reference_id', sa.Integer(), nullable=True),
    sa.Column('subject_reference_display', sa.String(), nullable=True),
    sa.Column('timing_datetime', sa.DateTime(timezone=True), nullable=True),
    sa.Column('timing_age_value', sa.Float(), nullable=True),
    sa.Column('timing_age_comparator', sa.String(), nullable=True),
    sa.Column('timing_age_unit', sa.String(), nullable=True),
    sa.Column('timing_age_system', sa.String(), nullable=True),
    sa.Column('timing_age_code', sa.String(), nullable=True),
    sa.Column('timing_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('timing_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('timing_duration_value', sa.Float(), nullable=True),
    sa.Column('timing_duration_comparator', sa.String(), nullable=True),
    sa.Column('timing_duration_unit', sa.String(), nullable=True),
    sa.Column('timing_duration_system', sa.String(), nullable=True),
    sa.Column('timing_duration_code', sa.String(), nullable=True),
    sa.Column('timing_range_low_value', sa.Float(), nullable=True),
    sa.Column('timing_range_low_unit', sa.String(), nullable=True),
    sa.Column('timing_range_low_system', sa.String(), nullable=True),
    sa.Column('timing_range_low_code', sa.String(), nullable=True),
    sa.Column('timing_range_high_value', sa.Float(), nullable=True),
    sa.Column('timing_range_high_unit', sa.String(), nullable=True),
    sa.Column('timing_range_high_system', sa.String(), nullable=True),
    sa.Column('timing_range_high_code', sa.String(), nullable=True),
    sa.Column('timing_timing_event', sa.Text(), nullable=True),
    sa.Column('timing_timing_code_system', sa.String(), nullable=True),
    sa.Column('timing_timing_code_code', sa.String(), nullable=True),
    sa.Column('timing_timing_code_display', sa.String(), nullable=True),
    sa.Column('timing_timing_code_text', sa.String(), nullable=True),
    sa.Column('timing_timing_repeat_bounds_duration_value', sa.Float(), nullable=True),
    sa.Column('timing_timing_repeat_bounds_duration_comparator', sa.String(), nullable=True),
    sa.Column('timing_timing_repeat_bounds_duration_unit', sa.String(), nullable=True),
    sa.Column('timing_timing_repeat_bounds_duration_system', sa.String(), nullable=True),
    sa.Column('timing_timing_repeat_bounds_duration_code', sa.String(), nullable=True),
    sa.Column('timing_timing_repeat_bounds_range_low_value', sa.Float(), nullable=True),
    sa.Column('timing_timing_repeat_bounds_range_low_unit', sa.String(), nullable=True),
    sa.Column('timing_timing_repeat_bounds_range_low_system', sa.String(), nullable=True),
    sa.Column('timing_timing_repeat_bounds_range_low_code', sa.String(), nullable=True),
    sa.Column('timing_timing_repeat_bounds_range_high_value', sa.Float(), nullable=True),
    sa.Column('timing_timing_repeat_bounds_range_high_unit', sa.String(), nullable=True),
    sa.Column('timing_timing_repeat_bounds_range_high_system', sa.String(), nullable=True),
    sa.Column('timing_timing_repeat_bounds_range_high_code', sa.String(), nullable=True),
    sa.Column('timing_timing_repeat_bounds_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('timing_timing_repeat_bounds_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('timing_timing_repeat_count', sa.Integer(), nullable=True),
    sa.Column('timing_timing_repeat_count_max', sa.Integer(), nullable=True),
    sa.Column('timing_timing_repeat_duration', sa.Float(), nullable=True),
    sa.Column('timing_timing_repeat_duration_max', sa.Float(), nullable=True),
    sa.Column('timing_timing_repeat_duration_unit', sa.String(), nullable=True),
    sa.Column('timing_timing_repeat_frequency', sa.Integer(), nullable=True),
    sa.Column('timing_timing_repeat_frequency_max', sa.Integer(), nullable=True),
    sa.Column('timing_timing_repeat_period', sa.Float(), nullable=True),
    sa.Column('timing_timing_repeat_period_max', sa.Float(), nullable=True),
    sa.Column('timing_timing_repeat_period_unit', sa.String(), nullable=True),
    sa.Column('timing_timing_repeat_day_of_week', sa.Text(), nullable=True),
    sa.Column('timing_timing_repeat_time_of_day', sa.Text(), nullable=True),
    sa.Column('timing_timing_repeat_when', sa.Text(), nullable=True),
    sa.Column('timing_timing_repeat_offset', sa.Integer(), nullable=True),
    sa.Column('type_system', sa.String(), nullable=True),
    sa.Column('type_code', sa.String(), nullable=True),
    sa.Column('type_display', sa.String(), nullable=True),
    sa.Column('type_text', sa.String(), nullable=True),
    sa.Column('grouping_behavior', postgresql.ENUM('visual_group', 'logical_group', 'sentence_group', name='plan_definition_grouping_behavior', create_type=False), nullable=True),
    sa.Column('selection_behavior', postgresql.ENUM('any', 'all', 'all_or_none', 'exactly_one', 'at_most_one', 'one_or_more', name='plan_definition_selection_behavior', create_type=False), nullable=True),
    sa.Column('required_behavior', postgresql.ENUM('must', 'could', 'must_unless_documented', name='plan_definition_required_behavior', create_type=False), nullable=True),
    sa.Column('precheck_behavior', postgresql.ENUM('yes', 'no', name='plan_definition_precheck_behavior', create_type=False), nullable=True),
    sa.Column('cardinality_behavior', postgresql.ENUM('single', 'multiple', name='plan_definition_cardinality_behavior', create_type=False), nullable=True),
    sa.Column('definition_canonical', sa.String(), nullable=True),
    sa.Column('definition_uri', sa.String(), nullable=True),
    sa.Column('transform', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['parent_action_id'], ['plan_definition_action.id'], ),
    sa.ForeignKeyConstraint(['plan_definition_id'], ['plan_definition.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_action_definition_canonical'), 'plan_definition_action', ['definition_canonical'], unique=False)
    op.create_index(op.f('ix_plan_definition_action_definition_uri'), 'plan_definition_action', ['definition_uri'], unique=False)
    op.create_index(op.f('ix_plan_definition_action_element_id'), 'plan_definition_action', ['element_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_action_id'), 'plan_definition_action', ['id'], unique=False)
    op.create_index(op.f('ix_plan_definition_action_parent_action_id'), 'plan_definition_action', ['parent_action_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_action_plan_definition_id'), 'plan_definition_action', ['plan_definition_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_action_subject_reference_id'), 'plan_definition_action', ['subject_reference_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_action_type_code'), 'plan_definition_action', ['type_code'], unique=False)
    op.create_table('plan_definition_contact',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('plan_definition_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('kind', postgresql.ENUM('contact', 'author', 'editor', 'reviewer', 'endorser', name='plan_definition_contact_kind', create_type=False), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['plan_definition_id'], ['plan_definition.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_contact_kind'), 'plan_definition_contact', ['kind'], unique=False)
    op.create_index(op.f('ix_plan_definition_contact_plan_definition_id'), 'plan_definition_contact', ['plan_definition_id'], unique=False)
    op.create_table('plan_definition_goal',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('plan_definition_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('element_id', sa.String(), nullable=True),
    sa.Column('category_system', sa.String(), nullable=True),
    sa.Column('category_code', sa.String(), nullable=True),
    sa.Column('category_display', sa.String(), nullable=True),
    sa.Column('category_text', sa.String(), nullable=True),
    sa.Column('description_system', sa.String(), nullable=True),
    sa.Column('description_code', sa.String(), nullable=True),
    sa.Column('description_display', sa.String(), nullable=True),
    sa.Column('description_text', sa.String(), nullable=True),
    sa.Column('priority_system', sa.String(), nullable=True),
    sa.Column('priority_code', sa.String(), nullable=True),
    sa.Column('priority_display', sa.String(), nullable=True),
    sa.Column('priority_text', sa.String(), nullable=True),
    sa.Column('start_system', sa.String(), nullable=True),
    sa.Column('start_code', sa.String(), nullable=True),
    sa.Column('start_display', sa.String(), nullable=True),
    sa.Column('start_text', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['plan_definition_id'], ['plan_definition.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_goal_description_code'), 'plan_definition_goal', ['description_code'], unique=False)
    op.create_index(op.f('ix_plan_definition_goal_element_id'), 'plan_definition_goal', ['element_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_goal_plan_definition_id'), 'plan_definition_goal', ['plan_definition_id'], unique=False)
    op.create_table('plan_definition_identifier',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('plan_definition_id', sa.Integer(), nullable=False),
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
    sa.ForeignKeyConstraint(['plan_definition_id'], ['plan_definition.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_identifier_plan_definition_id'), 'plan_definition_identifier', ['plan_definition_id'], unique=False)
    op.create_table('plan_definition_jurisdiction',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('plan_definition_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('coding_system', sa.String(), nullable=True),
    sa.Column('coding_code', sa.String(), nullable=True),
    sa.Column('coding_display', sa.String(), nullable=True),
    sa.Column('text', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['plan_definition_id'], ['plan_definition.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_jurisdiction_coding_code'), 'plan_definition_jurisdiction', ['coding_code'], unique=False)
    op.create_index(op.f('ix_plan_definition_jurisdiction_plan_definition_id'), 'plan_definition_jurisdiction', ['plan_definition_id'], unique=False)
    op.create_table('plan_definition_library',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('plan_definition_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('canonical', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['plan_definition_id'], ['plan_definition.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_library_canonical'), 'plan_definition_library', ['canonical'], unique=False)
    op.create_index(op.f('ix_plan_definition_library_plan_definition_id'), 'plan_definition_library', ['plan_definition_id'], unique=False)
    op.create_table('plan_definition_topic',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('plan_definition_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('coding_system', sa.String(), nullable=True),
    sa.Column('coding_code', sa.String(), nullable=True),
    sa.Column('coding_display', sa.String(), nullable=True),
    sa.Column('text', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['plan_definition_id'], ['plan_definition.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_topic_coding_code'), 'plan_definition_topic', ['coding_code'], unique=False)
    op.create_index(op.f('ix_plan_definition_topic_plan_definition_id'), 'plan_definition_topic', ['plan_definition_id'], unique=False)
    op.create_table('plan_definition_use_context',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('plan_definition_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('code_system', sa.String(), nullable=True),
    sa.Column('code_code', sa.String(), nullable=True),
    sa.Column('code_display', sa.String(), nullable=True),
    sa.Column('value_cc_system', sa.String(), nullable=True),
    sa.Column('value_cc_code', sa.String(), nullable=True),
    sa.Column('value_cc_display', sa.String(), nullable=True),
    sa.Column('value_cc_text', sa.String(), nullable=True),
    sa.Column('value_quantity_value', sa.Float(), nullable=True),
    sa.Column('value_quantity_unit', sa.String(), nullable=True),
    sa.Column('value_quantity_system', sa.String(), nullable=True),
    sa.Column('value_quantity_code', sa.String(), nullable=True),
    sa.Column('value_range_low_value', sa.Float(), nullable=True),
    sa.Column('value_range_low_unit', sa.String(), nullable=True),
    sa.Column('value_range_low_system', sa.String(), nullable=True),
    sa.Column('value_range_low_code', sa.String(), nullable=True),
    sa.Column('value_range_high_value', sa.Float(), nullable=True),
    sa.Column('value_range_high_unit', sa.String(), nullable=True),
    sa.Column('value_range_high_system', sa.String(), nullable=True),
    sa.Column('value_range_high_code', sa.String(), nullable=True),
    sa.Column('value_reference_type', postgresql.ENUM('PlanDefinition', 'ResearchStudy', 'InsurancePlan', 'HealthcareService', 'Group', 'Location', 'Organization', name='plan_definition_use_context_ref_type', create_type=False), nullable=True),
    sa.Column('value_reference_id', sa.Integer(), nullable=True),
    sa.Column('value_reference_display', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['plan_definition_id'], ['plan_definition.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_use_context_plan_definition_id'), 'plan_definition_use_context', ['plan_definition_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_use_context_value_reference_id'), 'plan_definition_use_context', ['value_reference_id'], unique=False)
    op.create_table('plan_definition_action_code',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('plan_definition_id', sa.Integer(), nullable=False),
    sa.Column('action_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('kind', sa.String(), nullable=False),
    sa.Column('coding_system', sa.String(), nullable=True),
    sa.Column('coding_code', sa.String(), nullable=True),
    sa.Column('coding_display', sa.String(), nullable=True),
    sa.Column('text', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['action_id'], ['plan_definition_action.id'], ),
    sa.ForeignKeyConstraint(['plan_definition_id'], ['plan_definition.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_action_code_action_id'), 'plan_definition_action_code', ['action_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_action_code_coding_code'), 'plan_definition_action_code', ['coding_code'], unique=False)
    op.create_index(op.f('ix_plan_definition_action_code_kind'), 'plan_definition_action_code', ['kind'], unique=False)
    op.create_index(op.f('ix_plan_definition_action_code_plan_definition_id'), 'plan_definition_action_code', ['plan_definition_id'], unique=False)
    op.create_table('plan_definition_action_condition',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('plan_definition_id', sa.Integer(), nullable=False),
    sa.Column('action_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('kind', postgresql.ENUM('applicability', 'start', 'stop', name='plan_definition_condition_kind', create_type=False), nullable=False),
    sa.Column('expression_description', sa.String(), nullable=True),
    sa.Column('expression_name', sa.String(), nullable=True),
    sa.Column('expression_language', sa.String(), nullable=True),
    sa.Column('expression_expression', sa.Text(), nullable=True),
    sa.Column('expression_reference', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['action_id'], ['plan_definition_action.id'], ),
    sa.ForeignKeyConstraint(['plan_definition_id'], ['plan_definition.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_action_condition_action_id'), 'plan_definition_action_condition', ['action_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_action_condition_plan_definition_id'), 'plan_definition_action_condition', ['plan_definition_id'], unique=False)
    op.create_table('plan_definition_action_dynamic_value',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('plan_definition_id', sa.Integer(), nullable=False),
    sa.Column('action_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('path', sa.String(), nullable=True),
    sa.Column('expression_description', sa.String(), nullable=True),
    sa.Column('expression_name', sa.String(), nullable=True),
    sa.Column('expression_language', sa.String(), nullable=True),
    sa.Column('expression_expression', sa.Text(), nullable=True),
    sa.Column('expression_reference', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['action_id'], ['plan_definition_action.id'], ),
    sa.ForeignKeyConstraint(['plan_definition_id'], ['plan_definition.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_action_dynamic_value_action_id'), 'plan_definition_action_dynamic_value', ['action_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_action_dynamic_value_plan_definition_id'), 'plan_definition_action_dynamic_value', ['plan_definition_id'], unique=False)
    op.create_table('plan_definition_action_goal_id',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('plan_definition_id', sa.Integer(), nullable=False),
    sa.Column('action_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('goal_element_id', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['action_id'], ['plan_definition_action.id'], ),
    sa.ForeignKeyConstraint(['plan_definition_id'], ['plan_definition.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_action_goal_id_action_id'), 'plan_definition_action_goal_id', ['action_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_action_goal_id_plan_definition_id'), 'plan_definition_action_goal_id', ['plan_definition_id'], unique=False)
    op.create_table('plan_definition_action_participant',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('plan_definition_id', sa.Integer(), nullable=False),
    sa.Column('action_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('type', postgresql.ENUM('patient', 'practitioner', 'related_person', 'device', name='plan_definition_participant_type', create_type=False), nullable=False),
    sa.Column('role_system', sa.String(), nullable=True),
    sa.Column('role_code', sa.String(), nullable=True),
    sa.Column('role_display', sa.String(), nullable=True),
    sa.Column('role_text', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['action_id'], ['plan_definition_action.id'], ),
    sa.ForeignKeyConstraint(['plan_definition_id'], ['plan_definition.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_action_participant_action_id'), 'plan_definition_action_participant', ['action_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_action_participant_plan_definition_id'), 'plan_definition_action_participant', ['plan_definition_id'], unique=False)
    op.create_table('plan_definition_action_related_action',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('plan_definition_id', sa.Integer(), nullable=False),
    sa.Column('action_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('related_action_id', sa.String(), nullable=False),
    sa.Column('relationship_type', postgresql.ENUM('before_start', 'before', 'before_end', 'concurrent_with_start', 'concurrent', 'concurrent_with_end', 'after_start', 'after', 'after_end', name='plan_definition_relationship_type', create_type=False), nullable=False),
    sa.Column('offset_duration_value', sa.Float(), nullable=True),
    sa.Column('offset_duration_comparator', sa.String(), nullable=True),
    sa.Column('offset_duration_unit', sa.String(), nullable=True),
    sa.Column('offset_duration_system', sa.String(), nullable=True),
    sa.Column('offset_duration_code', sa.String(), nullable=True),
    sa.Column('offset_range_low_value', sa.Float(), nullable=True),
    sa.Column('offset_range_low_unit', sa.String(), nullable=True),
    sa.Column('offset_range_low_system', sa.String(), nullable=True),
    sa.Column('offset_range_low_code', sa.String(), nullable=True),
    sa.Column('offset_range_high_value', sa.Float(), nullable=True),
    sa.Column('offset_range_high_unit', sa.String(), nullable=True),
    sa.Column('offset_range_high_system', sa.String(), nullable=True),
    sa.Column('offset_range_high_code', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['action_id'], ['plan_definition_action.id'], ),
    sa.ForeignKeyConstraint(['plan_definition_id'], ['plan_definition.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_action_related_action_action_id'), 'plan_definition_action_related_action', ['action_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_action_related_action_plan_definition_id'), 'plan_definition_action_related_action', ['plan_definition_id'], unique=False)
    op.create_table('plan_definition_action_trigger',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('plan_definition_id', sa.Integer(), nullable=False),
    sa.Column('action_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('type', postgresql.ENUM('named_event', 'periodic', 'data_changed', 'data_added', 'data_modified', 'data_removed', 'data_accessed', 'data_access_ended', name='plan_definition_trigger_type', create_type=False), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('timing_timing_event', sa.Text(), nullable=True),
    sa.Column('timing_timing_code_system', sa.String(), nullable=True),
    sa.Column('timing_timing_code_code', sa.String(), nullable=True),
    sa.Column('timing_timing_code_display', sa.String(), nullable=True),
    sa.Column('timing_timing_code_text', sa.String(), nullable=True),
    sa.Column('timing_timing_repeat_bounds_duration_value', sa.Float(), nullable=True),
    sa.Column('timing_timing_repeat_bounds_duration_comparator', sa.String(), nullable=True),
    sa.Column('timing_timing_repeat_bounds_duration_unit', sa.String(), nullable=True),
    sa.Column('timing_timing_repeat_bounds_duration_system', sa.String(), nullable=True),
    sa.Column('timing_timing_repeat_bounds_duration_code', sa.String(), nullable=True),
    sa.Column('timing_timing_repeat_bounds_range_low_value', sa.Float(), nullable=True),
    sa.Column('timing_timing_repeat_bounds_range_low_unit', sa.String(), nullable=True),
    sa.Column('timing_timing_repeat_bounds_range_low_system', sa.String(), nullable=True),
    sa.Column('timing_timing_repeat_bounds_range_low_code', sa.String(), nullable=True),
    sa.Column('timing_timing_repeat_bounds_range_high_value', sa.Float(), nullable=True),
    sa.Column('timing_timing_repeat_bounds_range_high_unit', sa.String(), nullable=True),
    sa.Column('timing_timing_repeat_bounds_range_high_system', sa.String(), nullable=True),
    sa.Column('timing_timing_repeat_bounds_range_high_code', sa.String(), nullable=True),
    sa.Column('timing_timing_repeat_bounds_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('timing_timing_repeat_bounds_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('timing_timing_repeat_count', sa.Integer(), nullable=True),
    sa.Column('timing_timing_repeat_count_max', sa.Integer(), nullable=True),
    sa.Column('timing_timing_repeat_duration', sa.Float(), nullable=True),
    sa.Column('timing_timing_repeat_duration_max', sa.Float(), nullable=True),
    sa.Column('timing_timing_repeat_duration_unit', sa.String(), nullable=True),
    sa.Column('timing_timing_repeat_frequency', sa.Integer(), nullable=True),
    sa.Column('timing_timing_repeat_frequency_max', sa.Integer(), nullable=True),
    sa.Column('timing_timing_repeat_period', sa.Float(), nullable=True),
    sa.Column('timing_timing_repeat_period_max', sa.Float(), nullable=True),
    sa.Column('timing_timing_repeat_period_unit', sa.String(), nullable=True),
    sa.Column('timing_timing_repeat_day_of_week', sa.Text(), nullable=True),
    sa.Column('timing_timing_repeat_time_of_day', sa.Text(), nullable=True),
    sa.Column('timing_timing_repeat_when', sa.Text(), nullable=True),
    sa.Column('timing_timing_repeat_offset', sa.Integer(), nullable=True),
    sa.Column('timing_reference_type', postgresql.ENUM('Schedule', name='plan_definition_schedule_ref_type', create_type=False), nullable=True),
    sa.Column('timing_reference_id', sa.Integer(), nullable=True),
    sa.Column('timing_reference_display', sa.String(), nullable=True),
    sa.Column('timing_date', sa.Date(), nullable=True),
    sa.Column('timing_datetime', sa.DateTime(timezone=True), nullable=True),
    sa.Column('condition_description', sa.String(), nullable=True),
    sa.Column('condition_name', sa.String(), nullable=True),
    sa.Column('condition_language', sa.String(), nullable=True),
    sa.Column('condition_expression', sa.Text(), nullable=True),
    sa.Column('condition_reference', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['action_id'], ['plan_definition_action.id'], ),
    sa.ForeignKeyConstraint(['plan_definition_id'], ['plan_definition.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_action_trigger_action_id'), 'plan_definition_action_trigger', ['action_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_action_trigger_plan_definition_id'), 'plan_definition_action_trigger', ['plan_definition_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_action_trigger_timing_reference_id'), 'plan_definition_action_trigger', ['timing_reference_id'], unique=False)
    op.create_table('plan_definition_contact_telecom',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('contact_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('system', sa.String(), nullable=True),
    sa.Column('value', sa.String(), nullable=True),
    sa.Column('use', sa.String(), nullable=True),
    sa.Column('rank', sa.Integer(), nullable=True),
    sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['contact_id'], ['plan_definition_contact.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_contact_telecom_contact_id'), 'plan_definition_contact_telecom', ['contact_id'], unique=False)
    op.create_table('plan_definition_goal_address',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('goal_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('coding_system', sa.String(), nullable=True),
    sa.Column('coding_code', sa.String(), nullable=True),
    sa.Column('coding_display', sa.String(), nullable=True),
    sa.Column('text', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['goal_id'], ['plan_definition_goal.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_goal_address_goal_id'), 'plan_definition_goal_address', ['goal_id'], unique=False)
    op.create_table('plan_definition_goal_target',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('goal_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('measure_system', sa.String(), nullable=True),
    sa.Column('measure_code', sa.String(), nullable=True),
    sa.Column('measure_display', sa.String(), nullable=True),
    sa.Column('measure_text', sa.String(), nullable=True),
    sa.Column('detail_quantity_value', sa.Float(), nullable=True),
    sa.Column('detail_quantity_comparator', sa.String(), nullable=True),
    sa.Column('detail_quantity_unit', sa.String(), nullable=True),
    sa.Column('detail_quantity_system', sa.String(), nullable=True),
    sa.Column('detail_quantity_code', sa.String(), nullable=True),
    sa.Column('detail_range_low_value', sa.Float(), nullable=True),
    sa.Column('detail_range_low_unit', sa.String(), nullable=True),
    sa.Column('detail_range_low_system', sa.String(), nullable=True),
    sa.Column('detail_range_low_code', sa.String(), nullable=True),
    sa.Column('detail_range_high_value', sa.Float(), nullable=True),
    sa.Column('detail_range_high_unit', sa.String(), nullable=True),
    sa.Column('detail_range_high_system', sa.String(), nullable=True),
    sa.Column('detail_range_high_code', sa.String(), nullable=True),
    sa.Column('detail_cc_system', sa.String(), nullable=True),
    sa.Column('detail_cc_code', sa.String(), nullable=True),
    sa.Column('detail_cc_display', sa.String(), nullable=True),
    sa.Column('detail_cc_text', sa.String(), nullable=True),
    sa.Column('due_value', sa.Float(), nullable=True),
    sa.Column('due_comparator', sa.String(), nullable=True),
    sa.Column('due_unit', sa.String(), nullable=True),
    sa.Column('due_system', sa.String(), nullable=True),
    sa.Column('due_code', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['goal_id'], ['plan_definition_goal.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_goal_target_goal_id'), 'plan_definition_goal_target', ['goal_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_goal_target_measure_code'), 'plan_definition_goal_target', ['measure_code'], unique=False)
    op.create_table('plan_definition_related_artifact',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('plan_definition_id', sa.Integer(), nullable=False),
    sa.Column('goal_id', sa.Integer(), nullable=True),
    sa.Column('action_id', sa.Integer(), nullable=True),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('scope', postgresql.ENUM('plan', 'goal', 'action', name='plan_definition_related_artifact_scope', create_type=False), nullable=False),
    sa.Column('type', postgresql.ENUM('documentation', 'justification', 'citation', 'predecessor', 'successor', 'derived_from', 'depends_on', 'composed_of', name='plan_definition_related_artifact_type', create_type=False), nullable=False),
    sa.Column('label', sa.String(), nullable=True),
    sa.Column('display', sa.String(), nullable=True),
    sa.Column('citation', sa.Text(), nullable=True),
    sa.Column('url', sa.String(), nullable=True),
    sa.Column('document_content_type', sa.String(), nullable=True),
    sa.Column('document_language', sa.String(), nullable=True),
    sa.Column('document_data', sa.Text(), nullable=True),
    sa.Column('document_url', sa.String(), nullable=True),
    sa.Column('document_size', sa.Integer(), nullable=True),
    sa.Column('document_hash', sa.String(), nullable=True),
    sa.Column('document_title', sa.String(), nullable=True),
    sa.Column('document_creation', sa.DateTime(timezone=True), nullable=True),
    sa.Column('resource', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['action_id'], ['plan_definition_action.id'], ),
    sa.ForeignKeyConstraint(['goal_id'], ['plan_definition_goal.id'], ),
    sa.ForeignKeyConstraint(['plan_definition_id'], ['plan_definition.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_related_artifact_action_id'), 'plan_definition_related_artifact', ['action_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_related_artifact_goal_id'), 'plan_definition_related_artifact', ['goal_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_related_artifact_plan_definition_id'), 'plan_definition_related_artifact', ['plan_definition_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_related_artifact_resource'), 'plan_definition_related_artifact', ['resource'], unique=False)
    op.create_index(op.f('ix_plan_definition_related_artifact_type'), 'plan_definition_related_artifact', ['type'], unique=False)
    op.create_table('plan_definition_data_requirement',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('plan_definition_id', sa.Integer(), nullable=False),
    sa.Column('action_id', sa.Integer(), nullable=True),
    sa.Column('trigger_id', sa.Integer(), nullable=True),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('role', postgresql.ENUM('input', 'output', 'trigger', name='plan_definition_dr_role', create_type=False), nullable=False),
    sa.Column('type', sa.String(), nullable=False),
    sa.Column('profile', sa.Text(), nullable=True),
    sa.Column('must_support', sa.Text(), nullable=True),
    sa.Column('limit', sa.Integer(), nullable=True),
    sa.Column('subject_cc_system', sa.String(), nullable=True),
    sa.Column('subject_cc_code', sa.String(), nullable=True),
    sa.Column('subject_cc_display', sa.String(), nullable=True),
    sa.Column('subject_cc_text', sa.String(), nullable=True),
    sa.Column('subject_reference_type', postgresql.ENUM('Group', name='plan_definition_group_ref_type', create_type=False), nullable=True),
    sa.Column('subject_reference_id', sa.Integer(), nullable=True),
    sa.Column('subject_reference_display', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['action_id'], ['plan_definition_action.id'], ),
    sa.ForeignKeyConstraint(['plan_definition_id'], ['plan_definition.id'], ),
    sa.ForeignKeyConstraint(['trigger_id'], ['plan_definition_action_trigger.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_data_requirement_action_id'), 'plan_definition_data_requirement', ['action_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_data_requirement_plan_definition_id'), 'plan_definition_data_requirement', ['plan_definition_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_data_requirement_subject_reference_id'), 'plan_definition_data_requirement', ['subject_reference_id'], unique=False)
    op.create_index(op.f('ix_plan_definition_data_requirement_trigger_id'), 'plan_definition_data_requirement', ['trigger_id'], unique=False)
    op.create_table('plan_definition_dr_code_filter',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('data_requirement_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('path', sa.String(), nullable=True),
    sa.Column('search_param', sa.String(), nullable=True),
    sa.Column('value_set', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['data_requirement_id'], ['plan_definition_data_requirement.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_dr_code_filter_data_requirement_id'), 'plan_definition_dr_code_filter', ['data_requirement_id'], unique=False)
    op.create_table('plan_definition_dr_date_filter',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('data_requirement_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('path', sa.String(), nullable=True),
    sa.Column('search_param', sa.String(), nullable=True),
    sa.Column('value_datetime', sa.DateTime(timezone=True), nullable=True),
    sa.Column('value_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('value_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('value_duration_value', sa.Float(), nullable=True),
    sa.Column('value_duration_comparator', sa.String(), nullable=True),
    sa.Column('value_duration_unit', sa.String(), nullable=True),
    sa.Column('value_duration_system', sa.String(), nullable=True),
    sa.Column('value_duration_code', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['data_requirement_id'], ['plan_definition_data_requirement.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_dr_date_filter_data_requirement_id'), 'plan_definition_dr_date_filter', ['data_requirement_id'], unique=False)
    op.create_table('plan_definition_dr_sort',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('data_requirement_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('path', sa.String(), nullable=False),
    sa.Column('direction', postgresql.ENUM('ascending', 'descending', name='plan_definition_sort_direction', create_type=False), nullable=False),
    sa.ForeignKeyConstraint(['data_requirement_id'], ['plan_definition_data_requirement.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_dr_sort_data_requirement_id'), 'plan_definition_dr_sort', ['data_requirement_id'], unique=False)
    op.create_table('plan_definition_dr_code_filter_code',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('code_filter_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('system', sa.String(), nullable=True),
    sa.Column('code', sa.String(), nullable=True),
    sa.Column('display', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['code_filter_id'], ['plan_definition_dr_code_filter.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_definition_dr_code_filter_code_code_filter_id'), 'plan_definition_dr_code_filter_code', ['code_filter_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_plan_definition_dr_code_filter_code_code_filter_id'), table_name='plan_definition_dr_code_filter_code')
    op.drop_table('plan_definition_dr_code_filter_code')
    op.drop_index(op.f('ix_plan_definition_dr_sort_data_requirement_id'), table_name='plan_definition_dr_sort')
    op.drop_table('plan_definition_dr_sort')
    op.drop_index(op.f('ix_plan_definition_dr_date_filter_data_requirement_id'), table_name='plan_definition_dr_date_filter')
    op.drop_table('plan_definition_dr_date_filter')
    op.drop_index(op.f('ix_plan_definition_dr_code_filter_data_requirement_id'), table_name='plan_definition_dr_code_filter')
    op.drop_table('plan_definition_dr_code_filter')
    op.drop_index(op.f('ix_plan_definition_data_requirement_trigger_id'), table_name='plan_definition_data_requirement')
    op.drop_index(op.f('ix_plan_definition_data_requirement_subject_reference_id'), table_name='plan_definition_data_requirement')
    op.drop_index(op.f('ix_plan_definition_data_requirement_plan_definition_id'), table_name='plan_definition_data_requirement')
    op.drop_index(op.f('ix_plan_definition_data_requirement_action_id'), table_name='plan_definition_data_requirement')
    op.drop_table('plan_definition_data_requirement')
    op.drop_index(op.f('ix_plan_definition_related_artifact_type'), table_name='plan_definition_related_artifact')
    op.drop_index(op.f('ix_plan_definition_related_artifact_resource'), table_name='plan_definition_related_artifact')
    op.drop_index(op.f('ix_plan_definition_related_artifact_plan_definition_id'), table_name='plan_definition_related_artifact')
    op.drop_index(op.f('ix_plan_definition_related_artifact_goal_id'), table_name='plan_definition_related_artifact')
    op.drop_index(op.f('ix_plan_definition_related_artifact_action_id'), table_name='plan_definition_related_artifact')
    op.drop_table('plan_definition_related_artifact')
    op.drop_index(op.f('ix_plan_definition_goal_target_measure_code'), table_name='plan_definition_goal_target')
    op.drop_index(op.f('ix_plan_definition_goal_target_goal_id'), table_name='plan_definition_goal_target')
    op.drop_table('plan_definition_goal_target')
    op.drop_index(op.f('ix_plan_definition_goal_address_goal_id'), table_name='plan_definition_goal_address')
    op.drop_table('plan_definition_goal_address')
    op.drop_index(op.f('ix_plan_definition_contact_telecom_contact_id'), table_name='plan_definition_contact_telecom')
    op.drop_table('plan_definition_contact_telecom')
    op.drop_index(op.f('ix_plan_definition_action_trigger_timing_reference_id'), table_name='plan_definition_action_trigger')
    op.drop_index(op.f('ix_plan_definition_action_trigger_plan_definition_id'), table_name='plan_definition_action_trigger')
    op.drop_index(op.f('ix_plan_definition_action_trigger_action_id'), table_name='plan_definition_action_trigger')
    op.drop_table('plan_definition_action_trigger')
    op.drop_index(op.f('ix_plan_definition_action_related_action_plan_definition_id'), table_name='plan_definition_action_related_action')
    op.drop_index(op.f('ix_plan_definition_action_related_action_action_id'), table_name='plan_definition_action_related_action')
    op.drop_table('plan_definition_action_related_action')
    op.drop_index(op.f('ix_plan_definition_action_participant_plan_definition_id'), table_name='plan_definition_action_participant')
    op.drop_index(op.f('ix_plan_definition_action_participant_action_id'), table_name='plan_definition_action_participant')
    op.drop_table('plan_definition_action_participant')
    op.drop_index(op.f('ix_plan_definition_action_goal_id_plan_definition_id'), table_name='plan_definition_action_goal_id')
    op.drop_index(op.f('ix_plan_definition_action_goal_id_action_id'), table_name='plan_definition_action_goal_id')
    op.drop_table('plan_definition_action_goal_id')
    op.drop_index(op.f('ix_plan_definition_action_dynamic_value_plan_definition_id'), table_name='plan_definition_action_dynamic_value')
    op.drop_index(op.f('ix_plan_definition_action_dynamic_value_action_id'), table_name='plan_definition_action_dynamic_value')
    op.drop_table('plan_definition_action_dynamic_value')
    op.drop_index(op.f('ix_plan_definition_action_condition_plan_definition_id'), table_name='plan_definition_action_condition')
    op.drop_index(op.f('ix_plan_definition_action_condition_action_id'), table_name='plan_definition_action_condition')
    op.drop_table('plan_definition_action_condition')
    op.drop_index(op.f('ix_plan_definition_action_code_plan_definition_id'), table_name='plan_definition_action_code')
    op.drop_index(op.f('ix_plan_definition_action_code_kind'), table_name='plan_definition_action_code')
    op.drop_index(op.f('ix_plan_definition_action_code_coding_code'), table_name='plan_definition_action_code')
    op.drop_index(op.f('ix_plan_definition_action_code_action_id'), table_name='plan_definition_action_code')
    op.drop_table('plan_definition_action_code')
    op.drop_index(op.f('ix_plan_definition_use_context_value_reference_id'), table_name='plan_definition_use_context')
    op.drop_index(op.f('ix_plan_definition_use_context_plan_definition_id'), table_name='plan_definition_use_context')
    op.drop_table('plan_definition_use_context')
    op.drop_index(op.f('ix_plan_definition_topic_plan_definition_id'), table_name='plan_definition_topic')
    op.drop_index(op.f('ix_plan_definition_topic_coding_code'), table_name='plan_definition_topic')
    op.drop_table('plan_definition_topic')
    op.drop_index(op.f('ix_plan_definition_library_plan_definition_id'), table_name='plan_definition_library')
    op.drop_index(op.f('ix_plan_definition_library_canonical'), table_name='plan_definition_library')
    op.drop_table('plan_definition_library')
    op.drop_index(op.f('ix_plan_definition_jurisdiction_plan_definition_id'), table_name='plan_definition_jurisdiction')
    op.drop_index(op.f('ix_plan_definition_jurisdiction_coding_code'), table_name='plan_definition_jurisdiction')
    op.drop_table('plan_definition_jurisdiction')
    op.drop_index(op.f('ix_plan_definition_identifier_plan_definition_id'), table_name='plan_definition_identifier')
    op.drop_table('plan_definition_identifier')
    op.drop_index(op.f('ix_plan_definition_goal_plan_definition_id'), table_name='plan_definition_goal')
    op.drop_index(op.f('ix_plan_definition_goal_element_id'), table_name='plan_definition_goal')
    op.drop_index(op.f('ix_plan_definition_goal_description_code'), table_name='plan_definition_goal')
    op.drop_table('plan_definition_goal')
    op.drop_index(op.f('ix_plan_definition_contact_plan_definition_id'), table_name='plan_definition_contact')
    op.drop_index(op.f('ix_plan_definition_contact_kind'), table_name='plan_definition_contact')
    op.drop_table('plan_definition_contact')
    op.drop_index(op.f('ix_plan_definition_action_type_code'), table_name='plan_definition_action')
    op.drop_index(op.f('ix_plan_definition_action_subject_reference_id'), table_name='plan_definition_action')
    op.drop_index(op.f('ix_plan_definition_action_plan_definition_id'), table_name='plan_definition_action')
    op.drop_index(op.f('ix_plan_definition_action_parent_action_id'), table_name='plan_definition_action')
    op.drop_index(op.f('ix_plan_definition_action_id'), table_name='plan_definition_action')
    op.drop_index(op.f('ix_plan_definition_action_element_id'), table_name='plan_definition_action')
    op.drop_index(op.f('ix_plan_definition_action_definition_uri'), table_name='plan_definition_action')
    op.drop_index(op.f('ix_plan_definition_action_definition_canonical'), table_name='plan_definition_action')
    op.drop_table('plan_definition_action')
    op.drop_index(op.f('ix_plan_definition_version'), table_name='plan_definition')
    op.drop_index(op.f('ix_plan_definition_user_id'), table_name='plan_definition')
    op.drop_index(op.f('ix_plan_definition_url'), table_name='plan_definition')
    op.drop_index(op.f('ix_plan_definition_type_code'), table_name='plan_definition')
    op.drop_index(op.f('ix_plan_definition_subject_reference_id'), table_name='plan_definition')
    op.drop_index(op.f('ix_plan_definition_status'), table_name='plan_definition')
    op.drop_index(op.f('ix_plan_definition_plan_definition_id'), table_name='plan_definition')
    op.drop_index(op.f('ix_plan_definition_org_id'), table_name='plan_definition')
    op.drop_index(op.f('ix_plan_definition_name'), table_name='plan_definition')
    op.drop_index(op.f('ix_plan_definition_id'), table_name='plan_definition')
    op.drop_index(op.f('ix_plan_definition_date'), table_name='plan_definition')
    op.drop_table('plan_definition')
    op.execute('DROP SEQUENCE IF EXISTS plan_definition_pub_seq')
    # ### end Alembic commands ###
    postgresql.ENUM(name='plan_definition_status').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='plan_definition_group_ref_type').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='plan_definition_action_priority').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='plan_definition_grouping_behavior').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='plan_definition_selection_behavior').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='plan_definition_required_behavior').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='plan_definition_precheck_behavior').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='plan_definition_cardinality_behavior').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='plan_definition_contact_kind').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='plan_definition_use_context_ref_type').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='plan_definition_condition_kind').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='plan_definition_participant_type').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='plan_definition_relationship_type').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='plan_definition_trigger_type').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='plan_definition_schedule_ref_type').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='plan_definition_related_artifact_scope').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='plan_definition_related_artifact_type').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='plan_definition_dr_role').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='plan_definition_sort_direction').drop(op.get_bind(), checkfirst=True)
