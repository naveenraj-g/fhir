"""add_claim_tables

Revision ID: 1db4549d789f
Revises: 2e2e58149f4f
Create Date: 2026-05-16 12:20:34.839885

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '1db4549d789f'
down_revision: Union[str, None] = '2e2e58149f4f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ── Enum types — all new to this migration ───────────────────────────────────
# organization_reference_type already exists — NOT created/dropped here.

_claim_status = postgresql.ENUM(
    'active', 'cancelled', 'draft', 'entered-in-error',
    name='claim_status',
)
_claim_use = postgresql.ENUM(
    'claim', 'preauthorization', 'predetermination',
    name='claim_use',
)
_claim_patient_ref = postgresql.ENUM(
    'Patient',
    name='claim_patient_ref_type',
)
_claim_enterer_ref = postgresql.ENUM(
    'Practitioner', 'PractitionerRole',
    name='claim_enterer_ref_type',
)
_claim_provider_ref = postgresql.ENUM(
    'Practitioner', 'PractitionerRole', 'Organization',
    name='claim_provider_ref_type',
)
_claim_prescription_ref = postgresql.ENUM(
    'DeviceRequest', 'MedicationRequest', 'VisionPrescription',
    name='claim_prescription_ref_type',
)
_claim_payee_party_ref = postgresql.ENUM(
    'Practitioner', 'PractitionerRole', 'Organization', 'Patient', 'RelatedPerson',
    name='claim_payee_party_ref_type',
)
_claim_referral_ref = postgresql.ENUM(
    'ServiceRequest',
    name='claim_referral_ref_type',
)
_claim_location_ref = postgresql.ENUM(
    'Location',
    name='claim_location_ref_type',
)
_claim_related_claim_ref = postgresql.ENUM(
    'Claim',
    name='claim_related_claim_ref_type',
)
_claim_diagnosis_condition_ref = postgresql.ENUM(
    'Condition',
    name='claim_diagnosis_condition_ref_type',
)
_claim_procedure_ref = postgresql.ENUM(
    'Procedure',
    name='claim_procedure_ref_type',
)
_claim_device_ref = postgresql.ENUM(
    'Device',
    name='claim_device_ref_type',
)
_claim_insurance_coverage_ref = postgresql.ENUM(
    'Coverage',
    name='claim_insurance_coverage_ref_type',
)
_claim_insurance_claim_response_ref = postgresql.ENUM(
    'ClaimResponse',
    name='claim_insurance_claim_response_ref_type',
)
_claim_item_encounter_ref = postgresql.ENUM(
    'Encounter',
    name='claim_item_encounter_ref_type',
)


def upgrade() -> None:
    bind = op.get_bind()

    # Create sequence (autogenerate omits this)
    op.execute(
        "CREATE SEQUENCE IF NOT EXISTS claim_id_seq START WITH 170000 INCREMENT BY 1"
    )

    # Create all new enum types
    _claim_status.create(bind, checkfirst=True)
    _claim_use.create(bind, checkfirst=True)
    _claim_patient_ref.create(bind, checkfirst=True)
    _claim_enterer_ref.create(bind, checkfirst=True)
    _claim_provider_ref.create(bind, checkfirst=True)
    _claim_prescription_ref.create(bind, checkfirst=True)
    _claim_payee_party_ref.create(bind, checkfirst=True)
    _claim_referral_ref.create(bind, checkfirst=True)
    _claim_location_ref.create(bind, checkfirst=True)
    _claim_related_claim_ref.create(bind, checkfirst=True)
    _claim_diagnosis_condition_ref.create(bind, checkfirst=True)
    _claim_procedure_ref.create(bind, checkfirst=True)
    _claim_device_ref.create(bind, checkfirst=True)
    _claim_insurance_coverage_ref.create(bind, checkfirst=True)
    _claim_insurance_claim_response_ref.create(bind, checkfirst=True)
    _claim_item_encounter_ref.create(bind, checkfirst=True)

    # ── claim (main table) ───────────────────────────────────────────────────
    op.create_table('claim',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('claim_id', sa.Integer(),
                  server_default=sa.text("nextval('claim_id_seq')"), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('status',
                  postgresql.ENUM('active', 'cancelled', 'draft', 'entered-in-error',
                                  name='claim_status', create_type=False),
                  nullable=False),
        sa.Column('type_system', sa.String(), nullable=True),
        sa.Column('type_code', sa.String(), nullable=True),
        sa.Column('type_display', sa.String(), nullable=True),
        sa.Column('type_text', sa.String(), nullable=True),
        sa.Column('sub_type_system', sa.String(), nullable=True),
        sa.Column('sub_type_code', sa.String(), nullable=True),
        sa.Column('sub_type_display', sa.String(), nullable=True),
        sa.Column('sub_type_text', sa.String(), nullable=True),
        sa.Column('use',
                  postgresql.ENUM('claim', 'preauthorization', 'predetermination',
                                  name='claim_use', create_type=False),
                  nullable=False),
        sa.Column('patient_type',
                  postgresql.ENUM('Patient', name='claim_patient_ref_type', create_type=False),
                  nullable=True),
        sa.Column('patient_id', sa.Integer(), nullable=True),
        sa.Column('patient_display', sa.String(), nullable=True),
        sa.Column('billable_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('billable_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created', sa.DateTime(timezone=True), nullable=False),
        sa.Column('enterer_type',
                  postgresql.ENUM('Practitioner', 'PractitionerRole',
                                  name='claim_enterer_ref_type', create_type=False),
                  nullable=True),
        sa.Column('enterer_id', sa.Integer(), nullable=True),
        sa.Column('enterer_display', sa.String(), nullable=True),
        # insurer: shared organization_reference_type — already exists
        sa.Column('insurer_type',
                  postgresql.ENUM('Organization', name='organization_reference_type',
                                  create_type=False),
                  nullable=True),
        sa.Column('insurer_id', sa.Integer(), nullable=True),
        sa.Column('insurer_display', sa.String(), nullable=True),
        sa.Column('provider_type',
                  postgresql.ENUM('Practitioner', 'PractitionerRole', 'Organization',
                                  name='claim_provider_ref_type', create_type=False),
                  nullable=True),
        sa.Column('provider_id', sa.Integer(), nullable=True),
        sa.Column('provider_display', sa.String(), nullable=True),
        sa.Column('priority_system', sa.String(), nullable=True),
        sa.Column('priority_code', sa.String(), nullable=True),
        sa.Column('priority_display', sa.String(), nullable=True),
        sa.Column('priority_text', sa.String(), nullable=True),
        sa.Column('funds_reserve_system', sa.String(), nullable=True),
        sa.Column('funds_reserve_code', sa.String(), nullable=True),
        sa.Column('funds_reserve_display', sa.String(), nullable=True),
        sa.Column('funds_reserve_text', sa.String(), nullable=True),
        sa.Column('prescription_type',
                  postgresql.ENUM('DeviceRequest', 'MedicationRequest', 'VisionPrescription',
                                  name='claim_prescription_ref_type', create_type=False),
                  nullable=True),
        sa.Column('prescription_id', sa.Integer(), nullable=True),
        sa.Column('prescription_display', sa.String(), nullable=True),
        sa.Column('original_prescription_type',
                  postgresql.ENUM('DeviceRequest', 'MedicationRequest', 'VisionPrescription',
                                  name='claim_prescription_ref_type', create_type=False),
                  nullable=True),
        sa.Column('original_prescription_id', sa.Integer(), nullable=True),
        sa.Column('original_prescription_display', sa.String(), nullable=True),
        # payee (flattened BackboneElement)
        sa.Column('payee_type_system', sa.String(), nullable=True),
        sa.Column('payee_type_code', sa.String(), nullable=True),
        sa.Column('payee_type_display', sa.String(), nullable=True),
        sa.Column('payee_type_text', sa.String(), nullable=True),
        sa.Column('payee_party_type',
                  postgresql.ENUM('Practitioner', 'PractitionerRole', 'Organization',
                                  'Patient', 'RelatedPerson',
                                  name='claim_payee_party_ref_type', create_type=False),
                  nullable=True),
        sa.Column('payee_party_id', sa.Integer(), nullable=True),
        sa.Column('payee_party_display', sa.String(), nullable=True),
        sa.Column('referral_type',
                  postgresql.ENUM('ServiceRequest', name='claim_referral_ref_type',
                                  create_type=False),
                  nullable=True),
        sa.Column('referral_id', sa.Integer(), nullable=True),
        sa.Column('referral_display', sa.String(), nullable=True),
        sa.Column('facility_type',
                  postgresql.ENUM('Location', name='claim_location_ref_type', create_type=False),
                  nullable=True),
        sa.Column('facility_id', sa.Integer(), nullable=True),
        sa.Column('facility_display', sa.String(), nullable=True),
        # accident (flattened BackboneElement)
        sa.Column('accident_date', sa.Date(), nullable=True),
        sa.Column('accident_type_system', sa.String(), nullable=True),
        sa.Column('accident_type_code', sa.String(), nullable=True),
        sa.Column('accident_type_display', sa.String(), nullable=True),
        sa.Column('accident_type_text', sa.String(), nullable=True),
        sa.Column('accident_location_address_use', sa.String(), nullable=True),
        sa.Column('accident_location_address_type', sa.String(), nullable=True),
        sa.Column('accident_location_address_text', sa.String(), nullable=True),
        sa.Column('accident_location_address_line', sa.Text(), nullable=True),
        sa.Column('accident_location_address_city', sa.String(), nullable=True),
        sa.Column('accident_location_address_district', sa.String(), nullable=True),
        sa.Column('accident_location_address_state', sa.String(), nullable=True),
        sa.Column('accident_location_address_postal_code', sa.String(), nullable=True),
        sa.Column('accident_location_address_country', sa.String(), nullable=True),
        sa.Column('accident_location_address_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('accident_location_address_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('accident_location_reference_type',
                  postgresql.ENUM('Location', name='claim_location_ref_type', create_type=False),
                  nullable=True),
        sa.Column('accident_location_reference_id', sa.Integer(), nullable=True),
        sa.Column('accident_location_reference_display', sa.String(), nullable=True),
        # total (Money)
        sa.Column('total_value', sa.Numeric(), nullable=True),
        sa.Column('total_currency', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_claim_claim_id'), 'claim', ['claim_id'], unique=True)
    op.create_index(op.f('ix_claim_id'), 'claim', ['id'], unique=False)
    op.create_index(op.f('ix_claim_org_id'), 'claim', ['org_id'], unique=False)
    op.create_index(op.f('ix_claim_user_id'), 'claim', ['user_id'], unique=False)

    # ── claim_identifier ─────────────────────────────────────────────────────
    op.create_table('claim_identifier',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('claim_id', sa.Integer(), nullable=False),
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
        sa.ForeignKeyConstraint(['claim_id'], ['claim.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_claim_identifier_claim_id'), 'claim_identifier', ['claim_id'], unique=False)

    # ── claim_related ─────────────────────────────────────────────────────────
    op.create_table('claim_related',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('claim_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('related_claim_type',
                  postgresql.ENUM('Claim', name='claim_related_claim_ref_type', create_type=False),
                  nullable=True),
        sa.Column('related_claim_id', sa.Integer(), nullable=True),
        sa.Column('related_claim_display', sa.String(), nullable=True),
        sa.Column('relationship_system', sa.String(), nullable=True),
        sa.Column('relationship_code', sa.String(), nullable=True),
        sa.Column('relationship_display', sa.String(), nullable=True),
        sa.Column('relationship_text', sa.String(), nullable=True),
        sa.Column('reference_use', sa.String(), nullable=True),
        sa.Column('reference_type_system', sa.String(), nullable=True),
        sa.Column('reference_type_code', sa.String(), nullable=True),
        sa.Column('reference_type_display', sa.String(), nullable=True),
        sa.Column('reference_type_text', sa.String(), nullable=True),
        sa.Column('reference_system', sa.String(), nullable=True),
        sa.Column('reference_value', sa.String(), nullable=True),
        sa.Column('reference_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reference_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reference_assigner', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['claim_id'], ['claim.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_claim_related_claim_id'), 'claim_related', ['claim_id'], unique=False)

    # ── claim_care_team ───────────────────────────────────────────────────────
    op.create_table('claim_care_team',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('claim_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('sequence', sa.Integer(), nullable=False),
        sa.Column('provider_type',
                  postgresql.ENUM('Practitioner', 'PractitionerRole', 'Organization',
                                  name='claim_provider_ref_type', create_type=False),
                  nullable=True),
        sa.Column('provider_id', sa.Integer(), nullable=True),
        sa.Column('provider_display', sa.String(), nullable=True),
        sa.Column('responsible', sa.Boolean(), nullable=True),
        sa.Column('role_system', sa.String(), nullable=True),
        sa.Column('role_code', sa.String(), nullable=True),
        sa.Column('role_display', sa.String(), nullable=True),
        sa.Column('role_text', sa.String(), nullable=True),
        sa.Column('qualification_system', sa.String(), nullable=True),
        sa.Column('qualification_code', sa.String(), nullable=True),
        sa.Column('qualification_display', sa.String(), nullable=True),
        sa.Column('qualification_text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['claim_id'], ['claim.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_claim_care_team_claim_id'), 'claim_care_team', ['claim_id'], unique=False)

    # ── claim_supporting_info ─────────────────────────────────────────────────
    op.create_table('claim_supporting_info',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('claim_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('sequence', sa.Integer(), nullable=False),
        sa.Column('category_system', sa.String(), nullable=True),
        sa.Column('category_code', sa.String(), nullable=True),
        sa.Column('category_display', sa.String(), nullable=True),
        sa.Column('category_text', sa.String(), nullable=True),
        sa.Column('code_system', sa.String(), nullable=True),
        sa.Column('code_code', sa.String(), nullable=True),
        sa.Column('code_display', sa.String(), nullable=True),
        sa.Column('code_text', sa.String(), nullable=True),
        sa.Column('timing_date', sa.Date(), nullable=True),
        sa.Column('timing_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('timing_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('value_boolean', sa.Boolean(), nullable=True),
        sa.Column('value_string', sa.String(), nullable=True),
        sa.Column('value_quantity_value', sa.Numeric(), nullable=True),
        sa.Column('value_quantity_comparator', sa.String(), nullable=True),
        sa.Column('value_quantity_unit', sa.String(), nullable=True),
        sa.Column('value_quantity_system', sa.String(), nullable=True),
        sa.Column('value_quantity_code', sa.String(), nullable=True),
        sa.Column('value_attachment_content_type', sa.String(), nullable=True),
        sa.Column('value_attachment_language', sa.String(), nullable=True),
        sa.Column('value_attachment_data', sa.Text(), nullable=True),
        sa.Column('value_attachment_url', sa.String(), nullable=True),
        sa.Column('value_attachment_size', sa.Integer(), nullable=True),
        sa.Column('value_attachment_hash', sa.String(), nullable=True),
        sa.Column('value_attachment_title', sa.String(), nullable=True),
        sa.Column('value_attachment_creation', sa.DateTime(timezone=True), nullable=True),
        sa.Column('value_reference_type', sa.String(), nullable=True),
        sa.Column('value_reference_id', sa.Integer(), nullable=True),
        sa.Column('value_reference_display', sa.String(), nullable=True),
        sa.Column('reason_system', sa.String(), nullable=True),
        sa.Column('reason_code', sa.String(), nullable=True),
        sa.Column('reason_display', sa.String(), nullable=True),
        sa.Column('reason_text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['claim_id'], ['claim.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_claim_supporting_info_claim_id'), 'claim_supporting_info', ['claim_id'], unique=False)

    # ── claim_diagnosis ───────────────────────────────────────────────────────
    op.create_table('claim_diagnosis',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('claim_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('sequence', sa.Integer(), nullable=False),
        sa.Column('diagnosis_codeable_concept_system', sa.String(), nullable=True),
        sa.Column('diagnosis_codeable_concept_code', sa.String(), nullable=True),
        sa.Column('diagnosis_codeable_concept_display', sa.String(), nullable=True),
        sa.Column('diagnosis_codeable_concept_text', sa.String(), nullable=True),
        sa.Column('diagnosis_reference_type',
                  postgresql.ENUM('Condition', name='claim_diagnosis_condition_ref_type',
                                  create_type=False),
                  nullable=True),
        sa.Column('diagnosis_reference_id', sa.Integer(), nullable=True),
        sa.Column('diagnosis_reference_display', sa.String(), nullable=True),
        sa.Column('on_admission_system', sa.String(), nullable=True),
        sa.Column('on_admission_code', sa.String(), nullable=True),
        sa.Column('on_admission_display', sa.String(), nullable=True),
        sa.Column('on_admission_text', sa.String(), nullable=True),
        sa.Column('package_code_system', sa.String(), nullable=True),
        sa.Column('package_code_code', sa.String(), nullable=True),
        sa.Column('package_code_display', sa.String(), nullable=True),
        sa.Column('package_code_text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['claim_id'], ['claim.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_claim_diagnosis_claim_id'), 'claim_diagnosis', ['claim_id'], unique=False)

    # ── claim_procedure ───────────────────────────────────────────────────────
    op.create_table('claim_procedure',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('claim_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('sequence', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('procedure_codeable_concept_system', sa.String(), nullable=True),
        sa.Column('procedure_codeable_concept_code', sa.String(), nullable=True),
        sa.Column('procedure_codeable_concept_display', sa.String(), nullable=True),
        sa.Column('procedure_codeable_concept_text', sa.String(), nullable=True),
        sa.Column('procedure_reference_type',
                  postgresql.ENUM('Procedure', name='claim_procedure_ref_type', create_type=False),
                  nullable=True),
        sa.Column('procedure_reference_id', sa.Integer(), nullable=True),
        sa.Column('procedure_reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['claim_id'], ['claim.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_claim_procedure_claim_id'), 'claim_procedure', ['claim_id'], unique=False)

    # ── claim_insurance ───────────────────────────────────────────────────────
    op.create_table('claim_insurance',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('claim_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('sequence', sa.Integer(), nullable=False),
        sa.Column('focal', sa.Boolean(), nullable=False),
        sa.Column('identifier_use', sa.String(), nullable=True),
        sa.Column('identifier_type_system', sa.String(), nullable=True),
        sa.Column('identifier_type_code', sa.String(), nullable=True),
        sa.Column('identifier_type_display', sa.String(), nullable=True),
        sa.Column('identifier_type_text', sa.String(), nullable=True),
        sa.Column('identifier_system', sa.String(), nullable=True),
        sa.Column('identifier_value', sa.String(), nullable=True),
        sa.Column('identifier_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('identifier_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('identifier_assigner', sa.String(), nullable=True),
        sa.Column('coverage_type',
                  postgresql.ENUM('Coverage', name='claim_insurance_coverage_ref_type',
                                  create_type=False),
                  nullable=True),
        sa.Column('coverage_id', sa.Integer(), nullable=True),
        sa.Column('coverage_display', sa.String(), nullable=True),
        sa.Column('business_arrangement', sa.String(), nullable=True),
        sa.Column('claim_response_type',
                  postgresql.ENUM('ClaimResponse', name='claim_insurance_claim_response_ref_type',
                                  create_type=False),
                  nullable=True),
        sa.Column('claim_response_id', sa.Integer(), nullable=True),
        sa.Column('claim_response_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['claim_id'], ['claim.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_claim_insurance_claim_id'), 'claim_insurance', ['claim_id'], unique=False)

    # ── claim_item ────────────────────────────────────────────────────────────
    op.create_table('claim_item',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('claim_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('sequence', sa.Integer(), nullable=False),
        sa.Column('care_team_sequence', sa.Text(), nullable=True),
        sa.Column('diagnosis_sequence', sa.Text(), nullable=True),
        sa.Column('procedure_sequence', sa.Text(), nullable=True),
        sa.Column('information_sequence', sa.Text(), nullable=True),
        sa.Column('revenue_system', sa.String(), nullable=True),
        sa.Column('revenue_code', sa.String(), nullable=True),
        sa.Column('revenue_display', sa.String(), nullable=True),
        sa.Column('revenue_text', sa.String(), nullable=True),
        sa.Column('category_system', sa.String(), nullable=True),
        sa.Column('category_code', sa.String(), nullable=True),
        sa.Column('category_display', sa.String(), nullable=True),
        sa.Column('category_text', sa.String(), nullable=True),
        sa.Column('product_or_service_system', sa.String(), nullable=True),
        sa.Column('product_or_service_code', sa.String(), nullable=True),
        sa.Column('product_or_service_display', sa.String(), nullable=True),
        sa.Column('product_or_service_text', sa.String(), nullable=True),
        sa.Column('serviced_date', sa.Date(), nullable=True),
        sa.Column('serviced_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('serviced_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('location_codeable_concept_system', sa.String(), nullable=True),
        sa.Column('location_codeable_concept_code', sa.String(), nullable=True),
        sa.Column('location_codeable_concept_display', sa.String(), nullable=True),
        sa.Column('location_codeable_concept_text', sa.String(), nullable=True),
        sa.Column('location_address_use', sa.String(), nullable=True),
        sa.Column('location_address_type', sa.String(), nullable=True),
        sa.Column('location_address_text', sa.String(), nullable=True),
        sa.Column('location_address_line', sa.Text(), nullable=True),
        sa.Column('location_address_city', sa.String(), nullable=True),
        sa.Column('location_address_district', sa.String(), nullable=True),
        sa.Column('location_address_state', sa.String(), nullable=True),
        sa.Column('location_address_postal_code', sa.String(), nullable=True),
        sa.Column('location_address_country', sa.String(), nullable=True),
        sa.Column('location_address_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('location_address_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('location_reference_type',
                  postgresql.ENUM('Location', name='claim_location_ref_type', create_type=False),
                  nullable=True),
        sa.Column('location_reference_id', sa.Integer(), nullable=True),
        sa.Column('location_reference_display', sa.String(), nullable=True),
        sa.Column('quantity_value', sa.Numeric(), nullable=True),
        sa.Column('quantity_unit', sa.String(), nullable=True),
        sa.Column('quantity_system', sa.String(), nullable=True),
        sa.Column('quantity_code', sa.String(), nullable=True),
        sa.Column('unit_price_value', sa.Numeric(), nullable=True),
        sa.Column('unit_price_currency', sa.String(), nullable=True),
        sa.Column('factor', sa.Numeric(), nullable=True),
        sa.Column('net_value', sa.Numeric(), nullable=True),
        sa.Column('net_currency', sa.String(), nullable=True),
        sa.Column('body_site_system', sa.String(), nullable=True),
        sa.Column('body_site_code', sa.String(), nullable=True),
        sa.Column('body_site_display', sa.String(), nullable=True),
        sa.Column('body_site_text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['claim_id'], ['claim.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_claim_item_claim_id'), 'claim_item', ['claim_id'], unique=False)

    # ── claim_diagnosis_type ──────────────────────────────────────────────────
    op.create_table('claim_diagnosis_type',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('diagnosis_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['diagnosis_id'], ['claim_diagnosis.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_claim_diagnosis_type_diagnosis_id'), 'claim_diagnosis_type', ['diagnosis_id'], unique=False)

    # ── claim_procedure_type ──────────────────────────────────────────────────
    op.create_table('claim_procedure_type',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('procedure_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['procedure_id'], ['claim_procedure.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_claim_procedure_type_procedure_id'), 'claim_procedure_type', ['procedure_id'], unique=False)

    # ── claim_procedure_udi ───────────────────────────────────────────────────
    op.create_table('claim_procedure_udi',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('procedure_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('reference_type',
                  postgresql.ENUM('Device', name='claim_device_ref_type', create_type=False),
                  nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['procedure_id'], ['claim_procedure.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_claim_procedure_udi_procedure_id'), 'claim_procedure_udi', ['procedure_id'], unique=False)

    # ── claim_insurance_pre_auth_ref ──────────────────────────────────────────
    op.create_table('claim_insurance_pre_auth_ref',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('insurance_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('value', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['insurance_id'], ['claim_insurance.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_claim_insurance_pre_auth_ref_insurance_id'), 'claim_insurance_pre_auth_ref', ['insurance_id'], unique=False)

    # ── claim_item_modifier ───────────────────────────────────────────────────
    op.create_table('claim_item_modifier',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['item_id'], ['claim_item.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_claim_item_modifier_item_id'), 'claim_item_modifier', ['item_id'], unique=False)

    # ── claim_item_program_code ───────────────────────────────────────────────
    op.create_table('claim_item_program_code',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['item_id'], ['claim_item.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_claim_item_program_code_item_id'), 'claim_item_program_code', ['item_id'], unique=False)

    # ── claim_item_udi ────────────────────────────────────────────────────────
    op.create_table('claim_item_udi',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('reference_type',
                  postgresql.ENUM('Device', name='claim_device_ref_type', create_type=False),
                  nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['item_id'], ['claim_item.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_claim_item_udi_item_id'), 'claim_item_udi', ['item_id'], unique=False)

    # ── claim_item_sub_site ───────────────────────────────────────────────────
    op.create_table('claim_item_sub_site',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['item_id'], ['claim_item.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_claim_item_sub_site_item_id'), 'claim_item_sub_site', ['item_id'], unique=False)

    # ── claim_item_encounter ──────────────────────────────────────────────────
    op.create_table('claim_item_encounter',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('reference_type',
                  postgresql.ENUM('Encounter', name='claim_item_encounter_ref_type',
                                  create_type=False),
                  nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['item_id'], ['claim_item.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_claim_item_encounter_item_id'), 'claim_item_encounter', ['item_id'], unique=False)

    # ── claim_item_detail ─────────────────────────────────────────────────────
    op.create_table('claim_item_detail',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('sequence', sa.Integer(), nullable=False),
        sa.Column('revenue_system', sa.String(), nullable=True),
        sa.Column('revenue_code', sa.String(), nullable=True),
        sa.Column('revenue_display', sa.String(), nullable=True),
        sa.Column('revenue_text', sa.String(), nullable=True),
        sa.Column('category_system', sa.String(), nullable=True),
        sa.Column('category_code', sa.String(), nullable=True),
        sa.Column('category_display', sa.String(), nullable=True),
        sa.Column('category_text', sa.String(), nullable=True),
        sa.Column('product_or_service_system', sa.String(), nullable=True),
        sa.Column('product_or_service_code', sa.String(), nullable=True),
        sa.Column('product_or_service_display', sa.String(), nullable=True),
        sa.Column('product_or_service_text', sa.String(), nullable=True),
        sa.Column('quantity_value', sa.Numeric(), nullable=True),
        sa.Column('quantity_unit', sa.String(), nullable=True),
        sa.Column('quantity_system', sa.String(), nullable=True),
        sa.Column('quantity_code', sa.String(), nullable=True),
        sa.Column('unit_price_value', sa.Numeric(), nullable=True),
        sa.Column('unit_price_currency', sa.String(), nullable=True),
        sa.Column('factor', sa.Numeric(), nullable=True),
        sa.Column('net_value', sa.Numeric(), nullable=True),
        sa.Column('net_currency', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['item_id'], ['claim_item.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_claim_item_detail_item_id'), 'claim_item_detail', ['item_id'], unique=False)

    # ── claim_item_detail_modifier ────────────────────────────────────────────
    op.create_table('claim_item_detail_modifier',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('detail_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['detail_id'], ['claim_item_detail.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_claim_item_detail_modifier_detail_id'), 'claim_item_detail_modifier', ['detail_id'], unique=False)

    # ── claim_item_detail_program_code ────────────────────────────────────────
    op.create_table('claim_item_detail_program_code',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('detail_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['detail_id'], ['claim_item_detail.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_claim_item_detail_program_code_detail_id'), 'claim_item_detail_program_code', ['detail_id'], unique=False)

    # ── claim_item_detail_udi ─────────────────────────────────────────────────
    op.create_table('claim_item_detail_udi',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('detail_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('reference_type',
                  postgresql.ENUM('Device', name='claim_device_ref_type', create_type=False),
                  nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['detail_id'], ['claim_item_detail.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_claim_item_detail_udi_detail_id'), 'claim_item_detail_udi', ['detail_id'], unique=False)

    # ── claim_item_detail_sub_detail ──────────────────────────────────────────
    op.create_table('claim_item_detail_sub_detail',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('detail_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('sequence', sa.Integer(), nullable=False),
        sa.Column('revenue_system', sa.String(), nullable=True),
        sa.Column('revenue_code', sa.String(), nullable=True),
        sa.Column('revenue_display', sa.String(), nullable=True),
        sa.Column('revenue_text', sa.String(), nullable=True),
        sa.Column('category_system', sa.String(), nullable=True),
        sa.Column('category_code', sa.String(), nullable=True),
        sa.Column('category_display', sa.String(), nullable=True),
        sa.Column('category_text', sa.String(), nullable=True),
        sa.Column('product_or_service_system', sa.String(), nullable=True),
        sa.Column('product_or_service_code', sa.String(), nullable=True),
        sa.Column('product_or_service_display', sa.String(), nullable=True),
        sa.Column('product_or_service_text', sa.String(), nullable=True),
        sa.Column('quantity_value', sa.Numeric(), nullable=True),
        sa.Column('quantity_unit', sa.String(), nullable=True),
        sa.Column('quantity_system', sa.String(), nullable=True),
        sa.Column('quantity_code', sa.String(), nullable=True),
        sa.Column('unit_price_value', sa.Numeric(), nullable=True),
        sa.Column('unit_price_currency', sa.String(), nullable=True),
        sa.Column('factor', sa.Numeric(), nullable=True),
        sa.Column('net_value', sa.Numeric(), nullable=True),
        sa.Column('net_currency', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['detail_id'], ['claim_item_detail.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_claim_item_detail_sub_detail_detail_id'), 'claim_item_detail_sub_detail', ['detail_id'], unique=False)

    # ── claim_item_detail_sub_detail_modifier ─────────────────────────────────
    op.create_table('claim_item_detail_sub_detail_modifier',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('sub_detail_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['sub_detail_id'], ['claim_item_detail_sub_detail.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_claim_item_detail_sub_detail_modifier_sub_detail_id'), 'claim_item_detail_sub_detail_modifier', ['sub_detail_id'], unique=False)

    # ── claim_item_detail_sub_detail_program_code ─────────────────────────────
    op.create_table('claim_item_detail_sub_detail_program_code',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('sub_detail_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['sub_detail_id'], ['claim_item_detail_sub_detail.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_claim_item_detail_sub_detail_program_code_sub_detail_id'), 'claim_item_detail_sub_detail_program_code', ['sub_detail_id'], unique=False)

    # ── claim_item_detail_sub_detail_udi ──────────────────────────────────────
    op.create_table('claim_item_detail_sub_detail_udi',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('sub_detail_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('reference_type',
                  postgresql.ENUM('Device', name='claim_device_ref_type', create_type=False),
                  nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['sub_detail_id'], ['claim_item_detail_sub_detail.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_claim_item_detail_sub_detail_udi_sub_detail_id'), 'claim_item_detail_sub_detail_udi', ['sub_detail_id'], unique=False)


def downgrade() -> None:
    bind = op.get_bind()

    # Drop in reverse dependency order
    op.drop_index(op.f('ix_claim_item_detail_sub_detail_udi_sub_detail_id'), table_name='claim_item_detail_sub_detail_udi')
    op.drop_table('claim_item_detail_sub_detail_udi')
    op.drop_index(op.f('ix_claim_item_detail_sub_detail_program_code_sub_detail_id'), table_name='claim_item_detail_sub_detail_program_code')
    op.drop_table('claim_item_detail_sub_detail_program_code')
    op.drop_index(op.f('ix_claim_item_detail_sub_detail_modifier_sub_detail_id'), table_name='claim_item_detail_sub_detail_modifier')
    op.drop_table('claim_item_detail_sub_detail_modifier')
    op.drop_index(op.f('ix_claim_item_detail_sub_detail_detail_id'), table_name='claim_item_detail_sub_detail')
    op.drop_table('claim_item_detail_sub_detail')
    op.drop_index(op.f('ix_claim_item_detail_udi_detail_id'), table_name='claim_item_detail_udi')
    op.drop_table('claim_item_detail_udi')
    op.drop_index(op.f('ix_claim_item_detail_program_code_detail_id'), table_name='claim_item_detail_program_code')
    op.drop_table('claim_item_detail_program_code')
    op.drop_index(op.f('ix_claim_item_detail_modifier_detail_id'), table_name='claim_item_detail_modifier')
    op.drop_table('claim_item_detail_modifier')
    op.drop_index(op.f('ix_claim_item_detail_item_id'), table_name='claim_item_detail')
    op.drop_table('claim_item_detail')
    op.drop_index(op.f('ix_claim_item_encounter_item_id'), table_name='claim_item_encounter')
    op.drop_table('claim_item_encounter')
    op.drop_index(op.f('ix_claim_item_sub_site_item_id'), table_name='claim_item_sub_site')
    op.drop_table('claim_item_sub_site')
    op.drop_index(op.f('ix_claim_item_udi_item_id'), table_name='claim_item_udi')
    op.drop_table('claim_item_udi')
    op.drop_index(op.f('ix_claim_item_program_code_item_id'), table_name='claim_item_program_code')
    op.drop_table('claim_item_program_code')
    op.drop_index(op.f('ix_claim_item_modifier_item_id'), table_name='claim_item_modifier')
    op.drop_table('claim_item_modifier')
    op.drop_index(op.f('ix_claim_item_claim_id'), table_name='claim_item')
    op.drop_table('claim_item')
    op.drop_index(op.f('ix_claim_insurance_pre_auth_ref_insurance_id'), table_name='claim_insurance_pre_auth_ref')
    op.drop_table('claim_insurance_pre_auth_ref')
    op.drop_index(op.f('ix_claim_insurance_claim_id'), table_name='claim_insurance')
    op.drop_table('claim_insurance')
    op.drop_index(op.f('ix_claim_procedure_udi_procedure_id'), table_name='claim_procedure_udi')
    op.drop_table('claim_procedure_udi')
    op.drop_index(op.f('ix_claim_procedure_type_procedure_id'), table_name='claim_procedure_type')
    op.drop_table('claim_procedure_type')
    op.drop_index(op.f('ix_claim_procedure_claim_id'), table_name='claim_procedure')
    op.drop_table('claim_procedure')
    op.drop_index(op.f('ix_claim_diagnosis_type_diagnosis_id'), table_name='claim_diagnosis_type')
    op.drop_table('claim_diagnosis_type')
    op.drop_index(op.f('ix_claim_diagnosis_claim_id'), table_name='claim_diagnosis')
    op.drop_table('claim_diagnosis')
    op.drop_index(op.f('ix_claim_supporting_info_claim_id'), table_name='claim_supporting_info')
    op.drop_table('claim_supporting_info')
    op.drop_index(op.f('ix_claim_care_team_claim_id'), table_name='claim_care_team')
    op.drop_table('claim_care_team')
    op.drop_index(op.f('ix_claim_related_claim_id'), table_name='claim_related')
    op.drop_table('claim_related')
    op.drop_index(op.f('ix_claim_identifier_claim_id'), table_name='claim_identifier')
    op.drop_table('claim_identifier')
    op.drop_index(op.f('ix_claim_user_id'), table_name='claim')
    op.drop_index(op.f('ix_claim_org_id'), table_name='claim')
    op.drop_index(op.f('ix_claim_id'), table_name='claim')
    op.drop_index(op.f('ix_claim_claim_id'), table_name='claim')
    op.drop_table('claim')

    op.execute("DROP SEQUENCE IF EXISTS claim_id_seq")

    # Drop enum types (reverse creation order; organization_reference_type is shared — do NOT drop)
    _claim_item_encounter_ref.drop(bind, checkfirst=True)
    _claim_insurance_claim_response_ref.drop(bind, checkfirst=True)
    _claim_insurance_coverage_ref.drop(bind, checkfirst=True)
    _claim_device_ref.drop(bind, checkfirst=True)
    _claim_procedure_ref.drop(bind, checkfirst=True)
    _claim_diagnosis_condition_ref.drop(bind, checkfirst=True)
    _claim_related_claim_ref.drop(bind, checkfirst=True)
    _claim_location_ref.drop(bind, checkfirst=True)
    _claim_referral_ref.drop(bind, checkfirst=True)
    _claim_payee_party_ref.drop(bind, checkfirst=True)
    _claim_prescription_ref.drop(bind, checkfirst=True)
    _claim_provider_ref.drop(bind, checkfirst=True)
    _claim_enterer_ref.drop(bind, checkfirst=True)
    _claim_patient_ref.drop(bind, checkfirst=True)
    _claim_use.drop(bind, checkfirst=True)
    _claim_status.drop(bind, checkfirst=True)
