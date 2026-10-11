"""add activity_definition

Revision ID: b1b9407f726c
Revises: 935bb132edbd
Create Date: 2026-10-10 20:54:22.697016

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b1b9407f726c'
down_revision: Union[str, None] = '935bb132edbd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    postgresql.ENUM('draft', 'active', 'retired', 'unknown', name='activity_definition_status').create(op.get_bind(), checkfirst=True)
    postgresql.ENUM('Group', name='activity_definition_group_ref_type').create(op.get_bind(), checkfirst=True)
    postgresql.ENUM('Appointment', 'AppointmentResponse', 'CarePlan', 'Claim', 'CommunicationRequest', 'Contract', 'DeviceRequest', 'EnrollmentRequest', 'ImmunizationRecommendation', 'MedicationRequest', 'NutritionOrder', 'ServiceRequest', 'SupplyRequest', 'Task', 'VisionPrescription', name='activity_definition_kind').create(op.get_bind(), checkfirst=True)
    postgresql.ENUM('proposal', 'plan', 'directive', 'order', 'original_order', 'reflex_order', 'filler_order', 'instance_order', 'option', name='activity_definition_intent').create(op.get_bind(), checkfirst=True)
    postgresql.ENUM('routine', 'urgent', 'asap', 'stat', name='activity_definition_priority').create(op.get_bind(), checkfirst=True)
    postgresql.ENUM('Location', name='activity_definition_location_ref_type').create(op.get_bind(), checkfirst=True)
    postgresql.ENUM('Medication', 'Substance', name='activity_definition_product_ref_type').create(op.get_bind(), checkfirst=True)
    postgresql.ENUM('contact', 'author', 'editor', 'reviewer', 'endorser', name='activity_definition_contact_kind').create(op.get_bind(), checkfirst=True)
    postgresql.ENUM('ObservationDefinition', name='activity_definition_observation_ref_type').create(op.get_bind(), checkfirst=True)
    postgresql.ENUM('patient', 'practitioner', 'related_person', 'device', name='activity_definition_participant_type').create(op.get_bind(), checkfirst=True)
    postgresql.ENUM('documentation', 'justification', 'citation', 'predecessor', 'successor', 'derived_from', 'depends_on', 'composed_of', name='activity_definition_related_artifact_type').create(op.get_bind(), checkfirst=True)
    postgresql.ENUM('SpecimenDefinition', name='activity_definition_specimen_ref_type').create(op.get_bind(), checkfirst=True)
    postgresql.ENUM('PlanDefinition', 'ResearchStudy', 'InsurancePlan', 'HealthcareService', 'Group', 'Location', 'Organization', name='activity_definition_use_context_ref_type').create(op.get_bind(), checkfirst=True)
    op.execute('CREATE SEQUENCE IF NOT EXISTS activity_definition_pub_seq START 410000 INCREMENT 1')
    op.create_table('activity_definition',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('activity_definition_id', sa.Integer(), server_default=sa.text("nextval('activity_definition_pub_seq')"), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('url', sa.String(), nullable=True),
    sa.Column('version', sa.String(), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('title', sa.String(), nullable=True),
    sa.Column('subtitle', sa.String(), nullable=True),
    sa.Column('status', postgresql.ENUM('draft', 'active', 'retired', 'unknown', name='activity_definition_status', create_type=False), nullable=False),
    sa.Column('experimental', sa.Boolean(), nullable=True),
    sa.Column('date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('publisher', sa.String(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('purpose', sa.Text(), nullable=True),
    sa.Column('usage', sa.Text(), nullable=True),
    sa.Column('copyright', sa.Text(), nullable=True),
    sa.Column('approval_date', sa.Date(), nullable=True),
    sa.Column('last_review_date', sa.Date(), nullable=True),
    sa.Column('subject_cc_system', sa.String(), nullable=True),
    sa.Column('subject_cc_code', sa.String(), nullable=True),
    sa.Column('subject_cc_display', sa.String(), nullable=True),
    sa.Column('subject_cc_text', sa.String(), nullable=True),
    sa.Column('subject_reference_type', postgresql.ENUM('Group', name='activity_definition_group_ref_type', create_type=False), nullable=True),
    sa.Column('subject_reference_id', sa.Integer(), nullable=True),
    sa.Column('subject_reference_display', sa.String(), nullable=True),
    sa.Column('effective_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('effective_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('kind', postgresql.ENUM('Appointment', 'AppointmentResponse', 'CarePlan', 'Claim', 'CommunicationRequest', 'Contract', 'DeviceRequest', 'EnrollmentRequest', 'ImmunizationRecommendation', 'MedicationRequest', 'NutritionOrder', 'ServiceRequest', 'SupplyRequest', 'Task', 'VisionPrescription', name='activity_definition_kind', create_type=False), nullable=True),
    sa.Column('profile', sa.String(), nullable=True),
    sa.Column('code_system', sa.String(), nullable=True),
    sa.Column('code_code', sa.String(), nullable=True),
    sa.Column('code_display', sa.String(), nullable=True),
    sa.Column('code_text', sa.String(), nullable=True),
    sa.Column('intent', postgresql.ENUM('proposal', 'plan', 'directive', 'order', 'original_order', 'reflex_order', 'filler_order', 'instance_order', 'option', name='activity_definition_intent', create_type=False), nullable=True),
    sa.Column('priority', postgresql.ENUM('routine', 'urgent', 'asap', 'stat', name='activity_definition_priority', create_type=False), nullable=True),
    sa.Column('do_not_perform', sa.Boolean(), nullable=True),
    sa.Column('timing_datetime', sa.DateTime(timezone=True), nullable=True),
    sa.Column('timing_age_value', sa.Float(), nullable=True),
    sa.Column('timing_age_comparator', sa.String(), nullable=True),
    sa.Column('timing_age_unit', sa.String(), nullable=True),
    sa.Column('timing_age_system', sa.String(), nullable=True),
    sa.Column('timing_age_code', sa.String(), nullable=True),
    sa.Column('timing_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('timing_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('timing_range_low_value', sa.Float(), nullable=True),
    sa.Column('timing_range_low_unit', sa.String(), nullable=True),
    sa.Column('timing_range_low_system', sa.String(), nullable=True),
    sa.Column('timing_range_low_code', sa.String(), nullable=True),
    sa.Column('timing_range_high_value', sa.Float(), nullable=True),
    sa.Column('timing_range_high_unit', sa.String(), nullable=True),
    sa.Column('timing_range_high_system', sa.String(), nullable=True),
    sa.Column('timing_range_high_code', sa.String(), nullable=True),
    sa.Column('timing_duration_value', sa.Float(), nullable=True),
    sa.Column('timing_duration_comparator', sa.String(), nullable=True),
    sa.Column('timing_duration_unit', sa.String(), nullable=True),
    sa.Column('timing_duration_system', sa.String(), nullable=True),
    sa.Column('timing_duration_code', sa.String(), nullable=True),
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
    sa.Column('location_type', postgresql.ENUM('Location', name='activity_definition_location_ref_type', create_type=False), nullable=True),
    sa.Column('location_id', sa.Integer(), nullable=True),
    sa.Column('location_display', sa.String(), nullable=True),
    sa.Column('product_reference_type', postgresql.ENUM('Medication', 'Substance', name='activity_definition_product_ref_type', create_type=False), nullable=True),
    sa.Column('product_reference_id', sa.Integer(), nullable=True),
    sa.Column('product_reference_display', sa.String(), nullable=True),
    sa.Column('product_cc_system', sa.String(), nullable=True),
    sa.Column('product_cc_code', sa.String(), nullable=True),
    sa.Column('product_cc_display', sa.String(), nullable=True),
    sa.Column('product_cc_text', sa.String(), nullable=True),
    sa.Column('quantity_value', sa.Float(), nullable=True),
    sa.Column('quantity_unit', sa.String(), nullable=True),
    sa.Column('quantity_system', sa.String(), nullable=True),
    sa.Column('quantity_code', sa.String(), nullable=True),
    sa.Column('transform', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_by', sa.String(), nullable=True),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_activity_definition_id'), 'activity_definition', ['activity_definition_id'], unique=True)
    op.create_index(op.f('ix_activity_definition_code_code'), 'activity_definition', ['code_code'], unique=False)
    op.create_index(op.f('ix_activity_definition_date'), 'activity_definition', ['date'], unique=False)
    op.create_index(op.f('ix_activity_definition_id'), 'activity_definition', ['id'], unique=False)
    op.create_index(op.f('ix_activity_definition_intent'), 'activity_definition', ['intent'], unique=False)
    op.create_index(op.f('ix_activity_definition_kind'), 'activity_definition', ['kind'], unique=False)
    op.create_index(op.f('ix_activity_definition_location_id'), 'activity_definition', ['location_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_name'), 'activity_definition', ['name'], unique=False)
    op.create_index(op.f('ix_activity_definition_org_id'), 'activity_definition', ['org_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_product_reference_id'), 'activity_definition', ['product_reference_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_status'), 'activity_definition', ['status'], unique=False)
    op.create_index(op.f('ix_activity_definition_subject_reference_id'), 'activity_definition', ['subject_reference_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_url'), 'activity_definition', ['url'], unique=False)
    op.create_index(op.f('ix_activity_definition_user_id'), 'activity_definition', ['user_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_version'), 'activity_definition', ['version'], unique=False)
    op.create_table('activity_definition_body_site',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('activity_definition_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('coding_system', sa.String(), nullable=True),
    sa.Column('coding_code', sa.String(), nullable=True),
    sa.Column('coding_display', sa.String(), nullable=True),
    sa.Column('text', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['activity_definition_id'], ['activity_definition.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_body_site_activity_definition_id'), 'activity_definition_body_site', ['activity_definition_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_body_site_coding_code'), 'activity_definition_body_site', ['coding_code'], unique=False)
    op.create_table('activity_definition_contact',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('activity_definition_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('kind', postgresql.ENUM('contact', 'author', 'editor', 'reviewer', 'endorser', name='activity_definition_contact_kind', create_type=False), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['activity_definition_id'], ['activity_definition.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_contact_activity_definition_id'), 'activity_definition_contact', ['activity_definition_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_contact_kind'), 'activity_definition_contact', ['kind'], unique=False)
    op.create_table('activity_definition_dosage',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('activity_definition_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('sequence', sa.Integer(), nullable=True),
    sa.Column('text', sa.Text(), nullable=True),
    sa.Column('patient_instruction', sa.Text(), nullable=True),
    sa.Column('timing_event', sa.Text(), nullable=True),
    sa.Column('timing_code_system', sa.String(), nullable=True),
    sa.Column('timing_code_code', sa.String(), nullable=True),
    sa.Column('timing_code_display', sa.String(), nullable=True),
    sa.Column('timing_code_text', sa.String(), nullable=True),
    sa.Column('timing_repeat_bounds_duration_value', sa.Float(), nullable=True),
    sa.Column('timing_repeat_bounds_duration_comparator', sa.String(), nullable=True),
    sa.Column('timing_repeat_bounds_duration_unit', sa.String(), nullable=True),
    sa.Column('timing_repeat_bounds_duration_system', sa.String(), nullable=True),
    sa.Column('timing_repeat_bounds_duration_code', sa.String(), nullable=True),
    sa.Column('timing_repeat_bounds_range_low_value', sa.Float(), nullable=True),
    sa.Column('timing_repeat_bounds_range_low_unit', sa.String(), nullable=True),
    sa.Column('timing_repeat_bounds_range_low_system', sa.String(), nullable=True),
    sa.Column('timing_repeat_bounds_range_low_code', sa.String(), nullable=True),
    sa.Column('timing_repeat_bounds_range_high_value', sa.Float(), nullable=True),
    sa.Column('timing_repeat_bounds_range_high_unit', sa.String(), nullable=True),
    sa.Column('timing_repeat_bounds_range_high_system', sa.String(), nullable=True),
    sa.Column('timing_repeat_bounds_range_high_code', sa.String(), nullable=True),
    sa.Column('timing_repeat_bounds_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('timing_repeat_bounds_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('timing_repeat_count', sa.Integer(), nullable=True),
    sa.Column('timing_repeat_count_max', sa.Integer(), nullable=True),
    sa.Column('timing_repeat_duration', sa.Float(), nullable=True),
    sa.Column('timing_repeat_duration_max', sa.Float(), nullable=True),
    sa.Column('timing_repeat_duration_unit', sa.String(), nullable=True),
    sa.Column('timing_repeat_frequency', sa.Integer(), nullable=True),
    sa.Column('timing_repeat_frequency_max', sa.Integer(), nullable=True),
    sa.Column('timing_repeat_period', sa.Float(), nullable=True),
    sa.Column('timing_repeat_period_max', sa.Float(), nullable=True),
    sa.Column('timing_repeat_period_unit', sa.String(), nullable=True),
    sa.Column('timing_repeat_day_of_week', sa.Text(), nullable=True),
    sa.Column('timing_repeat_time_of_day', sa.Text(), nullable=True),
    sa.Column('timing_repeat_when', sa.Text(), nullable=True),
    sa.Column('timing_repeat_offset', sa.Integer(), nullable=True),
    sa.Column('as_needed_boolean', sa.Boolean(), nullable=True),
    sa.Column('as_needed_system', sa.String(), nullable=True),
    sa.Column('as_needed_code', sa.String(), nullable=True),
    sa.Column('as_needed_display', sa.String(), nullable=True),
    sa.Column('as_needed_text', sa.String(), nullable=True),
    sa.Column('site_system', sa.String(), nullable=True),
    sa.Column('site_code', sa.String(), nullable=True),
    sa.Column('site_display', sa.String(), nullable=True),
    sa.Column('site_text', sa.String(), nullable=True),
    sa.Column('route_system', sa.String(), nullable=True),
    sa.Column('route_code', sa.String(), nullable=True),
    sa.Column('route_display', sa.String(), nullable=True),
    sa.Column('route_text', sa.String(), nullable=True),
    sa.Column('method_system', sa.String(), nullable=True),
    sa.Column('method_code', sa.String(), nullable=True),
    sa.Column('method_display', sa.String(), nullable=True),
    sa.Column('method_text', sa.String(), nullable=True),
    sa.Column('max_dose_per_period_numerator_value', sa.Float(), nullable=True),
    sa.Column('max_dose_per_period_numerator_comparator', sa.String(), nullable=True),
    sa.Column('max_dose_per_period_numerator_unit', sa.String(), nullable=True),
    sa.Column('max_dose_per_period_numerator_system', sa.String(), nullable=True),
    sa.Column('max_dose_per_period_numerator_code', sa.String(), nullable=True),
    sa.Column('max_dose_per_period_denominator_value', sa.Float(), nullable=True),
    sa.Column('max_dose_per_period_denominator_comparator', sa.String(), nullable=True),
    sa.Column('max_dose_per_period_denominator_unit', sa.String(), nullable=True),
    sa.Column('max_dose_per_period_denominator_system', sa.String(), nullable=True),
    sa.Column('max_dose_per_period_denominator_code', sa.String(), nullable=True),
    sa.Column('max_dose_per_administration_value', sa.Float(), nullable=True),
    sa.Column('max_dose_per_administration_unit', sa.String(), nullable=True),
    sa.Column('max_dose_per_administration_system', sa.String(), nullable=True),
    sa.Column('max_dose_per_administration_code', sa.String(), nullable=True),
    sa.Column('max_dose_per_lifetime_value', sa.Float(), nullable=True),
    sa.Column('max_dose_per_lifetime_unit', sa.String(), nullable=True),
    sa.Column('max_dose_per_lifetime_system', sa.String(), nullable=True),
    sa.Column('max_dose_per_lifetime_code', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['activity_definition_id'], ['activity_definition.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_dosage_activity_definition_id'), 'activity_definition_dosage', ['activity_definition_id'], unique=False)
    op.create_table('activity_definition_dynamic_value',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('activity_definition_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('path', sa.String(), nullable=True),
    sa.Column('expression_description', sa.String(), nullable=True),
    sa.Column('expression_name', sa.String(), nullable=True),
    sa.Column('expression_language', sa.String(), nullable=True),
    sa.Column('expression_expression', sa.Text(), nullable=True),
    sa.Column('expression_reference', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['activity_definition_id'], ['activity_definition.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_dynamic_value_activity_definition_id'), 'activity_definition_dynamic_value', ['activity_definition_id'], unique=False)
    op.create_table('activity_definition_identifier',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('activity_definition_id', sa.Integer(), nullable=False),
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
    sa.ForeignKeyConstraint(['activity_definition_id'], ['activity_definition.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_identifier_activity_definition_id'), 'activity_definition_identifier', ['activity_definition_id'], unique=False)
    op.create_table('activity_definition_jurisdiction',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('activity_definition_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('coding_system', sa.String(), nullable=True),
    sa.Column('coding_code', sa.String(), nullable=True),
    sa.Column('coding_display', sa.String(), nullable=True),
    sa.Column('text', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['activity_definition_id'], ['activity_definition.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_jurisdiction_activity_definition_id'), 'activity_definition_jurisdiction', ['activity_definition_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_jurisdiction_coding_code'), 'activity_definition_jurisdiction', ['coding_code'], unique=False)
    op.create_table('activity_definition_library',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('activity_definition_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('canonical', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['activity_definition_id'], ['activity_definition.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_library_activity_definition_id'), 'activity_definition_library', ['activity_definition_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_library_canonical'), 'activity_definition_library', ['canonical'], unique=False)
    op.create_table('activity_definition_observation_requirement',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('activity_definition_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('reference_type', postgresql.ENUM('ObservationDefinition', name='activity_definition_observation_ref_type', create_type=False), nullable=True),
    sa.Column('reference_id', sa.Integer(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['activity_definition_id'], ['activity_definition.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_observation_requirement_activity_definition_id'), 'activity_definition_observation_requirement', ['activity_definition_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_observation_requirement_reference_id'), 'activity_definition_observation_requirement', ['reference_id'], unique=False)
    op.create_table('activity_definition_observation_result_requirement',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('activity_definition_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('reference_type', postgresql.ENUM('ObservationDefinition', name='activity_definition_observation_ref_type', create_type=False), nullable=True),
    sa.Column('reference_id', sa.Integer(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['activity_definition_id'], ['activity_definition.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_observation_result_requirement_activity_definition_id'), 'activity_definition_observation_result_requirement', ['activity_definition_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_observation_result_requirement_reference_id'), 'activity_definition_observation_result_requirement', ['reference_id'], unique=False)
    op.create_table('activity_definition_participant',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('activity_definition_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('type', postgresql.ENUM('patient', 'practitioner', 'related_person', 'device', name='activity_definition_participant_type', create_type=False), nullable=False),
    sa.Column('role_system', sa.String(), nullable=True),
    sa.Column('role_code', sa.String(), nullable=True),
    sa.Column('role_display', sa.String(), nullable=True),
    sa.Column('role_text', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['activity_definition_id'], ['activity_definition.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_participant_activity_definition_id'), 'activity_definition_participant', ['activity_definition_id'], unique=False)
    op.create_table('activity_definition_related_artifact',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('activity_definition_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('type', postgresql.ENUM('documentation', 'justification', 'citation', 'predecessor', 'successor', 'derived_from', 'depends_on', 'composed_of', name='activity_definition_related_artifact_type', create_type=False), nullable=False),
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
    sa.ForeignKeyConstraint(['activity_definition_id'], ['activity_definition.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_related_artifact_activity_definition_id'), 'activity_definition_related_artifact', ['activity_definition_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_related_artifact_resource'), 'activity_definition_related_artifact', ['resource'], unique=False)
    op.create_index(op.f('ix_activity_definition_related_artifact_type'), 'activity_definition_related_artifact', ['type'], unique=False)
    op.create_table('activity_definition_specimen_requirement',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('activity_definition_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('reference_type', postgresql.ENUM('SpecimenDefinition', name='activity_definition_specimen_ref_type', create_type=False), nullable=True),
    sa.Column('reference_id', sa.Integer(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['activity_definition_id'], ['activity_definition.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_specimen_requirement_activity_definition_id'), 'activity_definition_specimen_requirement', ['activity_definition_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_specimen_requirement_reference_id'), 'activity_definition_specimen_requirement', ['reference_id'], unique=False)
    op.create_table('activity_definition_topic',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('activity_definition_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('coding_system', sa.String(), nullable=True),
    sa.Column('coding_code', sa.String(), nullable=True),
    sa.Column('coding_display', sa.String(), nullable=True),
    sa.Column('text', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['activity_definition_id'], ['activity_definition.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_topic_activity_definition_id'), 'activity_definition_topic', ['activity_definition_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_topic_coding_code'), 'activity_definition_topic', ['coding_code'], unique=False)
    op.create_table('activity_definition_use_context',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('activity_definition_id', sa.Integer(), nullable=False),
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
    sa.Column('value_reference_type', postgresql.ENUM('PlanDefinition', 'ResearchStudy', 'InsurancePlan', 'HealthcareService', 'Group', 'Location', 'Organization', name='activity_definition_use_context_ref_type', create_type=False), nullable=True),
    sa.Column('value_reference_id', sa.Integer(), nullable=True),
    sa.Column('value_reference_display', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['activity_definition_id'], ['activity_definition.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_use_context_activity_definition_id'), 'activity_definition_use_context', ['activity_definition_id'], unique=False)
    op.create_index(op.f('ix_activity_definition_use_context_value_reference_id'), 'activity_definition_use_context', ['value_reference_id'], unique=False)
    op.create_table('activity_definition_contact_telecom',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('contact_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('system', sa.String(), nullable=True),
    sa.Column('value', sa.String(), nullable=True),
    sa.Column('use', sa.String(), nullable=True),
    sa.Column('rank', sa.Integer(), nullable=True),
    sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['contact_id'], ['activity_definition_contact.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_contact_telecom_contact_id'), 'activity_definition_contact_telecom', ['contact_id'], unique=False)
    op.create_table('activity_definition_dosage_additional_instruction',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('dosage_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('coding_system', sa.String(), nullable=True),
    sa.Column('coding_code', sa.String(), nullable=True),
    sa.Column('coding_display', sa.String(), nullable=True),
    sa.Column('text', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['dosage_id'], ['activity_definition_dosage.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_dosage_additional_instruction_dosage_id'), 'activity_definition_dosage_additional_instruction', ['dosage_id'], unique=False)
    op.create_table('activity_definition_dosage_dose_and_rate',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('dosage_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('type_system', sa.String(), nullable=True),
    sa.Column('type_code', sa.String(), nullable=True),
    sa.Column('type_display', sa.String(), nullable=True),
    sa.Column('type_text', sa.String(), nullable=True),
    sa.Column('dose_range_low_value', sa.Float(), nullable=True),
    sa.Column('dose_range_low_unit', sa.String(), nullable=True),
    sa.Column('dose_range_low_system', sa.String(), nullable=True),
    sa.Column('dose_range_low_code', sa.String(), nullable=True),
    sa.Column('dose_range_high_value', sa.Float(), nullable=True),
    sa.Column('dose_range_high_unit', sa.String(), nullable=True),
    sa.Column('dose_range_high_system', sa.String(), nullable=True),
    sa.Column('dose_range_high_code', sa.String(), nullable=True),
    sa.Column('dose_quantity_value', sa.Float(), nullable=True),
    sa.Column('dose_quantity_unit', sa.String(), nullable=True),
    sa.Column('dose_quantity_system', sa.String(), nullable=True),
    sa.Column('dose_quantity_code', sa.String(), nullable=True),
    sa.Column('rate_ratio_numerator_value', sa.Float(), nullable=True),
    sa.Column('rate_ratio_numerator_comparator', sa.String(), nullable=True),
    sa.Column('rate_ratio_numerator_unit', sa.String(), nullable=True),
    sa.Column('rate_ratio_numerator_system', sa.String(), nullable=True),
    sa.Column('rate_ratio_numerator_code', sa.String(), nullable=True),
    sa.Column('rate_ratio_denominator_value', sa.Float(), nullable=True),
    sa.Column('rate_ratio_denominator_comparator', sa.String(), nullable=True),
    sa.Column('rate_ratio_denominator_unit', sa.String(), nullable=True),
    sa.Column('rate_ratio_denominator_system', sa.String(), nullable=True),
    sa.Column('rate_ratio_denominator_code', sa.String(), nullable=True),
    sa.Column('rate_range_low_value', sa.Float(), nullable=True),
    sa.Column('rate_range_low_unit', sa.String(), nullable=True),
    sa.Column('rate_range_low_system', sa.String(), nullable=True),
    sa.Column('rate_range_low_code', sa.String(), nullable=True),
    sa.Column('rate_range_high_value', sa.Float(), nullable=True),
    sa.Column('rate_range_high_unit', sa.String(), nullable=True),
    sa.Column('rate_range_high_system', sa.String(), nullable=True),
    sa.Column('rate_range_high_code', sa.String(), nullable=True),
    sa.Column('rate_quantity_value', sa.Float(), nullable=True),
    sa.Column('rate_quantity_unit', sa.String(), nullable=True),
    sa.Column('rate_quantity_system', sa.String(), nullable=True),
    sa.Column('rate_quantity_code', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['dosage_id'], ['activity_definition_dosage.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_definition_dosage_dose_and_rate_dosage_id'), 'activity_definition_dosage_dose_and_rate', ['dosage_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_activity_definition_dosage_dose_and_rate_dosage_id'), table_name='activity_definition_dosage_dose_and_rate')
    op.drop_table('activity_definition_dosage_dose_and_rate')
    op.drop_index(op.f('ix_activity_definition_dosage_additional_instruction_dosage_id'), table_name='activity_definition_dosage_additional_instruction')
    op.drop_table('activity_definition_dosage_additional_instruction')
    op.drop_index(op.f('ix_activity_definition_contact_telecom_contact_id'), table_name='activity_definition_contact_telecom')
    op.drop_table('activity_definition_contact_telecom')
    op.drop_index(op.f('ix_activity_definition_use_context_value_reference_id'), table_name='activity_definition_use_context')
    op.drop_index(op.f('ix_activity_definition_use_context_activity_definition_id'), table_name='activity_definition_use_context')
    op.drop_table('activity_definition_use_context')
    op.drop_index(op.f('ix_activity_definition_topic_coding_code'), table_name='activity_definition_topic')
    op.drop_index(op.f('ix_activity_definition_topic_activity_definition_id'), table_name='activity_definition_topic')
    op.drop_table('activity_definition_topic')
    op.drop_index(op.f('ix_activity_definition_specimen_requirement_reference_id'), table_name='activity_definition_specimen_requirement')
    op.drop_index(op.f('ix_activity_definition_specimen_requirement_activity_definition_id'), table_name='activity_definition_specimen_requirement')
    op.drop_table('activity_definition_specimen_requirement')
    op.drop_index(op.f('ix_activity_definition_related_artifact_type'), table_name='activity_definition_related_artifact')
    op.drop_index(op.f('ix_activity_definition_related_artifact_resource'), table_name='activity_definition_related_artifact')
    op.drop_index(op.f('ix_activity_definition_related_artifact_activity_definition_id'), table_name='activity_definition_related_artifact')
    op.drop_table('activity_definition_related_artifact')
    op.drop_index(op.f('ix_activity_definition_participant_activity_definition_id'), table_name='activity_definition_participant')
    op.drop_table('activity_definition_participant')
    op.drop_index(op.f('ix_activity_definition_observation_result_requirement_reference_id'), table_name='activity_definition_observation_result_requirement')
    op.drop_index(op.f('ix_activity_definition_observation_result_requirement_activity_definition_id'), table_name='activity_definition_observation_result_requirement')
    op.drop_table('activity_definition_observation_result_requirement')
    op.drop_index(op.f('ix_activity_definition_observation_requirement_reference_id'), table_name='activity_definition_observation_requirement')
    op.drop_index(op.f('ix_activity_definition_observation_requirement_activity_definition_id'), table_name='activity_definition_observation_requirement')
    op.drop_table('activity_definition_observation_requirement')
    op.drop_index(op.f('ix_activity_definition_library_canonical'), table_name='activity_definition_library')
    op.drop_index(op.f('ix_activity_definition_library_activity_definition_id'), table_name='activity_definition_library')
    op.drop_table('activity_definition_library')
    op.drop_index(op.f('ix_activity_definition_jurisdiction_coding_code'), table_name='activity_definition_jurisdiction')
    op.drop_index(op.f('ix_activity_definition_jurisdiction_activity_definition_id'), table_name='activity_definition_jurisdiction')
    op.drop_table('activity_definition_jurisdiction')
    op.drop_index(op.f('ix_activity_definition_identifier_activity_definition_id'), table_name='activity_definition_identifier')
    op.drop_table('activity_definition_identifier')
    op.drop_index(op.f('ix_activity_definition_dynamic_value_activity_definition_id'), table_name='activity_definition_dynamic_value')
    op.drop_table('activity_definition_dynamic_value')
    op.drop_index(op.f('ix_activity_definition_dosage_activity_definition_id'), table_name='activity_definition_dosage')
    op.drop_table('activity_definition_dosage')
    op.drop_index(op.f('ix_activity_definition_contact_kind'), table_name='activity_definition_contact')
    op.drop_index(op.f('ix_activity_definition_contact_activity_definition_id'), table_name='activity_definition_contact')
    op.drop_table('activity_definition_contact')
    op.drop_index(op.f('ix_activity_definition_body_site_coding_code'), table_name='activity_definition_body_site')
    op.drop_index(op.f('ix_activity_definition_body_site_activity_definition_id'), table_name='activity_definition_body_site')
    op.drop_table('activity_definition_body_site')
    op.drop_index(op.f('ix_activity_definition_version'), table_name='activity_definition')
    op.drop_index(op.f('ix_activity_definition_user_id'), table_name='activity_definition')
    op.drop_index(op.f('ix_activity_definition_url'), table_name='activity_definition')
    op.drop_index(op.f('ix_activity_definition_subject_reference_id'), table_name='activity_definition')
    op.drop_index(op.f('ix_activity_definition_status'), table_name='activity_definition')
    op.drop_index(op.f('ix_activity_definition_product_reference_id'), table_name='activity_definition')
    op.drop_index(op.f('ix_activity_definition_org_id'), table_name='activity_definition')
    op.drop_index(op.f('ix_activity_definition_name'), table_name='activity_definition')
    op.drop_index(op.f('ix_activity_definition_location_id'), table_name='activity_definition')
    op.drop_index(op.f('ix_activity_definition_kind'), table_name='activity_definition')
    op.drop_index(op.f('ix_activity_definition_intent'), table_name='activity_definition')
    op.drop_index(op.f('ix_activity_definition_id'), table_name='activity_definition')
    op.drop_index(op.f('ix_activity_definition_date'), table_name='activity_definition')
    op.drop_index(op.f('ix_activity_definition_code_code'), table_name='activity_definition')
    op.drop_index(op.f('ix_activity_definition_activity_definition_id'), table_name='activity_definition')
    op.drop_table('activity_definition')
    op.execute('DROP SEQUENCE IF EXISTS activity_definition_pub_seq')
    # ### end Alembic commands ###
    postgresql.ENUM(name='activity_definition_status').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='activity_definition_group_ref_type').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='activity_definition_kind').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='activity_definition_intent').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='activity_definition_priority').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='activity_definition_location_ref_type').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='activity_definition_product_ref_type').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='activity_definition_contact_kind').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='activity_definition_observation_ref_type').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='activity_definition_participant_type').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='activity_definition_related_artifact_type').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='activity_definition_specimen_ref_type').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='activity_definition_use_context_ref_type').drop(op.get_bind(), checkfirst=True)
