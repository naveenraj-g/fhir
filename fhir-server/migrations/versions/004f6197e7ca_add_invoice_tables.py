"""add_invoice_tables

Revision ID: 004f6197e7ca
Revises: 102de3e80915
Create Date: 2026-05-16 14:35:29.016832

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '004f6197e7ca'
down_revision: Union[str, None] = '102de3e80915'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_status_enum = postgresql.ENUM(
    'draft', 'issued', 'balanced', 'cancelled', 'entered-in-error',
    name='invoice_status',
)
_subject_ref_enum = postgresql.ENUM(
    'Patient', 'Group',
    name='invoice_subject_reference_type',
)
_recipient_ref_enum = postgresql.ENUM(
    'Organization', 'Patient', 'RelatedPerson',
    name='invoice_recipient_reference_type',
)
_account_ref_enum = postgresql.ENUM(
    'Account',
    name='invoice_account_reference_type',
)
_chargeitem_ref_enum = postgresql.ENUM(
    'ChargeItem',
    name='invoice_line_item_chargeitem_ref_type',
)
_participant_actor_ref_enum = postgresql.ENUM(
    'Practitioner', 'Organization', 'Patient', 'PractitionerRole', 'Device', 'RelatedPerson',
    name='invoice_participant_actor_reference_type',
)


def upgrade() -> None:
    bind = op.get_bind()

    op.execute("CREATE SEQUENCE IF NOT EXISTS invoice_id_seq START WITH 210000 INCREMENT BY 1")

    _status_enum.create(bind, checkfirst=True)
    _subject_ref_enum.create(bind, checkfirst=True)
    _recipient_ref_enum.create(bind, checkfirst=True)
    _account_ref_enum.create(bind, checkfirst=True)
    _chargeitem_ref_enum.create(bind, checkfirst=True)
    _participant_actor_ref_enum.create(bind, checkfirst=True)

    op.create_table('invoice',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('invoice_id', sa.Integer(), server_default=sa.text("nextval('invoice_id_seq')"), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_by', sa.String(), nullable=True),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('status', postgresql.ENUM(
        'draft', 'issued', 'balanced', 'cancelled', 'entered-in-error',
        name='invoice_status', create_type=False,
    ), nullable=False),
    sa.Column('cancelled_reason', sa.String(), nullable=True),
    sa.Column('type_system', sa.String(), nullable=True),
    sa.Column('type_code', sa.String(), nullable=True),
    sa.Column('type_display', sa.String(), nullable=True),
    sa.Column('type_text', sa.String(), nullable=True),
    sa.Column('subject_type', postgresql.ENUM(
        'Patient', 'Group',
        name='invoice_subject_reference_type', create_type=False,
    ), nullable=True),
    sa.Column('subject_id', sa.Integer(), nullable=True),
    sa.Column('subject_display', sa.String(), nullable=True),
    sa.Column('recipient_type', postgresql.ENUM(
        'Organization', 'Patient', 'RelatedPerson',
        name='invoice_recipient_reference_type', create_type=False,
    ), nullable=True),
    sa.Column('recipient_id', sa.Integer(), nullable=True),
    sa.Column('recipient_display', sa.String(), nullable=True),
    sa.Column('date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('issuer_type', postgresql.ENUM(
        'Organization',
        name='organization_reference_type', create_type=False,
    ), nullable=True),
    sa.Column('issuer_id', sa.Integer(), nullable=True),
    sa.Column('issuer_display', sa.String(), nullable=True),
    sa.Column('account_type', postgresql.ENUM(
        'Account',
        name='invoice_account_reference_type', create_type=False,
    ), nullable=True),
    sa.Column('account_id', sa.Integer(), nullable=True),
    sa.Column('account_display', sa.String(), nullable=True),
    sa.Column('total_net_value', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('total_net_currency', sa.String(length=3), nullable=True),
    sa.Column('total_gross_value', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('total_gross_currency', sa.String(length=3), nullable=True),
    sa.Column('payment_terms', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_invoice_id'), 'invoice', ['id'], unique=False)
    op.create_index(op.f('ix_invoice_invoice_id'), 'invoice', ['invoice_id'], unique=True)
    op.create_index(op.f('ix_invoice_org_id'), 'invoice', ['org_id'], unique=False)
    op.create_index(op.f('ix_invoice_user_id'), 'invoice', ['user_id'], unique=False)

    op.create_table('invoice_identifier',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('invoice_id', sa.Integer(), nullable=False),
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
    sa.ForeignKeyConstraint(['invoice_id'], ['invoice.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_invoice_identifier_invoice_id'), 'invoice_identifier', ['invoice_id'], unique=False)

    op.create_table('invoice_participant',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('invoice_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('role_system', sa.String(), nullable=True),
    sa.Column('role_code', sa.String(), nullable=True),
    sa.Column('role_display', sa.String(), nullable=True),
    sa.Column('role_text', sa.String(), nullable=True),
    sa.Column('reference_type', postgresql.ENUM(
        'Practitioner', 'Organization', 'Patient', 'PractitionerRole', 'Device', 'RelatedPerson',
        name='invoice_participant_actor_reference_type', create_type=False,
    ), nullable=True),
    sa.Column('reference_id', sa.Integer(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['invoice_id'], ['invoice.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_invoice_participant_invoice_id'), 'invoice_participant', ['invoice_id'], unique=False)

    op.create_table('invoice_line_item',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('invoice_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('sequence', sa.Integer(), nullable=True),
    sa.Column('chargeitem_ref_type', postgresql.ENUM(
        'ChargeItem',
        name='invoice_line_item_chargeitem_ref_type', create_type=False,
    ), nullable=True),
    sa.Column('chargeitem_ref_id', sa.Integer(), nullable=True),
    sa.Column('chargeitem_ref_display', sa.String(), nullable=True),
    sa.Column('chargeitem_cc_system', sa.String(), nullable=True),
    sa.Column('chargeitem_cc_code', sa.String(), nullable=True),
    sa.Column('chargeitem_cc_display', sa.String(), nullable=True),
    sa.Column('chargeitem_cc_text', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['invoice_id'], ['invoice.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_invoice_line_item_invoice_id'), 'invoice_line_item', ['invoice_id'], unique=False)

    op.create_table('invoice_line_item_price_component',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('line_item_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('type', sa.String(), nullable=False),
    sa.Column('code_system', sa.String(), nullable=True),
    sa.Column('code_code', sa.String(), nullable=True),
    sa.Column('code_display', sa.String(), nullable=True),
    sa.Column('code_text', sa.String(), nullable=True),
    sa.Column('factor', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('amount_value', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('amount_currency', sa.String(length=3), nullable=True),
    sa.ForeignKeyConstraint(['line_item_id'], ['invoice_line_item.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_invoice_line_item_price_component_line_item_id'), 'invoice_line_item_price_component', ['line_item_id'], unique=False)

    op.create_table('invoice_total_price_component',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('invoice_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('type', sa.String(), nullable=False),
    sa.Column('code_system', sa.String(), nullable=True),
    sa.Column('code_code', sa.String(), nullable=True),
    sa.Column('code_display', sa.String(), nullable=True),
    sa.Column('code_text', sa.String(), nullable=True),
    sa.Column('factor', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('amount_value', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('amount_currency', sa.String(length=3), nullable=True),
    sa.ForeignKeyConstraint(['invoice_id'], ['invoice.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_invoice_total_price_component_invoice_id'), 'invoice_total_price_component', ['invoice_id'], unique=False)

    op.create_table('invoice_note',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('invoice_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('time', sa.DateTime(timezone=True), nullable=True),
    sa.Column('author_string', sa.String(), nullable=True),
    sa.Column('author_reference_type', sa.String(), nullable=True),
    sa.Column('author_reference_id', sa.Integer(), nullable=True),
    sa.Column('author_reference_display', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['invoice_id'], ['invoice.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_invoice_note_invoice_id'), 'invoice_note', ['invoice_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_invoice_note_invoice_id'), table_name='invoice_note')
    op.drop_table('invoice_note')
    op.drop_index(op.f('ix_invoice_total_price_component_invoice_id'), table_name='invoice_total_price_component')
    op.drop_table('invoice_total_price_component')
    op.drop_index(op.f('ix_invoice_line_item_price_component_line_item_id'), table_name='invoice_line_item_price_component')
    op.drop_table('invoice_line_item_price_component')
    op.drop_index(op.f('ix_invoice_line_item_invoice_id'), table_name='invoice_line_item')
    op.drop_table('invoice_line_item')
    op.drop_index(op.f('ix_invoice_participant_invoice_id'), table_name='invoice_participant')
    op.drop_table('invoice_participant')
    op.drop_index(op.f('ix_invoice_identifier_invoice_id'), table_name='invoice_identifier')
    op.drop_table('invoice_identifier')
    op.drop_index(op.f('ix_invoice_user_id'), table_name='invoice')
    op.drop_index(op.f('ix_invoice_org_id'), table_name='invoice')
    op.drop_index(op.f('ix_invoice_invoice_id'), table_name='invoice')
    op.drop_index(op.f('ix_invoice_id'), table_name='invoice')
    op.drop_table('invoice')

    op.execute("DROP SEQUENCE IF EXISTS invoice_id_seq")

    bind = op.get_bind()
    _participant_actor_ref_enum.drop(bind, checkfirst=True)
    _chargeitem_ref_enum.drop(bind, checkfirst=True)
    _account_ref_enum.drop(bind, checkfirst=True)
    _recipient_ref_enum.drop(bind, checkfirst=True)
    _subject_ref_enum.drop(bind, checkfirst=True)
    _status_enum.drop(bind, checkfirst=True)
    # organization_reference_type is shared — never drop here
