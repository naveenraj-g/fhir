"""add_claim_response_tables

Revision ID: fe8491c09f90
Revises: 1db4549d789f
Create Date: 2026-05-16 13:34:39.258628

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'fe8491c09f90'
down_revision: Union[str, None] = '1db4549d789f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ---------------------------------------------------------------------------
# Enum type definitions (module-level so downgrade() can drop them)
# organization_reference_type is a shared type — never create/drop here
# ---------------------------------------------------------------------------
_status_enum = postgresql.ENUM('active', 'cancelled', 'draft', 'entered-in-error', name='claim_response_status')
_use_enum = postgresql.ENUM('claim', 'preauthorization', 'predetermination', name='claim_response_use')
_outcome_enum = postgresql.ENUM('queued', 'complete', 'error', 'partial', name='claim_response_outcome')
_patient_ref_enum = postgresql.ENUM('Patient', name='claim_response_patient_ref_type')
_requestor_ref_enum = postgresql.ENUM('Practitioner', 'PractitionerRole', 'Organization', name='claim_response_requestor_ref_type')
_request_ref_enum = postgresql.ENUM('Claim', name='claim_response_request_ref_type')
_add_item_location_ref_enum = postgresql.ENUM('Location', name='claim_response_add_item_location_ref_type')
_add_item_provider_ref_enum = postgresql.ENUM('Practitioner', 'PractitionerRole', 'Organization', name='claim_response_add_item_provider_ref_type')
_insurance_coverage_ref_enum = postgresql.ENUM('Coverage', name='claim_response_insurance_coverage_ref_type')
_insurance_cr_ref_enum = postgresql.ENUM('ClaimResponse', name='claim_response_insurance_cr_ref_type')
_comm_req_ref_enum = postgresql.ENUM('CommunicationRequest', name='claim_response_comm_req_ref_type')


def upgrade() -> None:
    bind = op.get_bind()

    # Sequence for claim_response_id
    op.execute("CREATE SEQUENCE IF NOT EXISTS claim_response_id_seq START WITH 180000 INCREMENT BY 1")

    # Create all new enum types
    _status_enum.create(bind, checkfirst=True)
    _use_enum.create(bind, checkfirst=True)
    _outcome_enum.create(bind, checkfirst=True)
    _patient_ref_enum.create(bind, checkfirst=True)
    _requestor_ref_enum.create(bind, checkfirst=True)
    _request_ref_enum.create(bind, checkfirst=True)
    _add_item_location_ref_enum.create(bind, checkfirst=True)
    _add_item_provider_ref_enum.create(bind, checkfirst=True)
    _insurance_coverage_ref_enum.create(bind, checkfirst=True)
    _insurance_cr_ref_enum.create(bind, checkfirst=True)
    _comm_req_ref_enum.create(bind, checkfirst=True)

    # Main table
    op.create_table('claim_response',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('claim_response_id', sa.Integer(), server_default=sa.text("nextval('claim_response_id_seq')"), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_by', sa.String(), nullable=True),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('status', postgresql.ENUM('active', 'cancelled', 'draft', 'entered-in-error', name='claim_response_status', create_type=False), nullable=False),
    sa.Column('type_system', sa.String(), nullable=True),
    sa.Column('type_code', sa.String(), nullable=True),
    sa.Column('type_display', sa.String(), nullable=True),
    sa.Column('type_text', sa.String(), nullable=True),
    sa.Column('sub_type_system', sa.String(), nullable=True),
    sa.Column('sub_type_code', sa.String(), nullable=True),
    sa.Column('sub_type_display', sa.String(), nullable=True),
    sa.Column('sub_type_text', sa.String(), nullable=True),
    sa.Column('use', postgresql.ENUM('claim', 'preauthorization', 'predetermination', name='claim_response_use', create_type=False), nullable=False),
    sa.Column('patient_type', postgresql.ENUM('Patient', name='claim_response_patient_ref_type', create_type=False), nullable=True),
    sa.Column('patient_id', sa.Integer(), nullable=True),
    sa.Column('patient_display', sa.String(), nullable=True),
    sa.Column('created', sa.DateTime(timezone=True), nullable=False),
    sa.Column('insurer_type', postgresql.ENUM('Organization', name='organization_reference_type', create_type=False), nullable=True),
    sa.Column('insurer_id', sa.Integer(), nullable=True),
    sa.Column('insurer_display', sa.String(), nullable=True),
    sa.Column('requestor_type', postgresql.ENUM('Practitioner', 'PractitionerRole', 'Organization', name='claim_response_requestor_ref_type', create_type=False), nullable=True),
    sa.Column('requestor_id', sa.Integer(), nullable=True),
    sa.Column('requestor_display', sa.String(), nullable=True),
    sa.Column('request_type', postgresql.ENUM('Claim', name='claim_response_request_ref_type', create_type=False), nullable=True),
    sa.Column('request_id', sa.Integer(), nullable=True),
    sa.Column('request_display', sa.String(), nullable=True),
    sa.Column('outcome', postgresql.ENUM('queued', 'complete', 'error', 'partial', name='claim_response_outcome', create_type=False), nullable=False),
    sa.Column('disposition', sa.String(), nullable=True),
    sa.Column('pre_auth_ref', sa.String(), nullable=True),
    sa.Column('pre_auth_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('pre_auth_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('payee_type_system', sa.String(), nullable=True),
    sa.Column('payee_type_code', sa.String(), nullable=True),
    sa.Column('payee_type_display', sa.String(), nullable=True),
    sa.Column('payee_type_text', sa.String(), nullable=True),
    sa.Column('payment_type_system', sa.String(), nullable=True),
    sa.Column('payment_type_code', sa.String(), nullable=True),
    sa.Column('payment_type_display', sa.String(), nullable=True),
    sa.Column('payment_type_text', sa.String(), nullable=True),
    sa.Column('payment_adjustment_value', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('payment_adjustment_currency', sa.String(length=3), nullable=True),
    sa.Column('payment_adjustment_reason_system', sa.String(), nullable=True),
    sa.Column('payment_adjustment_reason_code', sa.String(), nullable=True),
    sa.Column('payment_adjustment_reason_display', sa.String(), nullable=True),
    sa.Column('payment_adjustment_reason_text', sa.String(), nullable=True),
    sa.Column('payment_date', sa.Date(), nullable=True),
    sa.Column('payment_amount_value', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('payment_amount_currency', sa.String(length=3), nullable=True),
    sa.Column('payment_identifier_use', sa.String(), nullable=True),
    sa.Column('payment_identifier_type_system', sa.String(), nullable=True),
    sa.Column('payment_identifier_type_code', sa.String(), nullable=True),
    sa.Column('payment_identifier_type_display', sa.String(), nullable=True),
    sa.Column('payment_identifier_type_text', sa.String(), nullable=True),
    sa.Column('payment_identifier_system', sa.String(), nullable=True),
    sa.Column('payment_identifier_value', sa.String(), nullable=True),
    sa.Column('payment_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('payment_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('payment_identifier_assigner', sa.String(), nullable=True),
    sa.Column('funds_reserve_system', sa.String(), nullable=True),
    sa.Column('funds_reserve_code', sa.String(), nullable=True),
    sa.Column('funds_reserve_display', sa.String(), nullable=True),
    sa.Column('funds_reserve_text', sa.String(), nullable=True),
    sa.Column('form_code_system', sa.String(), nullable=True),
    sa.Column('form_code_code', sa.String(), nullable=True),
    sa.Column('form_code_display', sa.String(), nullable=True),
    sa.Column('form_code_text', sa.String(), nullable=True),
    sa.Column('form_content_type', sa.String(), nullable=True),
    sa.Column('form_language', sa.String(), nullable=True),
    sa.Column('form_data', sa.Text(), nullable=True),
    sa.Column('form_url', sa.String(), nullable=True),
    sa.Column('form_size', sa.Integer(), nullable=True),
    sa.Column('form_hash', sa.Text(), nullable=True),
    sa.Column('form_title', sa.String(), nullable=True),
    sa.Column('form_creation', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_claim_response_claim_response_id'), 'claim_response', ['claim_response_id'], unique=True)
    op.create_index(op.f('ix_claim_response_id'), 'claim_response', ['id'], unique=False)
    op.create_index(op.f('ix_claim_response_org_id'), 'claim_response', ['org_id'], unique=False)
    op.create_index(op.f('ix_claim_response_user_id'), 'claim_response', ['user_id'], unique=False)

    # identifier child table
    op.create_table('claim_response_identifier',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('claim_response_id', sa.Integer(), nullable=False),
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
    sa.ForeignKeyConstraint(['claim_response_id'], ['claim_response.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_claim_response_identifier_claim_response_id'), 'claim_response_identifier', ['claim_response_id'], unique=False)

    # item child table
    op.create_table('claim_response_item',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('claim_response_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('item_sequence', sa.Integer(), nullable=False),
    sa.Column('note_number', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['claim_response_id'], ['claim_response.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_claim_response_item_claim_response_id'), 'claim_response_item', ['claim_response_id'], unique=False)

    # item.adjudication grandchild
    op.create_table('claim_response_item_adjudication',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('item_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('category_system', sa.String(), nullable=True),
    sa.Column('category_code', sa.String(), nullable=True),
    sa.Column('category_display', sa.String(), nullable=True),
    sa.Column('category_text', sa.String(), nullable=True),
    sa.Column('reason_system', sa.String(), nullable=True),
    sa.Column('reason_code', sa.String(), nullable=True),
    sa.Column('reason_display', sa.String(), nullable=True),
    sa.Column('reason_text', sa.String(), nullable=True),
    sa.Column('amount_value', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('amount_currency', sa.String(length=3), nullable=True),
    sa.Column('adj_value', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.ForeignKeyConstraint(['item_id'], ['claim_response_item.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_claim_response_item_adjudication_item_id'), 'claim_response_item_adjudication', ['item_id'], unique=False)

    # item.detail grandchild
    op.create_table('claim_response_item_detail',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('item_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('detail_sequence', sa.Integer(), nullable=False),
    sa.Column('note_number', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['item_id'], ['claim_response_item.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_claim_response_item_detail_item_id'), 'claim_response_item_detail', ['item_id'], unique=False)

    # item.detail.adjudication great-grandchild
    op.create_table('claim_response_item_detail_adjudication',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('detail_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('category_system', sa.String(), nullable=True),
    sa.Column('category_code', sa.String(), nullable=True),
    sa.Column('category_display', sa.String(), nullable=True),
    sa.Column('category_text', sa.String(), nullable=True),
    sa.Column('reason_system', sa.String(), nullable=True),
    sa.Column('reason_code', sa.String(), nullable=True),
    sa.Column('reason_display', sa.String(), nullable=True),
    sa.Column('reason_text', sa.String(), nullable=True),
    sa.Column('amount_value', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('amount_currency', sa.String(length=3), nullable=True),
    sa.Column('adj_value', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.ForeignKeyConstraint(['detail_id'], ['claim_response_item_detail.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_claim_response_item_detail_adjudication_detail_id'), 'claim_response_item_detail_adjudication', ['detail_id'], unique=False)

    # item.detail.subDetail great-grandchild
    op.create_table('claim_response_item_detail_sub_detail',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('detail_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('sub_detail_sequence', sa.Integer(), nullable=False),
    sa.Column('note_number', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['detail_id'], ['claim_response_item_detail.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_claim_response_item_detail_sub_detail_detail_id'), 'claim_response_item_detail_sub_detail', ['detail_id'], unique=False)

    # item.detail.subDetail.adjudication great-great-grandchild
    op.create_table('claim_response_item_detail_sub_detail_adjudication',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('sub_detail_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('category_system', sa.String(), nullable=True),
    sa.Column('category_code', sa.String(), nullable=True),
    sa.Column('category_display', sa.String(), nullable=True),
    sa.Column('category_text', sa.String(), nullable=True),
    sa.Column('reason_system', sa.String(), nullable=True),
    sa.Column('reason_code', sa.String(), nullable=True),
    sa.Column('reason_display', sa.String(), nullable=True),
    sa.Column('reason_text', sa.String(), nullable=True),
    sa.Column('amount_value', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('amount_currency', sa.String(length=3), nullable=True),
    sa.Column('adj_value', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.ForeignKeyConstraint(['sub_detail_id'], ['claim_response_item_detail_sub_detail.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_claim_response_item_detail_sub_detail_adjudication_sub_detail_id'), 'claim_response_item_detail_sub_detail_adjudication', ['sub_detail_id'], unique=False)

    # addItem child table
    op.create_table('claim_response_add_item',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('claim_response_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('item_sequence', sa.Text(), nullable=True),
    sa.Column('detail_sequence', sa.Text(), nullable=True),
    sa.Column('subdetail_sequence', sa.Text(), nullable=True),
    sa.Column('product_or_service_system', sa.String(), nullable=True),
    sa.Column('product_or_service_code', sa.String(), nullable=True),
    sa.Column('product_or_service_display', sa.String(), nullable=True),
    sa.Column('product_or_service_text', sa.String(), nullable=True),
    sa.Column('serviced_date', sa.Date(), nullable=True),
    sa.Column('serviced_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('serviced_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('location_cc_system', sa.String(), nullable=True),
    sa.Column('location_cc_code', sa.String(), nullable=True),
    sa.Column('location_cc_display', sa.String(), nullable=True),
    sa.Column('location_cc_text', sa.String(), nullable=True),
    sa.Column('location_address_use', sa.String(), nullable=True),
    sa.Column('location_address_type', sa.String(), nullable=True),
    sa.Column('location_address_text', sa.String(), nullable=True),
    sa.Column('location_address_line', sa.Text(), nullable=True),
    sa.Column('location_address_city', sa.String(), nullable=True),
    sa.Column('location_address_district', sa.String(), nullable=True),
    sa.Column('location_address_state', sa.String(), nullable=True),
    sa.Column('location_address_postal_code', sa.String(), nullable=True),
    sa.Column('location_address_country', sa.String(), nullable=True),
    sa.Column('location_ref_type', postgresql.ENUM('Location', name='claim_response_add_item_location_ref_type', create_type=False), nullable=True),
    sa.Column('location_ref_id', sa.Integer(), nullable=True),
    sa.Column('location_ref_display', sa.String(), nullable=True),
    sa.Column('quantity_value', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('quantity_unit', sa.String(), nullable=True),
    sa.Column('quantity_system', sa.String(), nullable=True),
    sa.Column('quantity_code', sa.String(), nullable=True),
    sa.Column('unit_price_value', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('unit_price_currency', sa.String(length=3), nullable=True),
    sa.Column('factor', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('net_value', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('net_currency', sa.String(length=3), nullable=True),
    sa.Column('body_site_system', sa.String(), nullable=True),
    sa.Column('body_site_code', sa.String(), nullable=True),
    sa.Column('body_site_display', sa.String(), nullable=True),
    sa.Column('body_site_text', sa.String(), nullable=True),
    sa.Column('note_number', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['claim_response_id'], ['claim_response.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_claim_response_add_item_claim_response_id'), 'claim_response_add_item', ['claim_response_id'], unique=False)

    # addItem.provider grandchild
    op.create_table('claim_response_add_item_provider',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('add_item_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('reference_type', postgresql.ENUM('Practitioner', 'PractitionerRole', 'Organization', name='claim_response_add_item_provider_ref_type', create_type=False), nullable=True),
    sa.Column('reference_id', sa.Integer(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['add_item_id'], ['claim_response_add_item.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_claim_response_add_item_provider_add_item_id'), 'claim_response_add_item_provider', ['add_item_id'], unique=False)

    # addItem.modifier grandchild
    op.create_table('claim_response_add_item_modifier',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('add_item_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('coding_system', sa.String(), nullable=True),
    sa.Column('coding_code', sa.String(), nullable=True),
    sa.Column('coding_display', sa.String(), nullable=True),
    sa.Column('text', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['add_item_id'], ['claim_response_add_item.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_claim_response_add_item_modifier_add_item_id'), 'claim_response_add_item_modifier', ['add_item_id'], unique=False)

    # addItem.programCode grandchild
    op.create_table('claim_response_add_item_program_code',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('add_item_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('coding_system', sa.String(), nullable=True),
    sa.Column('coding_code', sa.String(), nullable=True),
    sa.Column('coding_display', sa.String(), nullable=True),
    sa.Column('text', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['add_item_id'], ['claim_response_add_item.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_claim_response_add_item_program_code_add_item_id'), 'claim_response_add_item_program_code', ['add_item_id'], unique=False)

    # addItem.subSite grandchild
    op.create_table('claim_response_add_item_sub_site',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('add_item_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('coding_system', sa.String(), nullable=True),
    sa.Column('coding_code', sa.String(), nullable=True),
    sa.Column('coding_display', sa.String(), nullable=True),
    sa.Column('text', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['add_item_id'], ['claim_response_add_item.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_claim_response_add_item_sub_site_add_item_id'), 'claim_response_add_item_sub_site', ['add_item_id'], unique=False)

    # addItem.adjudication grandchild
    op.create_table('claim_response_add_item_adjudication',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('add_item_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('category_system', sa.String(), nullable=True),
    sa.Column('category_code', sa.String(), nullable=True),
    sa.Column('category_display', sa.String(), nullable=True),
    sa.Column('category_text', sa.String(), nullable=True),
    sa.Column('reason_system', sa.String(), nullable=True),
    sa.Column('reason_code', sa.String(), nullable=True),
    sa.Column('reason_display', sa.String(), nullable=True),
    sa.Column('reason_text', sa.String(), nullable=True),
    sa.Column('amount_value', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('amount_currency', sa.String(length=3), nullable=True),
    sa.Column('adj_value', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.ForeignKeyConstraint(['add_item_id'], ['claim_response_add_item.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_claim_response_add_item_adjudication_add_item_id'), 'claim_response_add_item_adjudication', ['add_item_id'], unique=False)

    # addItem.detail grandchild
    op.create_table('claim_response_add_item_detail',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('add_item_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('product_or_service_system', sa.String(), nullable=True),
    sa.Column('product_or_service_code', sa.String(), nullable=True),
    sa.Column('product_or_service_display', sa.String(), nullable=True),
    sa.Column('product_or_service_text', sa.String(), nullable=True),
    sa.Column('quantity_value', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('quantity_unit', sa.String(), nullable=True),
    sa.Column('quantity_system', sa.String(), nullable=True),
    sa.Column('quantity_code', sa.String(), nullable=True),
    sa.Column('unit_price_value', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('unit_price_currency', sa.String(length=3), nullable=True),
    sa.Column('factor', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('net_value', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('net_currency', sa.String(length=3), nullable=True),
    sa.Column('note_number', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['add_item_id'], ['claim_response_add_item.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_claim_response_add_item_detail_add_item_id'), 'claim_response_add_item_detail', ['add_item_id'], unique=False)

    # addItem.detail.modifier great-grandchild
    op.create_table('claim_response_add_item_detail_modifier',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('detail_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('coding_system', sa.String(), nullable=True),
    sa.Column('coding_code', sa.String(), nullable=True),
    sa.Column('coding_display', sa.String(), nullable=True),
    sa.Column('text', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['detail_id'], ['claim_response_add_item_detail.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_claim_response_add_item_detail_modifier_detail_id'), 'claim_response_add_item_detail_modifier', ['detail_id'], unique=False)

    # addItem.detail.adjudication great-grandchild
    op.create_table('claim_response_add_item_detail_adjudication',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('detail_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('category_system', sa.String(), nullable=True),
    sa.Column('category_code', sa.String(), nullable=True),
    sa.Column('category_display', sa.String(), nullable=True),
    sa.Column('category_text', sa.String(), nullable=True),
    sa.Column('reason_system', sa.String(), nullable=True),
    sa.Column('reason_code', sa.String(), nullable=True),
    sa.Column('reason_display', sa.String(), nullable=True),
    sa.Column('reason_text', sa.String(), nullable=True),
    sa.Column('amount_value', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('amount_currency', sa.String(length=3), nullable=True),
    sa.Column('adj_value', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.ForeignKeyConstraint(['detail_id'], ['claim_response_add_item_detail.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_claim_response_add_item_detail_adjudication_detail_id'), 'claim_response_add_item_detail_adjudication', ['detail_id'], unique=False)

    # addItem.detail.subDetail great-grandchild
    op.create_table('claim_response_add_item_detail_sub_detail',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('detail_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('product_or_service_system', sa.String(), nullable=True),
    sa.Column('product_or_service_code', sa.String(), nullable=True),
    sa.Column('product_or_service_display', sa.String(), nullable=True),
    sa.Column('product_or_service_text', sa.String(), nullable=True),
    sa.Column('quantity_value', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('quantity_unit', sa.String(), nullable=True),
    sa.Column('quantity_system', sa.String(), nullable=True),
    sa.Column('quantity_code', sa.String(), nullable=True),
    sa.Column('unit_price_value', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('unit_price_currency', sa.String(length=3), nullable=True),
    sa.Column('factor', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('net_value', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('net_currency', sa.String(length=3), nullable=True),
    sa.Column('note_number', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['detail_id'], ['claim_response_add_item_detail.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_claim_response_add_item_detail_sub_detail_detail_id'), 'claim_response_add_item_detail_sub_detail', ['detail_id'], unique=False)

    # addItem.detail.subDetail.modifier great-great-grandchild
    op.create_table('claim_response_add_item_detail_sub_detail_modifier',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('sub_detail_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('coding_system', sa.String(), nullable=True),
    sa.Column('coding_code', sa.String(), nullable=True),
    sa.Column('coding_display', sa.String(), nullable=True),
    sa.Column('text', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['sub_detail_id'], ['claim_response_add_item_detail_sub_detail.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_claim_response_add_item_detail_sub_detail_modifier_sub_detail_id'), 'claim_response_add_item_detail_sub_detail_modifier', ['sub_detail_id'], unique=False)

    # addItem.detail.subDetail.adjudication great-great-grandchild
    op.create_table('claim_response_add_item_detail_sub_detail_adjudication',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('sub_detail_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('category_system', sa.String(), nullable=True),
    sa.Column('category_code', sa.String(), nullable=True),
    sa.Column('category_display', sa.String(), nullable=True),
    sa.Column('category_text', sa.String(), nullable=True),
    sa.Column('reason_system', sa.String(), nullable=True),
    sa.Column('reason_code', sa.String(), nullable=True),
    sa.Column('reason_display', sa.String(), nullable=True),
    sa.Column('reason_text', sa.String(), nullable=True),
    sa.Column('amount_value', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('amount_currency', sa.String(length=3), nullable=True),
    sa.Column('adj_value', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.ForeignKeyConstraint(['sub_detail_id'], ['claim_response_add_item_detail_sub_detail.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_claim_response_add_item_detail_sub_detail_adjudication_sub_detail_id'), 'claim_response_add_item_detail_sub_detail_adjudication', ['sub_detail_id'], unique=False)

    # Header-level adjudication child table
    op.create_table('claim_response_adjudication',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('claim_response_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('category_system', sa.String(), nullable=True),
    sa.Column('category_code', sa.String(), nullable=True),
    sa.Column('category_display', sa.String(), nullable=True),
    sa.Column('category_text', sa.String(), nullable=True),
    sa.Column('reason_system', sa.String(), nullable=True),
    sa.Column('reason_code', sa.String(), nullable=True),
    sa.Column('reason_display', sa.String(), nullable=True),
    sa.Column('reason_text', sa.String(), nullable=True),
    sa.Column('amount_value', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('amount_currency', sa.String(length=3), nullable=True),
    sa.Column('adj_value', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.ForeignKeyConstraint(['claim_response_id'], ['claim_response.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_claim_response_adjudication_claim_response_id'), 'claim_response_adjudication', ['claim_response_id'], unique=False)

    # total child table
    op.create_table('claim_response_total',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('claim_response_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('category_system', sa.String(), nullable=True),
    sa.Column('category_code', sa.String(), nullable=True),
    sa.Column('category_display', sa.String(), nullable=True),
    sa.Column('category_text', sa.String(), nullable=True),
    sa.Column('amount_value', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('amount_currency', sa.String(length=3), nullable=True),
    sa.ForeignKeyConstraint(['claim_response_id'], ['claim_response.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_claim_response_total_claim_response_id'), 'claim_response_total', ['claim_response_id'], unique=False)

    # processNote child table
    op.create_table('claim_response_process_note',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('claim_response_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('number', sa.Integer(), nullable=True),
    sa.Column('note_type', sa.String(), nullable=True),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('language_system', sa.String(), nullable=True),
    sa.Column('language_code', sa.String(), nullable=True),
    sa.Column('language_display', sa.String(), nullable=True),
    sa.Column('language_text', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['claim_response_id'], ['claim_response.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_claim_response_process_note_claim_response_id'), 'claim_response_process_note', ['claim_response_id'], unique=False)

    # communicationRequest child table
    op.create_table('claim_response_communication_request',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('claim_response_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('reference_type', postgresql.ENUM('CommunicationRequest', name='claim_response_comm_req_ref_type', create_type=False), nullable=True),
    sa.Column('reference_id', sa.Integer(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['claim_response_id'], ['claim_response.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_claim_response_communication_request_claim_response_id'), 'claim_response_communication_request', ['claim_response_id'], unique=False)

    # insurance child table
    op.create_table('claim_response_insurance',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('claim_response_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('sequence', sa.Integer(), nullable=False),
    sa.Column('focal', sa.Boolean(), nullable=False),
    sa.Column('coverage_type', postgresql.ENUM('Coverage', name='claim_response_insurance_coverage_ref_type', create_type=False), nullable=True),
    sa.Column('coverage_id', sa.Integer(), nullable=True),
    sa.Column('coverage_display', sa.String(), nullable=True),
    sa.Column('business_arrangement', sa.String(), nullable=True),
    sa.Column('claim_response_ref_type', postgresql.ENUM('ClaimResponse', name='claim_response_insurance_cr_ref_type', create_type=False), nullable=True),
    sa.Column('claim_response_ref_id', sa.Integer(), nullable=True),
    sa.Column('claim_response_ref_display', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['claim_response_id'], ['claim_response.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_claim_response_insurance_claim_response_id'), 'claim_response_insurance', ['claim_response_id'], unique=False)

    # error child table
    op.create_table('claim_response_error',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('claim_response_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('item_sequence', sa.Integer(), nullable=True),
    sa.Column('detail_sequence', sa.Integer(), nullable=True),
    sa.Column('sub_detail_sequence', sa.Integer(), nullable=True),
    sa.Column('code_system', sa.String(), nullable=True),
    sa.Column('code_code', sa.String(), nullable=True),
    sa.Column('code_display', sa.String(), nullable=True),
    sa.Column('code_text', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['claim_response_id'], ['claim_response.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_claim_response_error_claim_response_id'), 'claim_response_error', ['claim_response_id'], unique=False)


def downgrade() -> None:
    # Drop in reverse FK order (deepest first)
    op.drop_index(op.f('ix_claim_response_item_detail_sub_detail_adjudication_sub_detail_id'), table_name='claim_response_item_detail_sub_detail_adjudication')
    op.drop_table('claim_response_item_detail_sub_detail_adjudication')
    op.drop_index(op.f('ix_claim_response_add_item_detail_sub_detail_adjudication_sub_detail_id'), table_name='claim_response_add_item_detail_sub_detail_adjudication')
    op.drop_table('claim_response_add_item_detail_sub_detail_adjudication')
    op.drop_index(op.f('ix_claim_response_add_item_detail_sub_detail_modifier_sub_detail_id'), table_name='claim_response_add_item_detail_sub_detail_modifier')
    op.drop_table('claim_response_add_item_detail_sub_detail_modifier')
    op.drop_index(op.f('ix_claim_response_item_detail_sub_detail_detail_id'), table_name='claim_response_item_detail_sub_detail')
    op.drop_table('claim_response_item_detail_sub_detail')
    op.drop_index(op.f('ix_claim_response_add_item_detail_sub_detail_detail_id'), table_name='claim_response_add_item_detail_sub_detail')
    op.drop_table('claim_response_add_item_detail_sub_detail')
    op.drop_index(op.f('ix_claim_response_item_detail_adjudication_detail_id'), table_name='claim_response_item_detail_adjudication')
    op.drop_table('claim_response_item_detail_adjudication')
    op.drop_index(op.f('ix_claim_response_add_item_detail_adjudication_detail_id'), table_name='claim_response_add_item_detail_adjudication')
    op.drop_table('claim_response_add_item_detail_adjudication')
    op.drop_index(op.f('ix_claim_response_add_item_detail_modifier_detail_id'), table_name='claim_response_add_item_detail_modifier')
    op.drop_table('claim_response_add_item_detail_modifier')
    op.drop_index(op.f('ix_claim_response_item_detail_item_id'), table_name='claim_response_item_detail')
    op.drop_table('claim_response_item_detail')
    op.drop_index(op.f('ix_claim_response_add_item_detail_add_item_id'), table_name='claim_response_add_item_detail')
    op.drop_table('claim_response_add_item_detail')
    op.drop_index(op.f('ix_claim_response_item_adjudication_item_id'), table_name='claim_response_item_adjudication')
    op.drop_table('claim_response_item_adjudication')
    op.drop_index(op.f('ix_claim_response_add_item_adjudication_add_item_id'), table_name='claim_response_add_item_adjudication')
    op.drop_table('claim_response_add_item_adjudication')
    op.drop_index(op.f('ix_claim_response_add_item_sub_site_add_item_id'), table_name='claim_response_add_item_sub_site')
    op.drop_table('claim_response_add_item_sub_site')
    op.drop_index(op.f('ix_claim_response_add_item_program_code_add_item_id'), table_name='claim_response_add_item_program_code')
    op.drop_table('claim_response_add_item_program_code')
    op.drop_index(op.f('ix_claim_response_add_item_modifier_add_item_id'), table_name='claim_response_add_item_modifier')
    op.drop_table('claim_response_add_item_modifier')
    op.drop_index(op.f('ix_claim_response_add_item_provider_add_item_id'), table_name='claim_response_add_item_provider')
    op.drop_table('claim_response_add_item_provider')
    op.drop_index(op.f('ix_claim_response_item_claim_response_id'), table_name='claim_response_item')
    op.drop_table('claim_response_item')
    op.drop_index(op.f('ix_claim_response_add_item_claim_response_id'), table_name='claim_response_add_item')
    op.drop_table('claim_response_add_item')
    op.drop_index(op.f('ix_claim_response_error_claim_response_id'), table_name='claim_response_error')
    op.drop_table('claim_response_error')
    op.drop_index(op.f('ix_claim_response_insurance_claim_response_id'), table_name='claim_response_insurance')
    op.drop_table('claim_response_insurance')
    op.drop_index(op.f('ix_claim_response_communication_request_claim_response_id'), table_name='claim_response_communication_request')
    op.drop_table('claim_response_communication_request')
    op.drop_index(op.f('ix_claim_response_process_note_claim_response_id'), table_name='claim_response_process_note')
    op.drop_table('claim_response_process_note')
    op.drop_index(op.f('ix_claim_response_total_claim_response_id'), table_name='claim_response_total')
    op.drop_table('claim_response_total')
    op.drop_index(op.f('ix_claim_response_adjudication_claim_response_id'), table_name='claim_response_adjudication')
    op.drop_table('claim_response_adjudication')
    op.drop_index(op.f('ix_claim_response_identifier_claim_response_id'), table_name='claim_response_identifier')
    op.drop_table('claim_response_identifier')
    op.drop_index(op.f('ix_claim_response_user_id'), table_name='claim_response')
    op.drop_index(op.f('ix_claim_response_org_id'), table_name='claim_response')
    op.drop_index(op.f('ix_claim_response_id'), table_name='claim_response')
    op.drop_index(op.f('ix_claim_response_claim_response_id'), table_name='claim_response')
    op.drop_table('claim_response')

    op.execute("DROP SEQUENCE IF EXISTS claim_response_id_seq")

    # Drop new enum types (not organization_reference_type — it is shared)
    bind = op.get_bind()
    _status_enum.drop(bind, checkfirst=True)
    _use_enum.drop(bind, checkfirst=True)
    _outcome_enum.drop(bind, checkfirst=True)
    _patient_ref_enum.drop(bind, checkfirst=True)
    _requestor_ref_enum.drop(bind, checkfirst=True)
    _request_ref_enum.drop(bind, checkfirst=True)
    _add_item_location_ref_enum.drop(bind, checkfirst=True)
    _add_item_provider_ref_enum.drop(bind, checkfirst=True)
    _insurance_coverage_ref_enum.drop(bind, checkfirst=True)
    _insurance_cr_ref_enum.drop(bind, checkfirst=True)
    _comm_req_ref_enum.drop(bind, checkfirst=True)
