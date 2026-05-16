"""add_observation_tables

Revision ID: 2e2e58149f4f
Revises: 2cba83ec392a
Create Date: 2026-05-16 12:08:18.642666

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '2e2e58149f4f'
down_revision: Union[str, None] = '2cba83ec392a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ── Enum types — all created fresh by this migration ────────────────────────

_obs_status = postgresql.ENUM(
    'registered', 'preliminary', 'final', 'amended',
    'corrected', 'cancelled', 'entered-in-error', 'unknown',
    name='observation_status',
)
_obs_subject_ref = postgresql.ENUM(
    'Patient', 'Group', 'Device', 'Location',
    name='obs_subject_ref_type',
)
_obs_encounter_ref = postgresql.ENUM(
    'Encounter',
    name='obs_encounter_ref_type',
)
_obs_specimen_ref = postgresql.ENUM(
    'Specimen',
    name='obs_specimen_ref_type',
)
_obs_device_ref = postgresql.ENUM(
    'Device', 'DeviceMetric',
    name='obs_device_ref_type',
)
_obs_based_on_ref = postgresql.ENUM(
    'CarePlan', 'DeviceRequest', 'ImmunizationRecommendation',
    'MedicationRequest', 'NutritionOrder', 'ServiceRequest',
    name='obs_based_on_ref_type',
)
_obs_part_of_ref = postgresql.ENUM(
    'MedicationAdministration', 'MedicationDispense', 'MedicationStatement',
    'Procedure', 'Immunization', 'ImagingStudy',
    name='obs_part_of_ref_type',
)
_obs_performer_ref = postgresql.ENUM(
    'Practitioner', 'PractitionerRole', 'Organization',
    'CareTeam', 'Patient', 'RelatedPerson',
    name='obs_performer_ref_type',
)
_obs_has_member_ref = postgresql.ENUM(
    'Observation', 'QuestionnaireResponse', 'MolecularSequence',
    name='obs_has_member_ref_type',
)
_obs_derived_from_ref = postgresql.ENUM(
    'DocumentReference', 'ImagingStudy', 'Media',
    'QuestionnaireResponse', 'Observation', 'MolecularSequence',
    name='obs_derived_from_ref_type',
)


def upgrade() -> None:
    bind = op.get_bind()

    # Create sequence (autogenerate omits this)
    op.execute(
        "CREATE SEQUENCE IF NOT EXISTS observation_id_seq START WITH 160000 INCREMENT BY 1"
    )

    # Create all new enum types
    _obs_status.create(bind, checkfirst=True)
    _obs_subject_ref.create(bind, checkfirst=True)
    _obs_encounter_ref.create(bind, checkfirst=True)
    _obs_specimen_ref.create(bind, checkfirst=True)
    _obs_device_ref.create(bind, checkfirst=True)
    _obs_based_on_ref.create(bind, checkfirst=True)
    _obs_part_of_ref.create(bind, checkfirst=True)
    _obs_performer_ref.create(bind, checkfirst=True)
    _obs_has_member_ref.create(bind, checkfirst=True)
    _obs_derived_from_ref.create(bind, checkfirst=True)

    # ── Main observation table ───────────────────────────────────────────────
    op.create_table('observation',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('observation_id', sa.Integer(),
                  server_default=sa.text("nextval('observation_id_seq')"), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('org_id', sa.String(), nullable=True),
        # status 1..1
        sa.Column('status',
                  postgresql.ENUM('registered', 'preliminary', 'final', 'amended',
                                  'corrected', 'cancelled', 'entered-in-error', 'unknown',
                                  name='observation_status', create_type=False),
                  nullable=False),
        # code 1..1 CodeableConcept
        sa.Column('code_system', sa.String(), nullable=True),
        sa.Column('code_code', sa.String(), nullable=True),
        sa.Column('code_display', sa.String(), nullable=True),
        sa.Column('code_text', sa.String(), nullable=True),
        # subject 0..1 Reference(Patient|Group|Device|Location)
        sa.Column('subject_type',
                  postgresql.ENUM('Patient', 'Group', 'Device', 'Location',
                                  name='obs_subject_ref_type', create_type=False),
                  nullable=True),
        sa.Column('subject_id', sa.Integer(), nullable=True),
        sa.Column('subject_display', sa.String(), nullable=True),
        # encounter 0..1 Reference(Encounter)
        sa.Column('encounter_type',
                  postgresql.ENUM('Encounter', name='obs_encounter_ref_type', create_type=False),
                  nullable=True),
        sa.Column('encounter_id', sa.Integer(), nullable=True),
        sa.Column('encounter_display', sa.String(), nullable=True),
        # effective[x] — dateTime | Period | Timing | instant
        sa.Column('effective_date_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('effective_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('effective_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('effective_instant', sa.DateTime(timezone=True), nullable=True),
        sa.Column('effective_timing_event', sa.Text(), nullable=True),
        sa.Column('effective_timing_code_system', sa.String(), nullable=True),
        sa.Column('effective_timing_code_code', sa.String(), nullable=True),
        sa.Column('effective_timing_code_display', sa.String(), nullable=True),
        sa.Column('effective_timing_code_text', sa.String(), nullable=True),
        sa.Column('effective_timing_repeat_bounds_duration_value', sa.Numeric(), nullable=True),
        sa.Column('effective_timing_repeat_bounds_duration_comparator', sa.String(), nullable=True),
        sa.Column('effective_timing_repeat_bounds_duration_unit', sa.String(), nullable=True),
        sa.Column('effective_timing_repeat_bounds_duration_system', sa.String(), nullable=True),
        sa.Column('effective_timing_repeat_bounds_duration_code', sa.String(), nullable=True),
        sa.Column('effective_timing_repeat_bounds_range_low_value', sa.Numeric(), nullable=True),
        sa.Column('effective_timing_repeat_bounds_range_low_unit', sa.String(), nullable=True),
        sa.Column('effective_timing_repeat_bounds_range_low_system', sa.String(), nullable=True),
        sa.Column('effective_timing_repeat_bounds_range_low_code', sa.String(), nullable=True),
        sa.Column('effective_timing_repeat_bounds_range_high_value', sa.Numeric(), nullable=True),
        sa.Column('effective_timing_repeat_bounds_range_high_unit', sa.String(), nullable=True),
        sa.Column('effective_timing_repeat_bounds_range_high_system', sa.String(), nullable=True),
        sa.Column('effective_timing_repeat_bounds_range_high_code', sa.String(), nullable=True),
        sa.Column('effective_timing_repeat_bounds_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('effective_timing_repeat_bounds_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('effective_timing_repeat_count', sa.Integer(), nullable=True),
        sa.Column('effective_timing_repeat_count_max', sa.Integer(), nullable=True),
        sa.Column('effective_timing_repeat_duration', sa.Numeric(), nullable=True),
        sa.Column('effective_timing_repeat_duration_max', sa.Numeric(), nullable=True),
        sa.Column('effective_timing_repeat_duration_unit', sa.String(), nullable=True),
        sa.Column('effective_timing_repeat_frequency', sa.Integer(), nullable=True),
        sa.Column('effective_timing_repeat_frequency_max', sa.Integer(), nullable=True),
        sa.Column('effective_timing_repeat_period', sa.Numeric(), nullable=True),
        sa.Column('effective_timing_repeat_period_max', sa.Numeric(), nullable=True),
        sa.Column('effective_timing_repeat_period_unit', sa.String(), nullable=True),
        sa.Column('effective_timing_repeat_day_of_week', sa.Text(), nullable=True),
        sa.Column('effective_timing_repeat_time_of_day', sa.Text(), nullable=True),
        sa.Column('effective_timing_repeat_when', sa.Text(), nullable=True),
        sa.Column('effective_timing_repeat_offset', sa.Integer(), nullable=True),
        # issued 0..1 instant
        sa.Column('issued', sa.DateTime(timezone=True), nullable=True),
        # value[x] — Quantity
        sa.Column('value_quantity_value', sa.Numeric(), nullable=True),
        sa.Column('value_quantity_comparator', sa.String(), nullable=True),
        sa.Column('value_quantity_unit', sa.String(), nullable=True),
        sa.Column('value_quantity_system', sa.String(), nullable=True),
        sa.Column('value_quantity_code', sa.String(), nullable=True),
        # value[x] — CodeableConcept
        sa.Column('value_codeable_concept_system', sa.String(), nullable=True),
        sa.Column('value_codeable_concept_code', sa.String(), nullable=True),
        sa.Column('value_codeable_concept_display', sa.String(), nullable=True),
        sa.Column('value_codeable_concept_text', sa.String(), nullable=True),
        # value[x] — primitives
        sa.Column('value_string', sa.String(), nullable=True),
        sa.Column('value_boolean', sa.Boolean(), nullable=True),
        sa.Column('value_integer', sa.Integer(), nullable=True),
        sa.Column('value_time', sa.String(), nullable=True),
        sa.Column('value_date_time', sa.DateTime(timezone=True), nullable=True),
        # value[x] — Period
        sa.Column('value_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('value_period_end', sa.DateTime(timezone=True), nullable=True),
        # value[x] — Range (SimpleQuantity — no comparator)
        sa.Column('value_range_low_value', sa.Numeric(), nullable=True),
        sa.Column('value_range_low_unit', sa.String(), nullable=True),
        sa.Column('value_range_low_system', sa.String(), nullable=True),
        sa.Column('value_range_low_code', sa.String(), nullable=True),
        sa.Column('value_range_high_value', sa.Numeric(), nullable=True),
        sa.Column('value_range_high_unit', sa.String(), nullable=True),
        sa.Column('value_range_high_system', sa.String(), nullable=True),
        sa.Column('value_range_high_code', sa.String(), nullable=True),
        # value[x] — Ratio (full Quantity — has comparator)
        sa.Column('value_ratio_numerator_value', sa.Numeric(), nullable=True),
        sa.Column('value_ratio_numerator_comparator', sa.String(), nullable=True),
        sa.Column('value_ratio_numerator_unit', sa.String(), nullable=True),
        sa.Column('value_ratio_numerator_system', sa.String(), nullable=True),
        sa.Column('value_ratio_numerator_code', sa.String(), nullable=True),
        sa.Column('value_ratio_denominator_value', sa.Numeric(), nullable=True),
        sa.Column('value_ratio_denominator_comparator', sa.String(), nullable=True),
        sa.Column('value_ratio_denominator_unit', sa.String(), nullable=True),
        sa.Column('value_ratio_denominator_system', sa.String(), nullable=True),
        sa.Column('value_ratio_denominator_code', sa.String(), nullable=True),
        # value[x] — SampledData
        sa.Column('value_sampled_data_origin_value', sa.Numeric(), nullable=True),
        sa.Column('value_sampled_data_origin_unit', sa.String(), nullable=True),
        sa.Column('value_sampled_data_origin_system', sa.String(), nullable=True),
        sa.Column('value_sampled_data_origin_code', sa.String(), nullable=True),
        sa.Column('value_sampled_data_period', sa.Numeric(), nullable=True),
        sa.Column('value_sampled_data_factor', sa.Numeric(), nullable=True),
        sa.Column('value_sampled_data_lower_limit', sa.Numeric(), nullable=True),
        sa.Column('value_sampled_data_upper_limit', sa.Numeric(), nullable=True),
        sa.Column('value_sampled_data_dimensions', sa.Integer(), nullable=True),
        sa.Column('value_sampled_data_data', sa.Text(), nullable=True),
        # dataAbsentReason 0..1 CodeableConcept
        sa.Column('data_absent_reason_system', sa.String(), nullable=True),
        sa.Column('data_absent_reason_code', sa.String(), nullable=True),
        sa.Column('data_absent_reason_display', sa.String(), nullable=True),
        sa.Column('data_absent_reason_text', sa.String(), nullable=True),
        # bodySite 0..1 CodeableConcept
        sa.Column('body_site_system', sa.String(), nullable=True),
        sa.Column('body_site_code', sa.String(), nullable=True),
        sa.Column('body_site_display', sa.String(), nullable=True),
        sa.Column('body_site_text', sa.String(), nullable=True),
        # method 0..1 CodeableConcept
        sa.Column('method_system', sa.String(), nullable=True),
        sa.Column('method_code', sa.String(), nullable=True),
        sa.Column('method_display', sa.String(), nullable=True),
        sa.Column('method_text', sa.String(), nullable=True),
        # specimen 0..1 Reference(Specimen)
        sa.Column('specimen_type',
                  postgresql.ENUM('Specimen', name='obs_specimen_ref_type', create_type=False),
                  nullable=True),
        sa.Column('specimen_id', sa.Integer(), nullable=True),
        sa.Column('specimen_display', sa.String(), nullable=True),
        # device 0..1 Reference(Device|DeviceMetric)
        sa.Column('device_type',
                  postgresql.ENUM('Device', 'DeviceMetric',
                                  name='obs_device_ref_type', create_type=False),
                  nullable=True),
        sa.Column('device_id', sa.Integer(), nullable=True),
        sa.Column('device_display', sa.String(), nullable=True),
        # audit
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_observation_id'), 'observation', ['id'], unique=False)
    op.create_index(op.f('ix_observation_observation_id'), 'observation', ['observation_id'], unique=True)
    op.create_index(op.f('ix_observation_org_id'), 'observation', ['org_id'], unique=False)
    op.create_index(op.f('ix_observation_user_id'), 'observation', ['user_id'], unique=False)

    # ── observation_based_on ─────────────────────────────────────────────────
    op.create_table('observation_based_on',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('observation_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('reference_type',
                  postgresql.ENUM('CarePlan', 'DeviceRequest', 'ImmunizationRecommendation',
                                  'MedicationRequest', 'NutritionOrder', 'ServiceRequest',
                                  name='obs_based_on_ref_type', create_type=False),
                  nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['observation_id'], ['observation.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_observation_based_on_observation_id'), 'observation_based_on', ['observation_id'], unique=False)

    # ── observation_part_of ──────────────────────────────────────────────────
    op.create_table('observation_part_of',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('observation_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('reference_type',
                  postgresql.ENUM('MedicationAdministration', 'MedicationDispense',
                                  'MedicationStatement', 'Procedure', 'Immunization', 'ImagingStudy',
                                  name='obs_part_of_ref_type', create_type=False),
                  nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['observation_id'], ['observation.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_observation_part_of_observation_id'), 'observation_part_of', ['observation_id'], unique=False)

    # ── observation_category ─────────────────────────────────────────────────
    op.create_table('observation_category',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('observation_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['observation_id'], ['observation.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_observation_category_observation_id'), 'observation_category', ['observation_id'], unique=False)

    # ── observation_focus ────────────────────────────────────────────────────
    op.create_table('observation_focus',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('observation_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('reference_type', sa.String(), nullable=True),   # open reference
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['observation_id'], ['observation.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_observation_focus_observation_id'), 'observation_focus', ['observation_id'], unique=False)

    # ── observation_performer ────────────────────────────────────────────────
    op.create_table('observation_performer',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('observation_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('reference_type',
                  postgresql.ENUM('Practitioner', 'PractitionerRole', 'Organization',
                                  'CareTeam', 'Patient', 'RelatedPerson',
                                  name='obs_performer_ref_type', create_type=False),
                  nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['observation_id'], ['observation.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_observation_performer_observation_id'), 'observation_performer', ['observation_id'], unique=False)

    # ── observation_interpretation ───────────────────────────────────────────
    op.create_table('observation_interpretation',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('observation_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['observation_id'], ['observation.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_observation_interpretation_observation_id'), 'observation_interpretation', ['observation_id'], unique=False)

    # ── observation_note ─────────────────────────────────────────────────────
    op.create_table('observation_note',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('observation_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('author_string', sa.String(), nullable=True),
        sa.Column('author_reference_type', sa.String(), nullable=True),
        sa.Column('author_reference_id', sa.Integer(), nullable=True),
        sa.Column('author_reference_display', sa.String(), nullable=True),
        sa.Column('time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['observation_id'], ['observation.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_observation_note_observation_id'), 'observation_note', ['observation_id'], unique=False)

    # ── observation_reference_range ──────────────────────────────────────────
    op.create_table('observation_reference_range',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('observation_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('low_value', sa.Numeric(), nullable=True),
        sa.Column('low_unit', sa.String(), nullable=True),
        sa.Column('low_system', sa.String(), nullable=True),
        sa.Column('low_code', sa.String(), nullable=True),
        sa.Column('high_value', sa.Numeric(), nullable=True),
        sa.Column('high_unit', sa.String(), nullable=True),
        sa.Column('high_system', sa.String(), nullable=True),
        sa.Column('high_code', sa.String(), nullable=True),
        sa.Column('type_system', sa.String(), nullable=True),
        sa.Column('type_code', sa.String(), nullable=True),
        sa.Column('type_display', sa.String(), nullable=True),
        sa.Column('type_text', sa.String(), nullable=True),
        sa.Column('age_low_value', sa.Numeric(), nullable=True),
        sa.Column('age_low_unit', sa.String(), nullable=True),
        sa.Column('age_low_system', sa.String(), nullable=True),
        sa.Column('age_low_code', sa.String(), nullable=True),
        sa.Column('age_high_value', sa.Numeric(), nullable=True),
        sa.Column('age_high_unit', sa.String(), nullable=True),
        sa.Column('age_high_system', sa.String(), nullable=True),
        sa.Column('age_high_code', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['observation_id'], ['observation.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_observation_reference_range_observation_id'), 'observation_reference_range', ['observation_id'], unique=False)

    # ── observation_has_member ───────────────────────────────────────────────
    op.create_table('observation_has_member',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('observation_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('reference_type',
                  postgresql.ENUM('Observation', 'QuestionnaireResponse', 'MolecularSequence',
                                  name='obs_has_member_ref_type', create_type=False),
                  nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['observation_id'], ['observation.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_observation_has_member_observation_id'), 'observation_has_member', ['observation_id'], unique=False)

    # ── observation_derived_from ─────────────────────────────────────────────
    op.create_table('observation_derived_from',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('observation_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('reference_type',
                  postgresql.ENUM('DocumentReference', 'ImagingStudy', 'Media',
                                  'QuestionnaireResponse', 'Observation', 'MolecularSequence',
                                  name='obs_derived_from_ref_type', create_type=False),
                  nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['observation_id'], ['observation.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_observation_derived_from_observation_id'), 'observation_derived_from', ['observation_id'], unique=False)

    # ── observation_component ────────────────────────────────────────────────
    op.create_table('observation_component',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('observation_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('code_system', sa.String(), nullable=True),
        sa.Column('code_code', sa.String(), nullable=True),
        sa.Column('code_display', sa.String(), nullable=True),
        sa.Column('code_text', sa.String(), nullable=True),
        sa.Column('value_quantity_value', sa.Numeric(), nullable=True),
        sa.Column('value_quantity_comparator', sa.String(), nullable=True),
        sa.Column('value_quantity_unit', sa.String(), nullable=True),
        sa.Column('value_quantity_system', sa.String(), nullable=True),
        sa.Column('value_quantity_code', sa.String(), nullable=True),
        sa.Column('value_codeable_concept_system', sa.String(), nullable=True),
        sa.Column('value_codeable_concept_code', sa.String(), nullable=True),
        sa.Column('value_codeable_concept_display', sa.String(), nullable=True),
        sa.Column('value_codeable_concept_text', sa.String(), nullable=True),
        sa.Column('value_string', sa.String(), nullable=True),
        sa.Column('value_boolean', sa.Boolean(), nullable=True),
        sa.Column('value_integer', sa.Integer(), nullable=True),
        sa.Column('value_time', sa.String(), nullable=True),
        sa.Column('value_date_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('value_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('value_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('value_range_low_value', sa.Numeric(), nullable=True),
        sa.Column('value_range_low_unit', sa.String(), nullable=True),
        sa.Column('value_range_low_system', sa.String(), nullable=True),
        sa.Column('value_range_low_code', sa.String(), nullable=True),
        sa.Column('value_range_high_value', sa.Numeric(), nullable=True),
        sa.Column('value_range_high_unit', sa.String(), nullable=True),
        sa.Column('value_range_high_system', sa.String(), nullable=True),
        sa.Column('value_range_high_code', sa.String(), nullable=True),
        sa.Column('value_ratio_numerator_value', sa.Numeric(), nullable=True),
        sa.Column('value_ratio_numerator_comparator', sa.String(), nullable=True),
        sa.Column('value_ratio_numerator_unit', sa.String(), nullable=True),
        sa.Column('value_ratio_numerator_system', sa.String(), nullable=True),
        sa.Column('value_ratio_numerator_code', sa.String(), nullable=True),
        sa.Column('value_ratio_denominator_value', sa.Numeric(), nullable=True),
        sa.Column('value_ratio_denominator_comparator', sa.String(), nullable=True),
        sa.Column('value_ratio_denominator_unit', sa.String(), nullable=True),
        sa.Column('value_ratio_denominator_system', sa.String(), nullable=True),
        sa.Column('value_ratio_denominator_code', sa.String(), nullable=True),
        sa.Column('value_sampled_data_origin_value', sa.Numeric(), nullable=True),
        sa.Column('value_sampled_data_origin_unit', sa.String(), nullable=True),
        sa.Column('value_sampled_data_origin_system', sa.String(), nullable=True),
        sa.Column('value_sampled_data_origin_code', sa.String(), nullable=True),
        sa.Column('value_sampled_data_period', sa.Numeric(), nullable=True),
        sa.Column('value_sampled_data_factor', sa.Numeric(), nullable=True),
        sa.Column('value_sampled_data_lower_limit', sa.Numeric(), nullable=True),
        sa.Column('value_sampled_data_upper_limit', sa.Numeric(), nullable=True),
        sa.Column('value_sampled_data_dimensions', sa.Integer(), nullable=True),
        sa.Column('value_sampled_data_data', sa.Text(), nullable=True),
        sa.Column('data_absent_reason_system', sa.String(), nullable=True),
        sa.Column('data_absent_reason_code', sa.String(), nullable=True),
        sa.Column('data_absent_reason_display', sa.String(), nullable=True),
        sa.Column('data_absent_reason_text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['observation_id'], ['observation.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_observation_component_observation_id'), 'observation_component', ['observation_id'], unique=False)

    # ── observation_component_interpretation ─────────────────────────────────
    op.create_table('observation_component_interpretation',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('component_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['component_id'], ['observation_component.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_observation_component_interpretation_component_id'), 'observation_component_interpretation', ['component_id'], unique=False)

    # ── observation_component_reference_range ────────────────────────────────
    op.create_table('observation_component_reference_range',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('component_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('low_value', sa.Numeric(), nullable=True),
        sa.Column('low_unit', sa.String(), nullable=True),
        sa.Column('low_system', sa.String(), nullable=True),
        sa.Column('low_code', sa.String(), nullable=True),
        sa.Column('high_value', sa.Numeric(), nullable=True),
        sa.Column('high_unit', sa.String(), nullable=True),
        sa.Column('high_system', sa.String(), nullable=True),
        sa.Column('high_code', sa.String(), nullable=True),
        sa.Column('type_system', sa.String(), nullable=True),
        sa.Column('type_code', sa.String(), nullable=True),
        sa.Column('type_display', sa.String(), nullable=True),
        sa.Column('type_text', sa.String(), nullable=True),
        sa.Column('age_low_value', sa.Numeric(), nullable=True),
        sa.Column('age_low_unit', sa.String(), nullable=True),
        sa.Column('age_low_system', sa.String(), nullable=True),
        sa.Column('age_low_code', sa.String(), nullable=True),
        sa.Column('age_high_value', sa.Numeric(), nullable=True),
        sa.Column('age_high_unit', sa.String(), nullable=True),
        sa.Column('age_high_system', sa.String(), nullable=True),
        sa.Column('age_high_code', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['component_id'], ['observation_component.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_observation_component_reference_range_component_id'), 'observation_component_reference_range', ['component_id'], unique=False)

    # ── observation_reference_range_applies_to ───────────────────────────────
    op.create_table('observation_reference_range_applies_to',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('reference_range_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['reference_range_id'], ['observation_reference_range.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_observation_reference_range_applies_to_reference_range_id'), 'observation_reference_range_applies_to', ['reference_range_id'], unique=False)

    # ── observation_component_reference_range_applies_to ─────────────────────
    op.create_table('observation_component_reference_range_applies_to',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('reference_range_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['reference_range_id'], ['observation_component_reference_range.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_observation_component_reference_range_applies_to_reference_range_id'), 'observation_component_reference_range_applies_to', ['reference_range_id'], unique=False)


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_index(op.f('ix_observation_component_reference_range_applies_to_reference_range_id'), table_name='observation_component_reference_range_applies_to')
    op.drop_table('observation_component_reference_range_applies_to')
    op.drop_index(op.f('ix_observation_reference_range_applies_to_reference_range_id'), table_name='observation_reference_range_applies_to')
    op.drop_table('observation_reference_range_applies_to')
    op.drop_index(op.f('ix_observation_component_reference_range_component_id'), table_name='observation_component_reference_range')
    op.drop_table('observation_component_reference_range')
    op.drop_index(op.f('ix_observation_component_interpretation_component_id'), table_name='observation_component_interpretation')
    op.drop_table('observation_component_interpretation')
    op.drop_index(op.f('ix_observation_component_observation_id'), table_name='observation_component')
    op.drop_table('observation_component')
    op.drop_index(op.f('ix_observation_derived_from_observation_id'), table_name='observation_derived_from')
    op.drop_table('observation_derived_from')
    op.drop_index(op.f('ix_observation_has_member_observation_id'), table_name='observation_has_member')
    op.drop_table('observation_has_member')
    op.drop_index(op.f('ix_observation_reference_range_observation_id'), table_name='observation_reference_range')
    op.drop_table('observation_reference_range')
    op.drop_index(op.f('ix_observation_note_observation_id'), table_name='observation_note')
    op.drop_table('observation_note')
    op.drop_index(op.f('ix_observation_interpretation_observation_id'), table_name='observation_interpretation')
    op.drop_table('observation_interpretation')
    op.drop_index(op.f('ix_observation_performer_observation_id'), table_name='observation_performer')
    op.drop_table('observation_performer')
    op.drop_index(op.f('ix_observation_focus_observation_id'), table_name='observation_focus')
    op.drop_table('observation_focus')
    op.drop_index(op.f('ix_observation_category_observation_id'), table_name='observation_category')
    op.drop_table('observation_category')
    op.drop_index(op.f('ix_observation_part_of_observation_id'), table_name='observation_part_of')
    op.drop_table('observation_part_of')
    op.drop_index(op.f('ix_observation_based_on_observation_id'), table_name='observation_based_on')
    op.drop_table('observation_based_on')
    op.drop_index(op.f('ix_observation_user_id'), table_name='observation')
    op.drop_index(op.f('ix_observation_org_id'), table_name='observation')
    op.drop_index(op.f('ix_observation_observation_id'), table_name='observation')
    op.drop_index(op.f('ix_observation_id'), table_name='observation')
    op.drop_table('observation')

    op.execute("DROP SEQUENCE IF EXISTS observation_id_seq")

    _obs_derived_from_ref.drop(bind, checkfirst=True)
    _obs_has_member_ref.drop(bind, checkfirst=True)
    _obs_performer_ref.drop(bind, checkfirst=True)
    _obs_part_of_ref.drop(bind, checkfirst=True)
    _obs_based_on_ref.drop(bind, checkfirst=True)
    _obs_device_ref.drop(bind, checkfirst=True)
    _obs_specimen_ref.drop(bind, checkfirst=True)
    _obs_encounter_ref.drop(bind, checkfirst=True)
    _obs_subject_ref.drop(bind, checkfirst=True)
    _obs_status.drop(bind, checkfirst=True)
