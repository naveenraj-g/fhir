"""encounter_r5_updates

Revision ID: 719a592d7843
Revises: 9084ef1a2f6d
Create Date: 2026-05-15 15:17:32.455226

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '719a592d7843'
down_revision: Union[str, None] = '9084ef1a2f6d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# New enum types (all TitleCase FHIR values)
_encounter_service_type_reference_type = postgresql.ENUM(
    'HealthcareService',
    name='encounter_service_type_reference_type',
)
_encounter_reason_value_reference_type = postgresql.ENUM(
    'Condition', 'DiagnosticReport', 'Observation', 'Procedure',
    name='encounter_reason_value_reference_type',
)
# Existing enum types that need to be dropped and recreated with TitleCase values
_encounter_participant_reference_type = postgresql.ENUM(
    'Patient', 'Group', 'RelatedPerson', 'Practitioner', 'PractitionerRole',
    'Device', 'HealthcareService',
    name='encounter_participant_reference_type',
)
_encounter_diagnosis_condition_type = postgresql.ENUM(
    'Condition',
    name='encounter_diagnosis_condition_type',
)


def upgrade() -> None:
    # Create new enum types
    _encounter_service_type_reference_type.create(op.get_bind(), checkfirst=True)
    _encounter_reason_value_reference_type.create(op.get_bind(), checkfirst=True)

    # Drop old columns that reference enums being replaced (must happen before enum drop)
    op.drop_column('encounter_participant', 'individual_display')
    op.drop_column('encounter_participant', 'individual_id')
    op.drop_column('encounter_participant', 'individual_type')
    op.drop_column('encounter_diagnosis', 'condition_display')
    op.drop_column('encounter_diagnosis', 'condition_id')
    op.drop_column('encounter_diagnosis', 'condition_type')
    op.drop_column('encounter_diagnosis', 'rank')
    op.drop_column('encounter_diagnosis', 'use_code')
    op.drop_column('encounter_diagnosis', 'use_display')
    op.drop_column('encounter_diagnosis', 'use_system')
    op.drop_column('encounter_diagnosis', 'use_text')

    # Drop old enum types then recreate with TitleCase values
    op.execute('DROP TYPE IF EXISTS encounter_participant_reference_type')
    op.execute('DROP TYPE IF EXISTS encounter_diagnosis_condition_type')
    _encounter_participant_reference_type.create(op.get_bind(), checkfirst=True)
    _encounter_diagnosis_condition_type.create(op.get_bind(), checkfirst=True)

    # Add new encounter_participant.actor_type column with expanded enum
    op.add_column(
        'encounter_participant',
        sa.Column(
            'actor_type',
            postgresql.ENUM(
                'Patient', 'Group', 'RelatedPerson', 'Practitioner', 'PractitionerRole',
                'Device', 'HealthcareService',
                name='encounter_participant_reference_type', create_type=False,
            ),
            nullable=True,
        ),
    )
    op.add_column('encounter_participant', sa.Column('actor_id', sa.Integer(), nullable=True))
    op.add_column('encounter_participant', sa.Column('actor_display', sa.String(), nullable=True))

    # Drop old tables
    op.drop_index(op.f('ix_encounter_reason_code_encounter_id'), table_name='encounter_reason_code')
    op.drop_table('encounter_reason_code')
    op.drop_index(op.f('ix_encounter_reason_reference_encounter_id'), table_name='encounter_reason_reference')
    op.drop_table('encounter_reason_reference')
    op.drop_index(op.f('ix_encounter_hosp_diet_preference_encounter_id'), table_name='encounter_hosp_diet_preference')
    op.drop_table('encounter_hosp_diet_preference')
    op.drop_index(op.f('ix_encounter_hosp_special_arrangement_encounter_id'), table_name='encounter_hosp_special_arrangement')
    op.drop_table('encounter_hosp_special_arrangement')
    op.drop_index(op.f('ix_encounter_hosp_special_courtesy_encounter_id'), table_name='encounter_hosp_special_courtesy')
    op.drop_table('encounter_hosp_special_courtesy')

    # Create new child tables
    op.create_table(
        'encounter_business_status',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('encounter_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('code_system', sa.String(), nullable=True),
        sa.Column('code_code', sa.String(), nullable=False),
        sa.Column('code_display', sa.String(), nullable=True),
        sa.Column('code_text', sa.String(), nullable=True),
        sa.Column('type_system', sa.String(), nullable=True),
        sa.Column('type_code', sa.String(), nullable=True),
        sa.Column('type_display', sa.String(), nullable=True),
        sa.Column('effective_date', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['encounter_id'], ['encounter.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_encounter_business_status_encounter_id'), 'encounter_business_status', ['encounter_id'], unique=False)

    op.create_table(
        'encounter_care_team',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('encounter_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('care_team_id', sa.Integer(), nullable=True),
        sa.Column('care_team_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['encounter_id'], ['encounter.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_encounter_care_team_encounter_id'), 'encounter_care_team', ['encounter_id'], unique=False)

    op.create_table(
        'encounter_class',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('encounter_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['encounter_id'], ['encounter.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_encounter_class_encounter_id'), 'encounter_class', ['encounter_id'], unique=False)

    op.create_table(
        'encounter_diet_preference',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('encounter_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['encounter_id'], ['encounter.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_encounter_diet_preference_encounter_id'), 'encounter_diet_preference', ['encounter_id'], unique=False)

    op.create_table(
        'encounter_special_arrangement',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('encounter_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['encounter_id'], ['encounter.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_encounter_special_arrangement_encounter_id'), 'encounter_special_arrangement', ['encounter_id'], unique=False)

    op.create_table(
        'encounter_special_courtesy',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('encounter_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['encounter_id'], ['encounter.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_encounter_special_courtesy_encounter_id'), 'encounter_special_courtesy', ['encounter_id'], unique=False)

    op.create_table(
        'encounter_virtual_service',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('encounter_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('channel_type_system', sa.String(), nullable=True),
        sa.Column('channel_type_code', sa.String(), nullable=True),
        sa.Column('channel_type_display', sa.String(), nullable=True),
        sa.Column('address_url', sa.String(), nullable=True),
        sa.Column('additional_info', sa.Text(), nullable=True),
        sa.Column('max_participants', sa.Integer(), nullable=True),
        sa.Column('session_key', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['encounter_id'], ['encounter.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_encounter_virtual_service_encounter_id'), 'encounter_virtual_service', ['encounter_id'], unique=False)

    op.create_table(
        'encounter_service_type',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('encounter_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column(
            'reference_type',
            postgresql.ENUM('HealthcareService', name='encounter_service_type_reference_type', create_type=False),
            nullable=True,
        ),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['encounter_id'], ['encounter.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_encounter_service_type_encounter_id'), 'encounter_service_type', ['encounter_id'], unique=False)

    # encounter_reason parent table + grandchildren
    op.create_table(
        'encounter_reason',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('encounter_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['encounter_id'], ['encounter.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_encounter_reason_encounter_id'), 'encounter_reason', ['encounter_id'], unique=False)

    op.create_table(
        'encounter_reason_use',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('reason_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['reason_id'], ['encounter_reason.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_encounter_reason_use_reason_id'), 'encounter_reason_use', ['reason_id'], unique=False)

    op.create_table(
        'encounter_reason_value',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('reason_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column(
            'reference_type',
            postgresql.ENUM(
                'Condition', 'DiagnosticReport', 'Observation', 'Procedure',
                name='encounter_reason_value_reference_type', create_type=False,
            ),
            nullable=True,
        ),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['reason_id'], ['encounter_reason.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_encounter_reason_value_reason_id'), 'encounter_reason_value', ['reason_id'], unique=False)

    # encounter_diagnosis grandchildren
    op.create_table(
        'encounter_diagnosis_condition',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('diagnosis_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column(
            'reference_type',
            postgresql.ENUM('Condition', name='encounter_diagnosis_condition_type', create_type=False),
            nullable=True,
        ),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['diagnosis_id'], ['encounter_diagnosis.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_encounter_diagnosis_condition_diagnosis_id'), 'encounter_diagnosis_condition', ['diagnosis_id'], unique=False)

    op.create_table(
        'encounter_diagnosis_use',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('diagnosis_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['diagnosis_id'], ['encounter_diagnosis.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_encounter_diagnosis_use_diagnosis_id'), 'encounter_diagnosis_use', ['diagnosis_id'], unique=False)

    # encounter main table: add new columns, drop old columns
    op.add_column('encounter', sa.Column('subject_status_system', sa.String(), nullable=True))
    op.add_column('encounter', sa.Column('subject_status_code', sa.String(), nullable=True))
    op.add_column('encounter', sa.Column('subject_status_display', sa.String(), nullable=True))
    op.add_column('encounter', sa.Column('subject_status_text', sa.String(), nullable=True))
    op.add_column('encounter', sa.Column('actual_period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('encounter', sa.Column('actual_period_end', sa.DateTime(timezone=True), nullable=True))
    op.add_column('encounter', sa.Column('planned_start_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('encounter', sa.Column('planned_end_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('encounter', sa.Column('admission_pre_admission_identifier_system', sa.String(), nullable=True))
    op.add_column('encounter', sa.Column('admission_pre_admission_identifier_value', sa.String(), nullable=True))
    op.add_column('encounter', sa.Column('admission_origin_type', sa.String(), nullable=True))
    op.add_column('encounter', sa.Column('admission_origin_id', sa.Integer(), nullable=True))
    op.add_column('encounter', sa.Column('admission_origin_display', sa.String(), nullable=True))
    op.add_column('encounter', sa.Column('admission_admit_source_system', sa.String(), nullable=True))
    op.add_column('encounter', sa.Column('admission_admit_source_code', sa.String(), nullable=True))
    op.add_column('encounter', sa.Column('admission_admit_source_display', sa.String(), nullable=True))
    op.add_column('encounter', sa.Column('admission_admit_source_text', sa.String(), nullable=True))
    op.add_column('encounter', sa.Column('admission_re_admission_system', sa.String(), nullable=True))
    op.add_column('encounter', sa.Column('admission_re_admission_code', sa.String(), nullable=True))
    op.add_column('encounter', sa.Column('admission_re_admission_display', sa.String(), nullable=True))
    op.add_column('encounter', sa.Column('admission_re_admission_text', sa.String(), nullable=True))
    op.add_column('encounter', sa.Column('admission_destination_type', sa.String(), nullable=True))
    op.add_column('encounter', sa.Column('admission_destination_id', sa.Integer(), nullable=True))
    op.add_column('encounter', sa.Column('admission_destination_display', sa.String(), nullable=True))
    op.add_column('encounter', sa.Column('admission_discharge_disposition_system', sa.String(), nullable=True))
    op.add_column('encounter', sa.Column('admission_discharge_disposition_code', sa.String(), nullable=True))
    op.add_column('encounter', sa.Column('admission_discharge_disposition_display', sa.String(), nullable=True))
    op.add_column('encounter', sa.Column('admission_discharge_disposition_text', sa.String(), nullable=True))

    op.drop_column('encounter', 'class_system')
    op.drop_column('encounter', 'class_version')
    op.drop_column('encounter', 'class_code')
    op.drop_column('encounter', 'class_display')
    op.drop_column('encounter', 'service_type_system')
    op.drop_column('encounter', 'service_type_code')
    op.drop_column('encounter', 'service_type_display')
    op.drop_column('encounter', 'service_type_text')
    op.drop_column('encounter', 'period_start')
    op.drop_column('encounter', 'period_end')
    op.drop_column('encounter', 'hosp_pre_admission_identifier_system')
    op.drop_column('encounter', 'hosp_pre_admission_identifier_value')
    op.drop_column('encounter', 'hosp_origin_type')
    op.drop_column('encounter', 'hosp_origin_id')
    op.drop_column('encounter', 'hosp_origin_display')
    op.drop_column('encounter', 'hosp_admit_source_system')
    op.drop_column('encounter', 'hosp_admit_source_code')
    op.drop_column('encounter', 'hosp_admit_source_display')
    op.drop_column('encounter', 'hosp_admit_source_text')
    op.drop_column('encounter', 'hosp_re_admission_system')
    op.drop_column('encounter', 'hosp_re_admission_code')
    op.drop_column('encounter', 'hosp_re_admission_display')
    op.drop_column('encounter', 'hosp_re_admission_text')
    op.drop_column('encounter', 'hosp_destination_type')
    op.drop_column('encounter', 'hosp_destination_id')
    op.drop_column('encounter', 'hosp_destination_display')
    op.drop_column('encounter', 'hosp_discharge_disposition_system')
    op.drop_column('encounter', 'hosp_discharge_disposition_code')
    op.drop_column('encounter', 'hosp_discharge_disposition_display')
    op.drop_column('encounter', 'hosp_discharge_disposition_text')

    # encounter_location: rename physicalType → form
    op.add_column('encounter_location', sa.Column('form_system', sa.String(), nullable=True))
    op.add_column('encounter_location', sa.Column('form_code', sa.String(), nullable=True))
    op.add_column('encounter_location', sa.Column('form_display', sa.String(), nullable=True))
    op.add_column('encounter_location', sa.Column('form_text', sa.String(), nullable=True))
    op.drop_column('encounter_location', 'physical_type_system')
    op.drop_column('encounter_location', 'physical_type_code')
    op.drop_column('encounter_location', 'physical_type_display')
    op.drop_column('encounter_location', 'physical_type_text')


def downgrade() -> None:
    # encounter_location: restore physicalType
    op.add_column('encounter_location', sa.Column('physical_type_system', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('encounter_location', sa.Column('physical_type_code', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('encounter_location', sa.Column('physical_type_display', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('encounter_location', sa.Column('physical_type_text', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_column('encounter_location', 'form_system')
    op.drop_column('encounter_location', 'form_code')
    op.drop_column('encounter_location', 'form_display')
    op.drop_column('encounter_location', 'form_text')

    # Restore encounter main table columns
    op.add_column('encounter', sa.Column('class_system', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('encounter', sa.Column('class_version', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('encounter', sa.Column('class_code', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('encounter', sa.Column('class_display', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('encounter', sa.Column('service_type_system', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('encounter', sa.Column('service_type_code', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('encounter', sa.Column('service_type_display', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('encounter', sa.Column('service_type_text', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('encounter', sa.Column('period_start', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
    op.add_column('encounter', sa.Column('period_end', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
    op.add_column('encounter', sa.Column('hosp_pre_admission_identifier_system', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('encounter', sa.Column('hosp_pre_admission_identifier_value', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('encounter', sa.Column('hosp_origin_type', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('encounter', sa.Column('hosp_origin_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('encounter', sa.Column('hosp_origin_display', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('encounter', sa.Column('hosp_admit_source_system', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('encounter', sa.Column('hosp_admit_source_code', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('encounter', sa.Column('hosp_admit_source_display', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('encounter', sa.Column('hosp_admit_source_text', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('encounter', sa.Column('hosp_re_admission_system', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('encounter', sa.Column('hosp_re_admission_code', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('encounter', sa.Column('hosp_re_admission_display', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('encounter', sa.Column('hosp_re_admission_text', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('encounter', sa.Column('hosp_destination_type', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('encounter', sa.Column('hosp_destination_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('encounter', sa.Column('hosp_destination_display', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('encounter', sa.Column('hosp_discharge_disposition_system', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('encounter', sa.Column('hosp_discharge_disposition_code', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('encounter', sa.Column('hosp_discharge_disposition_display', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('encounter', sa.Column('hosp_discharge_disposition_text', sa.VARCHAR(), autoincrement=False, nullable=True))

    op.drop_column('encounter', 'admission_discharge_disposition_text')
    op.drop_column('encounter', 'admission_discharge_disposition_display')
    op.drop_column('encounter', 'admission_discharge_disposition_code')
    op.drop_column('encounter', 'admission_discharge_disposition_system')
    op.drop_column('encounter', 'admission_destination_display')
    op.drop_column('encounter', 'admission_destination_id')
    op.drop_column('encounter', 'admission_destination_type')
    op.drop_column('encounter', 'admission_re_admission_text')
    op.drop_column('encounter', 'admission_re_admission_display')
    op.drop_column('encounter', 'admission_re_admission_code')
    op.drop_column('encounter', 'admission_re_admission_system')
    op.drop_column('encounter', 'admission_admit_source_text')
    op.drop_column('encounter', 'admission_admit_source_display')
    op.drop_column('encounter', 'admission_admit_source_code')
    op.drop_column('encounter', 'admission_admit_source_system')
    op.drop_column('encounter', 'admission_origin_display')
    op.drop_column('encounter', 'admission_origin_id')
    op.drop_column('encounter', 'admission_origin_type')
    op.drop_column('encounter', 'admission_pre_admission_identifier_value')
    op.drop_column('encounter', 'admission_pre_admission_identifier_system')
    op.drop_column('encounter', 'planned_end_date')
    op.drop_column('encounter', 'planned_start_date')
    op.drop_column('encounter', 'actual_period_end')
    op.drop_column('encounter', 'actual_period_start')
    op.drop_column('encounter', 'subject_status_text')
    op.drop_column('encounter', 'subject_status_display')
    op.drop_column('encounter', 'subject_status_code')
    op.drop_column('encounter', 'subject_status_system')

    # Restore old tables
    op.create_table(
        'encounter_reason_code',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('encounter_id', sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column('org_id', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column('coding_system', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column('coding_code', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column('coding_display', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column('text', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(['encounter_id'], ['encounter.id'], name=op.f('encounter_reason_code_encounter_id_fkey')),
        sa.PrimaryKeyConstraint('id', name=op.f('encounter_reason_code_pkey')),
    )
    op.create_index(op.f('ix_encounter_reason_code_encounter_id'), 'encounter_reason_code', ['encounter_id'], unique=False)

    op.create_table(
        'encounter_reason_reference',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('encounter_id', sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column('org_id', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column('reference_type', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column('reference_id', sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column('reference_display', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(['encounter_id'], ['encounter.id'], name=op.f('encounter_reason_reference_encounter_id_fkey')),
        sa.PrimaryKeyConstraint('id', name=op.f('encounter_reason_reference_pkey')),
    )
    op.create_index(op.f('ix_encounter_reason_reference_encounter_id'), 'encounter_reason_reference', ['encounter_id'], unique=False)

    op.create_table(
        'encounter_hosp_diet_preference',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('encounter_id', sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column('org_id', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column('coding_system', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column('coding_code', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column('coding_display', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column('text', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(['encounter_id'], ['encounter.id'], name=op.f('encounter_hosp_diet_preference_encounter_id_fkey')),
        sa.PrimaryKeyConstraint('id', name=op.f('encounter_hosp_diet_preference_pkey')),
    )
    op.create_index(op.f('ix_encounter_hosp_diet_preference_encounter_id'), 'encounter_hosp_diet_preference', ['encounter_id'], unique=False)

    op.create_table(
        'encounter_hosp_special_arrangement',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('encounter_id', sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column('org_id', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column('coding_system', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column('coding_code', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column('coding_display', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column('text', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(['encounter_id'], ['encounter.id'], name=op.f('encounter_hosp_special_arrangement_encounter_id_fkey')),
        sa.PrimaryKeyConstraint('id', name=op.f('encounter_hosp_special_arrangement_pkey')),
    )
    op.create_index(op.f('ix_encounter_hosp_special_arrangement_encounter_id'), 'encounter_hosp_special_arrangement', ['encounter_id'], unique=False)

    op.create_table(
        'encounter_hosp_special_courtesy',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('encounter_id', sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column('org_id', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column('coding_system', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column('coding_code', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column('coding_display', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column('text', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(['encounter_id'], ['encounter.id'], name=op.f('encounter_hosp_special_courtesy_encounter_id_fkey')),
        sa.PrimaryKeyConstraint('id', name=op.f('encounter_hosp_special_courtesy_pkey')),
    )
    op.create_index(op.f('ix_encounter_hosp_special_courtesy_encounter_id'), 'encounter_hosp_special_courtesy', ['encounter_id'], unique=False)

    # Drop new grandchild tables
    op.drop_index(op.f('ix_encounter_reason_value_reason_id'), table_name='encounter_reason_value')
    op.drop_table('encounter_reason_value')
    op.drop_index(op.f('ix_encounter_reason_use_reason_id'), table_name='encounter_reason_use')
    op.drop_table('encounter_reason_use')
    op.drop_index(op.f('ix_encounter_reason_encounter_id'), table_name='encounter_reason')
    op.drop_table('encounter_reason')
    op.drop_index(op.f('ix_encounter_diagnosis_use_diagnosis_id'), table_name='encounter_diagnosis_use')
    op.drop_table('encounter_diagnosis_use')
    op.drop_index(op.f('ix_encounter_diagnosis_condition_diagnosis_id'), table_name='encounter_diagnosis_condition')
    op.drop_table('encounter_diagnosis_condition')
    op.drop_index(op.f('ix_encounter_service_type_encounter_id'), table_name='encounter_service_type')
    op.drop_table('encounter_service_type')
    op.drop_index(op.f('ix_encounter_virtual_service_encounter_id'), table_name='encounter_virtual_service')
    op.drop_table('encounter_virtual_service')
    op.drop_index(op.f('ix_encounter_special_courtesy_encounter_id'), table_name='encounter_special_courtesy')
    op.drop_table('encounter_special_courtesy')
    op.drop_index(op.f('ix_encounter_special_arrangement_encounter_id'), table_name='encounter_special_arrangement')
    op.drop_table('encounter_special_arrangement')
    op.drop_index(op.f('ix_encounter_diet_preference_encounter_id'), table_name='encounter_diet_preference')
    op.drop_table('encounter_diet_preference')
    op.drop_index(op.f('ix_encounter_class_encounter_id'), table_name='encounter_class')
    op.drop_table('encounter_class')
    op.drop_index(op.f('ix_encounter_care_team_encounter_id'), table_name='encounter_care_team')
    op.drop_table('encounter_care_team')
    op.drop_index(op.f('ix_encounter_business_status_encounter_id'), table_name='encounter_business_status')
    op.drop_table('encounter_business_status')

    # Restore encounter_participant old columns
    op.drop_column('encounter_participant', 'actor_display')
    op.drop_column('encounter_participant', 'actor_id')
    op.drop_column('encounter_participant', 'actor_type')
    op.execute('DROP TYPE IF EXISTS encounter_participant_reference_type')
    op.execute(
        "CREATE TYPE encounter_participant_reference_type AS ENUM "
        "('PRACTITIONER', 'PRACTITIONER_ROLE', 'RELATED_PERSON')"
    )
    op.add_column(
        'encounter_participant',
        sa.Column(
            'individual_type',
            postgresql.ENUM('PRACTITIONER', 'PRACTITIONER_ROLE', 'RELATED_PERSON', name='encounter_participant_reference_type', create_type=False),
            autoincrement=False, nullable=True,
        ),
    )
    op.add_column('encounter_participant', sa.Column('individual_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('encounter_participant', sa.Column('individual_display', sa.VARCHAR(), autoincrement=False, nullable=True))

    # Restore encounter_diagnosis old columns
    op.execute('DROP TYPE IF EXISTS encounter_diagnosis_condition_type')
    op.execute(
        "CREATE TYPE encounter_diagnosis_condition_type AS ENUM "
        "('CONDITION', 'PROCEDURE')"
    )
    op.add_column(
        'encounter_diagnosis',
        sa.Column(
            'condition_type',
            postgresql.ENUM('CONDITION', 'PROCEDURE', name='encounter_diagnosis_condition_type', create_type=False),
            autoincrement=False, nullable=True,
        ),
    )
    op.add_column('encounter_diagnosis', sa.Column('condition_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('encounter_diagnosis', sa.Column('condition_display', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('encounter_diagnosis', sa.Column('rank', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('encounter_diagnosis', sa.Column('use_system', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('encounter_diagnosis', sa.Column('use_code', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('encounter_diagnosis', sa.Column('use_display', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('encounter_diagnosis', sa.Column('use_text', sa.VARCHAR(), autoincrement=False, nullable=True))

    # Drop new enum types
    _encounter_service_type_reference_type.drop(op.get_bind(), checkfirst=True)
    _encounter_reason_value_reference_type.drop(op.get_bind(), checkfirst=True)
