"""add episode_of_care tables

Revision ID: 6fe394d10fac
Revises: 80f97ad7e15e
Create Date: 2026-05-18 23:46:03.740674

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '6fe394d10fac'
down_revision: Union[str, None] = '80f97ad7e15e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_episode_of_care_status = postgresql.ENUM(
    'planned', 'waitlist', 'active', 'onhold', 'finished', 'cancelled', 'entered-in-error',
    name='episode_of_care_status',
)
_episode_of_care_patient_reference_type = postgresql.ENUM(
    'Patient',
    name='episode_of_care_patient_reference_type',
)
_episode_of_care_care_manager_reference_type = postgresql.ENUM(
    'Practitioner', 'PractitionerRole',
    name='episode_of_care_care_manager_reference_type',
)
_episode_of_care_diagnosis_reference_type = postgresql.ENUM(
    'Condition',
    name='episode_of_care_diagnosis_reference_type',
)
_episode_of_care_referral_request_reference_type = postgresql.ENUM(
    'ServiceRequest',
    name='episode_of_care_referral_request_reference_type',
)
_episode_of_care_team_reference_type = postgresql.ENUM(
    'CareTeam',
    name='episode_of_care_team_reference_type',
)
_episode_of_care_account_reference_type = postgresql.ENUM(
    'Account',
    name='episode_of_care_account_reference_type',
)


def upgrade() -> None:
    _episode_of_care_status.create(op.get_bind(), checkfirst=True)
    _episode_of_care_patient_reference_type.create(op.get_bind(), checkfirst=True)
    _episode_of_care_care_manager_reference_type.create(op.get_bind(), checkfirst=True)
    _episode_of_care_diagnosis_reference_type.create(op.get_bind(), checkfirst=True)
    _episode_of_care_referral_request_reference_type.create(op.get_bind(), checkfirst=True)
    _episode_of_care_team_reference_type.create(op.get_bind(), checkfirst=True)
    _episode_of_care_account_reference_type.create(op.get_bind(), checkfirst=True)

    op.execute("CREATE SEQUENCE IF NOT EXISTS episode_of_care_id_seq START 350000 INCREMENT 1")

    op.create_table(
        'episode_of_care',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('episode_of_care_id', sa.Integer(), server_default=sa.text("nextval('episode_of_care_id_seq')"), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('status', postgresql.ENUM('planned', 'waitlist', 'active', 'onhold', 'finished', 'cancelled', 'entered-in-error', name='episode_of_care_status', create_type=False), nullable=False),
        sa.Column('patient_type', postgresql.ENUM('Patient', name='episode_of_care_patient_reference_type', create_type=False), nullable=True),
        sa.Column('patient_id', sa.Integer(), nullable=True),
        sa.Column('patient_display', sa.String(), nullable=True),
        sa.Column('managing_organization_type', postgresql.ENUM('Organization', name='organization_reference_type', create_type=False), nullable=True),
        sa.Column('managing_organization_id', sa.Integer(), nullable=True),
        sa.Column('managing_organization_display', sa.String(), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('care_manager_type', postgresql.ENUM('Practitioner', 'PractitionerRole', name='episode_of_care_care_manager_reference_type', create_type=False), nullable=True),
        sa.Column('care_manager_id', sa.Integer(), nullable=True),
        sa.Column('care_manager_display', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['managing_organization_id'], ['organization.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_episode_of_care_id'), 'episode_of_care', ['id'], unique=False)
    op.create_index(op.f('ix_episode_of_care_episode_of_care_id'), 'episode_of_care', ['episode_of_care_id'], unique=True)
    op.create_index(op.f('ix_episode_of_care_user_id'), 'episode_of_care', ['user_id'], unique=False)
    op.create_index(op.f('ix_episode_of_care_org_id'), 'episode_of_care', ['org_id'], unique=False)
    op.create_index(op.f('ix_episode_of_care_managing_organization_id'), 'episode_of_care', ['managing_organization_id'], unique=False)

    op.create_table(
        'episode_of_care_identifier',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('episode_of_care_id', sa.Integer(), nullable=False),
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
        sa.ForeignKeyConstraint(['episode_of_care_id'], ['episode_of_care.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_episode_of_care_identifier_episode_of_care_id'), 'episode_of_care_identifier', ['episode_of_care_id'], unique=False)

    op.create_table(
        'episode_of_care_status_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('episode_of_care_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['episode_of_care_id'], ['episode_of_care.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_episode_of_care_status_history_episode_of_care_id'), 'episode_of_care_status_history', ['episode_of_care_id'], unique=False)

    op.create_table(
        'episode_of_care_type',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('episode_of_care_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['episode_of_care_id'], ['episode_of_care.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_episode_of_care_type_episode_of_care_id'), 'episode_of_care_type', ['episode_of_care_id'], unique=False)

    op.create_table(
        'episode_of_care_diagnosis',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('episode_of_care_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Condition', name='episode_of_care_diagnosis_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('role_system', sa.String(), nullable=True),
        sa.Column('role_code', sa.String(), nullable=True),
        sa.Column('role_display', sa.String(), nullable=True),
        sa.Column('role_text', sa.String(), nullable=True),
        sa.Column('rank', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['episode_of_care_id'], ['episode_of_care.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_episode_of_care_diagnosis_episode_of_care_id'), 'episode_of_care_diagnosis', ['episode_of_care_id'], unique=False)

    op.create_table(
        'episode_of_care_referral_request',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('episode_of_care_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('ServiceRequest', name='episode_of_care_referral_request_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['episode_of_care_id'], ['episode_of_care.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_episode_of_care_referral_request_episode_of_care_id'), 'episode_of_care_referral_request', ['episode_of_care_id'], unique=False)

    op.create_table(
        'episode_of_care_team',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('episode_of_care_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('CareTeam', name='episode_of_care_team_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['episode_of_care_id'], ['episode_of_care.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_episode_of_care_team_episode_of_care_id'), 'episode_of_care_team', ['episode_of_care_id'], unique=False)

    op.create_table(
        'episode_of_care_account',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('episode_of_care_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Account', name='episode_of_care_account_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['episode_of_care_id'], ['episode_of_care.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_episode_of_care_account_episode_of_care_id'), 'episode_of_care_account', ['episode_of_care_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_episode_of_care_account_episode_of_care_id'), table_name='episode_of_care_account')
    op.drop_table('episode_of_care_account')
    op.drop_index(op.f('ix_episode_of_care_team_episode_of_care_id'), table_name='episode_of_care_team')
    op.drop_table('episode_of_care_team')
    op.drop_index(op.f('ix_episode_of_care_referral_request_episode_of_care_id'), table_name='episode_of_care_referral_request')
    op.drop_table('episode_of_care_referral_request')
    op.drop_index(op.f('ix_episode_of_care_diagnosis_episode_of_care_id'), table_name='episode_of_care_diagnosis')
    op.drop_table('episode_of_care_diagnosis')
    op.drop_index(op.f('ix_episode_of_care_type_episode_of_care_id'), table_name='episode_of_care_type')
    op.drop_table('episode_of_care_type')
    op.drop_index(op.f('ix_episode_of_care_status_history_episode_of_care_id'), table_name='episode_of_care_status_history')
    op.drop_table('episode_of_care_status_history')
    op.drop_index(op.f('ix_episode_of_care_identifier_episode_of_care_id'), table_name='episode_of_care_identifier')
    op.drop_table('episode_of_care_identifier')
    op.drop_index(op.f('ix_episode_of_care_managing_organization_id'), table_name='episode_of_care')
    op.drop_index(op.f('ix_episode_of_care_org_id'), table_name='episode_of_care')
    op.drop_index(op.f('ix_episode_of_care_user_id'), table_name='episode_of_care')
    op.drop_index(op.f('ix_episode_of_care_episode_of_care_id'), table_name='episode_of_care')
    op.drop_index(op.f('ix_episode_of_care_id'), table_name='episode_of_care')
    op.drop_table('episode_of_care')

    op.execute("DROP SEQUENCE IF EXISTS episode_of_care_id_seq")

    _episode_of_care_account_reference_type.drop(op.get_bind(), checkfirst=True)
    _episode_of_care_team_reference_type.drop(op.get_bind(), checkfirst=True)
    _episode_of_care_referral_request_reference_type.drop(op.get_bind(), checkfirst=True)
    _episode_of_care_diagnosis_reference_type.drop(op.get_bind(), checkfirst=True)
    _episode_of_care_care_manager_reference_type.drop(op.get_bind(), checkfirst=True)
    _episode_of_care_patient_reference_type.drop(op.get_bind(), checkfirst=True)
    _episode_of_care_status.drop(op.get_bind(), checkfirst=True)
