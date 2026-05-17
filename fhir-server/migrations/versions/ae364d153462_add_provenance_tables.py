"""add_provenance_tables

Revision ID: ae364d153462
Revises: a5c4e11ebbb3
Create Date: 2026-05-18 00:53:29.229496

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'ae364d153462'
down_revision: Union[str, None] = 'a5c4e11ebbb3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_location_ref = postgresql.ENUM('Location', name='provenance_location_reference_type')
_agent_who_ref = postgresql.ENUM(
    'Practitioner', 'PractitionerRole', 'RelatedPerson', 'Patient', 'Device', 'Organization',
    name='provenance_agent_who_reference_type',
)
_entity_role = postgresql.ENUM(
    'derivation', 'revision', 'quotation', 'source', 'removal',
    name='provenance_entity_role',
)


def upgrade() -> None:
    bind = op.get_bind()
    _location_ref.create(bind, checkfirst=True)
    _agent_who_ref.create(bind, checkfirst=True)
    _entity_role.create(bind, checkfirst=True)

    op.execute(
        "CREATE SEQUENCE IF NOT EXISTS provenance_id_seq START WITH 270000 INCREMENT BY 1"
    )

    op.create_table(
        'provenance',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('provenance_id', sa.Integer(), server_default=sa.text("nextval('provenance_id_seq')"), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('occurred_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('occurred_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('occurred_date_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('recorded', sa.DateTime(timezone=True), nullable=False),
        sa.Column('location_type', postgresql.ENUM('Location', name='provenance_location_reference_type', create_type=False), nullable=True),
        sa.Column('location_id', sa.Integer(), nullable=True),
        sa.Column('location_display', sa.String(), nullable=True),
        sa.Column('activity_system', sa.String(), nullable=True),
        sa.Column('activity_code', sa.String(), nullable=True),
        sa.Column('activity_display', sa.String(), nullable=True),
        sa.Column('activity_text', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_provenance_id'), 'provenance', ['id'], unique=False)
    op.create_index(op.f('ix_provenance_org_id'), 'provenance', ['org_id'], unique=False)
    op.create_index(op.f('ix_provenance_provenance_id'), 'provenance', ['provenance_id'], unique=True)
    op.create_index(op.f('ix_provenance_user_id'), 'provenance', ['user_id'], unique=False)

    op.create_table(
        'provenance_agent',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('provenance_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('type_system', sa.String(), nullable=True),
        sa.Column('type_code', sa.String(), nullable=True),
        sa.Column('type_display', sa.String(), nullable=True),
        sa.Column('type_text', sa.String(), nullable=True),
        sa.Column('who_type', postgresql.ENUM('Practitioner', 'PractitionerRole', 'RelatedPerson', 'Patient', 'Device', 'Organization', name='provenance_agent_who_reference_type', create_type=False), nullable=False),
        sa.Column('who_id', sa.Integer(), nullable=False),
        sa.Column('who_display', sa.String(), nullable=True),
        sa.Column('on_behalf_of_type', postgresql.ENUM('Practitioner', 'PractitionerRole', 'RelatedPerson', 'Patient', 'Device', 'Organization', name='provenance_agent_who_reference_type', create_type=False), nullable=True),
        sa.Column('on_behalf_of_id', sa.Integer(), nullable=True),
        sa.Column('on_behalf_of_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['provenance_id'], ['provenance.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_provenance_agent_provenance_id'), 'provenance_agent', ['provenance_id'], unique=False)

    op.create_table(
        'provenance_entity',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('provenance_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('role', postgresql.ENUM('derivation', 'revision', 'quotation', 'source', 'removal', name='provenance_entity_role', create_type=False), nullable=False),
        sa.Column('what_type', sa.String(), nullable=False),
        sa.Column('what_id', sa.Integer(), nullable=False),
        sa.Column('what_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['provenance_id'], ['provenance.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_provenance_entity_provenance_id'), 'provenance_entity', ['provenance_id'], unique=False)

    op.create_table(
        'provenance_policy',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('provenance_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('uri', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['provenance_id'], ['provenance.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_provenance_policy_provenance_id'), 'provenance_policy', ['provenance_id'], unique=False)

    op.create_table(
        'provenance_reason',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('provenance_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['provenance_id'], ['provenance.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_provenance_reason_provenance_id'), 'provenance_reason', ['provenance_id'], unique=False)

    op.create_table(
        'provenance_signature',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('provenance_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('when', sa.DateTime(timezone=True), nullable=False),
        sa.Column('who_type', sa.String(), nullable=True),
        sa.Column('who_id', sa.Integer(), nullable=True),
        sa.Column('who_display', sa.String(), nullable=True),
        sa.Column('on_behalf_of_type', sa.String(), nullable=True),
        sa.Column('on_behalf_of_id', sa.Integer(), nullable=True),
        sa.Column('on_behalf_of_display', sa.String(), nullable=True),
        sa.Column('target_format', sa.String(), nullable=True),
        sa.Column('sig_format', sa.String(), nullable=True),
        sa.Column('data', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['provenance_id'], ['provenance.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_provenance_signature_provenance_id'), 'provenance_signature', ['provenance_id'], unique=False)

    op.create_table(
        'provenance_target',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('provenance_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('reference_type', sa.String(), nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['provenance_id'], ['provenance.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_provenance_target_provenance_id'), 'provenance_target', ['provenance_id'], unique=False)

    op.create_table(
        'provenance_agent_role',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['provenance_agent.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_provenance_agent_role_agent_id'), 'provenance_agent_role', ['agent_id'], unique=False)

    op.create_table(
        'provenance_entity_agent',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('type_system', sa.String(), nullable=True),
        sa.Column('type_code', sa.String(), nullable=True),
        sa.Column('type_display', sa.String(), nullable=True),
        sa.Column('type_text', sa.String(), nullable=True),
        sa.Column('who_type', postgresql.ENUM('Practitioner', 'PractitionerRole', 'RelatedPerson', 'Patient', 'Device', 'Organization', name='provenance_agent_who_reference_type', create_type=False), nullable=False),
        sa.Column('who_id', sa.Integer(), nullable=False),
        sa.Column('who_display', sa.String(), nullable=True),
        sa.Column('on_behalf_of_type', postgresql.ENUM('Practitioner', 'PractitionerRole', 'RelatedPerson', 'Patient', 'Device', 'Organization', name='provenance_agent_who_reference_type', create_type=False), nullable=True),
        sa.Column('on_behalf_of_id', sa.Integer(), nullable=True),
        sa.Column('on_behalf_of_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['entity_id'], ['provenance_entity.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_provenance_entity_agent_entity_id'), 'provenance_entity_agent', ['entity_id'], unique=False)

    op.create_table(
        'provenance_signature_type',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('signature_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['signature_id'], ['provenance_signature.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_provenance_signature_type_signature_id'), 'provenance_signature_type', ['signature_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_provenance_signature_type_signature_id'), table_name='provenance_signature_type')
    op.drop_table('provenance_signature_type')
    op.drop_index(op.f('ix_provenance_entity_agent_entity_id'), table_name='provenance_entity_agent')
    op.drop_table('provenance_entity_agent')
    op.drop_index(op.f('ix_provenance_agent_role_agent_id'), table_name='provenance_agent_role')
    op.drop_table('provenance_agent_role')
    op.drop_index(op.f('ix_provenance_target_provenance_id'), table_name='provenance_target')
    op.drop_table('provenance_target')
    op.drop_index(op.f('ix_provenance_signature_provenance_id'), table_name='provenance_signature')
    op.drop_table('provenance_signature')
    op.drop_index(op.f('ix_provenance_reason_provenance_id'), table_name='provenance_reason')
    op.drop_table('provenance_reason')
    op.drop_index(op.f('ix_provenance_policy_provenance_id'), table_name='provenance_policy')
    op.drop_table('provenance_policy')
    op.drop_index(op.f('ix_provenance_entity_provenance_id'), table_name='provenance_entity')
    op.drop_table('provenance_entity')
    op.drop_index(op.f('ix_provenance_agent_provenance_id'), table_name='provenance_agent')
    op.drop_table('provenance_agent')
    op.drop_index(op.f('ix_provenance_user_id'), table_name='provenance')
    op.drop_index(op.f('ix_provenance_provenance_id'), table_name='provenance')
    op.drop_index(op.f('ix_provenance_org_id'), table_name='provenance')
    op.drop_index(op.f('ix_provenance_id'), table_name='provenance')
    op.drop_table('provenance')

    op.execute("DROP SEQUENCE IF EXISTS provenance_id_seq")

    bind = op.get_bind()
    _entity_role.drop(bind, checkfirst=True)
    _agent_who_ref.drop(bind, checkfirst=True)
    _location_ref.drop(bind, checkfirst=True)
