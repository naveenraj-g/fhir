"""add audit_event tables

Revision ID: 80f97ad7e15e
Revises: a03e90d011a7
Create Date: 2026-05-18 23:27:51.387207

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '80f97ad7e15e'
down_revision: Union[str, None] = 'a03e90d011a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_audit_event_who_reference_type = postgresql.ENUM(
    'Practitioner', 'PractitionerRole', 'Organization', 'Device', 'Patient', 'RelatedPerson',
    name='audit_event_who_reference_type',
)
_audit_event_location_reference_type = postgresql.ENUM(
    'Location',
    name='audit_event_location_reference_type',
)


def upgrade() -> None:
    _audit_event_who_reference_type.create(op.get_bind(), checkfirst=True)
    _audit_event_location_reference_type.create(op.get_bind(), checkfirst=True)

    op.execute("CREATE SEQUENCE IF NOT EXISTS audit_event_id_seq START 340000 INCREMENT 1")

    op.create_table(
        'audit_event',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('audit_event_id', sa.Integer(), server_default=sa.text("nextval('audit_event_id_seq')"), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('type_system', sa.String(), nullable=True),
        sa.Column('type_code', sa.String(), nullable=False),
        sa.Column('type_display', sa.String(), nullable=True),
        sa.Column('action', sa.String(), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('recorded', sa.DateTime(timezone=True), nullable=False),
        sa.Column('outcome', sa.String(), nullable=True),
        sa.Column('outcome_desc', sa.String(), nullable=True),
        sa.Column('source_site', sa.String(), nullable=True),
        sa.Column('source_observer_type', postgresql.ENUM('Practitioner', 'PractitionerRole', 'Organization', 'Device', 'Patient', 'RelatedPerson', name='audit_event_who_reference_type', create_type=False), nullable=True),
        sa.Column('source_observer_id', sa.Integer(), nullable=True),
        sa.Column('source_observer_display', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_audit_event_id'), 'audit_event', ['id'], unique=False)
    op.create_index(op.f('ix_audit_event_audit_event_id'), 'audit_event', ['audit_event_id'], unique=True)
    op.create_index(op.f('ix_audit_event_user_id'), 'audit_event', ['user_id'], unique=False)
    op.create_index(op.f('ix_audit_event_org_id'), 'audit_event', ['org_id'], unique=False)

    op.create_table(
        'audit_event_subtype',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('audit_event_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['audit_event_id'], ['audit_event.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_audit_event_subtype_audit_event_id'), 'audit_event_subtype', ['audit_event_id'], unique=False)

    op.create_table(
        'audit_event_purpose_of_event',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('audit_event_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['audit_event_id'], ['audit_event.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_audit_event_purpose_of_event_audit_event_id'), 'audit_event_purpose_of_event', ['audit_event_id'], unique=False)

    op.create_table(
        'audit_event_source_type',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('audit_event_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['audit_event_id'], ['audit_event.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_audit_event_source_type_audit_event_id'), 'audit_event_source_type', ['audit_event_id'], unique=False)

    op.create_table(
        'audit_event_agent',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('audit_event_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('type_system', sa.String(), nullable=True),
        sa.Column('type_code', sa.String(), nullable=True),
        sa.Column('type_display', sa.String(), nullable=True),
        sa.Column('type_text', sa.String(), nullable=True),
        sa.Column('who_type', postgresql.ENUM('Practitioner', 'PractitionerRole', 'Organization', 'Device', 'Patient', 'RelatedPerson', name='audit_event_who_reference_type', create_type=False), nullable=True),
        sa.Column('who_id', sa.Integer(), nullable=True),
        sa.Column('who_display', sa.String(), nullable=True),
        sa.Column('alt_id', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('requestor', sa.Boolean(), nullable=False),
        sa.Column('location_type', postgresql.ENUM('Location', name='audit_event_location_reference_type', create_type=False), nullable=True),
        sa.Column('location_id', sa.Integer(), nullable=True),
        sa.Column('location_display', sa.String(), nullable=True),
        sa.Column('media_system', sa.String(), nullable=True),
        sa.Column('media_code', sa.String(), nullable=True),
        sa.Column('media_display', sa.String(), nullable=True),
        sa.Column('network_address', sa.String(), nullable=True),
        sa.Column('network_type', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['audit_event_id'], ['audit_event.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_audit_event_agent_audit_event_id'), 'audit_event_agent', ['audit_event_id'], unique=False)

    op.create_table(
        'audit_event_agent_role',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['audit_event_agent.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_audit_event_agent_role_agent_id'), 'audit_event_agent_role', ['agent_id'], unique=False)

    op.create_table(
        'audit_event_agent_policy',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('value', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['audit_event_agent.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_audit_event_agent_policy_agent_id'), 'audit_event_agent_policy', ['agent_id'], unique=False)

    op.create_table(
        'audit_event_agent_purpose_of_use',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['audit_event_agent.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_audit_event_agent_purpose_of_use_agent_id'), 'audit_event_agent_purpose_of_use', ['agent_id'], unique=False)

    op.create_table(
        'audit_event_entity',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('audit_event_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('what_type', sa.String(), nullable=True),
        sa.Column('what_id', sa.Integer(), nullable=True),
        sa.Column('what_display', sa.String(), nullable=True),
        sa.Column('type_system', sa.String(), nullable=True),
        sa.Column('type_code', sa.String(), nullable=True),
        sa.Column('type_display', sa.String(), nullable=True),
        sa.Column('role_system', sa.String(), nullable=True),
        sa.Column('role_code', sa.String(), nullable=True),
        sa.Column('role_display', sa.String(), nullable=True),
        sa.Column('lifecycle_system', sa.String(), nullable=True),
        sa.Column('lifecycle_code', sa.String(), nullable=True),
        sa.Column('lifecycle_display', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('query', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['audit_event_id'], ['audit_event.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_audit_event_entity_audit_event_id'), 'audit_event_entity', ['audit_event_id'], unique=False)

    op.create_table(
        'audit_event_entity_security_label',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['entity_id'], ['audit_event_entity.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_audit_event_entity_security_label_entity_id'), 'audit_event_entity_security_label', ['entity_id'], unique=False)

    op.create_table(
        'audit_event_entity_detail',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('value_string', sa.Text(), nullable=True),
        sa.Column('value_base64_binary', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['entity_id'], ['audit_event_entity.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_audit_event_entity_detail_entity_id'), 'audit_event_entity_detail', ['entity_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_audit_event_entity_detail_entity_id'), table_name='audit_event_entity_detail')
    op.drop_table('audit_event_entity_detail')

    op.drop_index(op.f('ix_audit_event_entity_security_label_entity_id'), table_name='audit_event_entity_security_label')
    op.drop_table('audit_event_entity_security_label')

    op.drop_index(op.f('ix_audit_event_entity_audit_event_id'), table_name='audit_event_entity')
    op.drop_table('audit_event_entity')

    op.drop_index(op.f('ix_audit_event_agent_purpose_of_use_agent_id'), table_name='audit_event_agent_purpose_of_use')
    op.drop_table('audit_event_agent_purpose_of_use')

    op.drop_index(op.f('ix_audit_event_agent_policy_agent_id'), table_name='audit_event_agent_policy')
    op.drop_table('audit_event_agent_policy')

    op.drop_index(op.f('ix_audit_event_agent_role_agent_id'), table_name='audit_event_agent_role')
    op.drop_table('audit_event_agent_role')

    op.drop_index(op.f('ix_audit_event_agent_audit_event_id'), table_name='audit_event_agent')
    op.drop_table('audit_event_agent')

    op.drop_index(op.f('ix_audit_event_source_type_audit_event_id'), table_name='audit_event_source_type')
    op.drop_table('audit_event_source_type')

    op.drop_index(op.f('ix_audit_event_purpose_of_event_audit_event_id'), table_name='audit_event_purpose_of_event')
    op.drop_table('audit_event_purpose_of_event')

    op.drop_index(op.f('ix_audit_event_subtype_audit_event_id'), table_name='audit_event_subtype')
    op.drop_table('audit_event_subtype')

    op.drop_index(op.f('ix_audit_event_org_id'), table_name='audit_event')
    op.drop_index(op.f('ix_audit_event_user_id'), table_name='audit_event')
    op.drop_index(op.f('ix_audit_event_audit_event_id'), table_name='audit_event')
    op.drop_index(op.f('ix_audit_event_id'), table_name='audit_event')
    op.drop_table('audit_event')

    op.execute("DROP SEQUENCE IF EXISTS audit_event_id_seq")

    _audit_event_location_reference_type.drop(op.get_bind(), checkfirst=True)
    _audit_event_who_reference_type.drop(op.get_bind(), checkfirst=True)
