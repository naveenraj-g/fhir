"""add care_team

Revision ID: a715c89f62fd
Revises: c00a6dd9381e
Create Date: 2026-10-10 21:22:46.759210

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a715c89f62fd'
down_revision: Union[str, None] = 'c00a6dd9381e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    postgresql.ENUM('proposed', 'active', 'suspended', 'inactive', 'entered_in_error', name='care_team_status').create(op.get_bind(), checkfirst=True)
    postgresql.ENUM('Practitioner', 'PractitionerRole', 'RelatedPerson', 'Patient', 'Organization', 'CareTeam', name='care_team_member_type').create(op.get_bind(), checkfirst=True)
    postgresql.ENUM('Condition', name='care_team_reason_reference_type').create(op.get_bind(), checkfirst=True)
    op.execute('CREATE SEQUENCE IF NOT EXISTS care_team_pub_seq START 420000 INCREMENT 1')
    op.create_table('care_team',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('care_team_id', sa.Integer(), server_default=sa.text("nextval('care_team_pub_seq')"), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('status', postgresql.ENUM('proposed', 'active', 'suspended', 'inactive', 'entered_in_error', name='care_team_status', create_type=False), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('subject_type', postgresql.ENUM('Patient', 'Group', name='subject_reference_type', create_type=False), nullable=True),
    sa.Column('subject_id', sa.Integer(), nullable=True),
    sa.Column('subject_display', sa.String(), nullable=True),
    sa.Column('encounter_type', postgresql.ENUM('Encounter', name='encounter_reference_type', create_type=False), nullable=True),
    sa.Column('encounter_id', sa.Integer(), nullable=True),
    sa.Column('encounter_display', sa.String(), nullable=True),
    sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_by', sa.String(), nullable=True),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_care_team_care_team_id'), 'care_team', ['care_team_id'], unique=True)
    op.create_index(op.f('ix_care_team_encounter_id'), 'care_team', ['encounter_id'], unique=False)
    op.create_index(op.f('ix_care_team_id'), 'care_team', ['id'], unique=False)
    op.create_index(op.f('ix_care_team_name'), 'care_team', ['name'], unique=False)
    op.create_index(op.f('ix_care_team_org_id'), 'care_team', ['org_id'], unique=False)
    op.create_index(op.f('ix_care_team_status'), 'care_team', ['status'], unique=False)
    op.create_index(op.f('ix_care_team_subject_id'), 'care_team', ['subject_id'], unique=False)
    op.create_index(op.f('ix_care_team_user_id'), 'care_team', ['user_id'], unique=False)
    op.create_table('care_team_category',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('care_team_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('coding_system', sa.String(), nullable=True),
    sa.Column('coding_code', sa.String(), nullable=True),
    sa.Column('coding_display', sa.String(), nullable=True),
    sa.Column('text', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['care_team_id'], ['care_team.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_care_team_category_care_team_id'), 'care_team_category', ['care_team_id'], unique=False)
    op.create_index(op.f('ix_care_team_category_coding_code'), 'care_team_category', ['coding_code'], unique=False)
    op.create_table('care_team_identifier',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('care_team_id', sa.Integer(), nullable=False),
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
    sa.ForeignKeyConstraint(['care_team_id'], ['care_team.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_care_team_identifier_care_team_id'), 'care_team_identifier', ['care_team_id'], unique=False)
    op.create_table('care_team_managing_organization',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('care_team_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('reference_type', postgresql.ENUM('Organization', name='organization_reference_type', create_type=False), nullable=True),
    sa.Column('reference_id', sa.Integer(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['care_team_id'], ['care_team.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_care_team_managing_organization_care_team_id'), 'care_team_managing_organization', ['care_team_id'], unique=False)
    op.create_index(op.f('ix_care_team_managing_organization_reference_id'), 'care_team_managing_organization', ['reference_id'], unique=False)
    op.create_table('care_team_note',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('care_team_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('time', sa.DateTime(timezone=True), nullable=True),
    sa.Column('author_string', sa.String(), nullable=True),
    sa.Column('author_reference_type', sa.String(), nullable=True),
    sa.Column('author_reference_id', sa.Integer(), nullable=True),
    sa.Column('author_reference_display', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['care_team_id'], ['care_team.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_care_team_note_care_team_id'), 'care_team_note', ['care_team_id'], unique=False)
    op.create_table('care_team_participant',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('care_team_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('member_type', postgresql.ENUM('Practitioner', 'PractitionerRole', 'RelatedPerson', 'Patient', 'Organization', 'CareTeam', name='care_team_member_type', create_type=False), nullable=True),
    sa.Column('member_id', sa.Integer(), nullable=True),
    sa.Column('member_display', sa.String(), nullable=True),
    sa.Column('on_behalf_of_type', postgresql.ENUM('Organization', name='organization_reference_type', create_type=False), nullable=True),
    sa.Column('on_behalf_of_id', sa.Integer(), nullable=True),
    sa.Column('on_behalf_of_display', sa.String(), nullable=True),
    sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['care_team_id'], ['care_team.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_care_team_participant_care_team_id'), 'care_team_participant', ['care_team_id'], unique=False)
    op.create_index(op.f('ix_care_team_participant_member_id'), 'care_team_participant', ['member_id'], unique=False)
    op.create_index(op.f('ix_care_team_participant_on_behalf_of_id'), 'care_team_participant', ['on_behalf_of_id'], unique=False)
    op.create_table('care_team_reason_code',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('care_team_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('coding_system', sa.String(), nullable=True),
    sa.Column('coding_code', sa.String(), nullable=True),
    sa.Column('coding_display', sa.String(), nullable=True),
    sa.Column('text', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['care_team_id'], ['care_team.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_care_team_reason_code_care_team_id'), 'care_team_reason_code', ['care_team_id'], unique=False)
    op.create_table('care_team_reason_reference',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('care_team_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('reference_type', postgresql.ENUM('Condition', name='care_team_reason_reference_type', create_type=False), nullable=True),
    sa.Column('reference_id', sa.Integer(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['care_team_id'], ['care_team.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_care_team_reason_reference_care_team_id'), 'care_team_reason_reference', ['care_team_id'], unique=False)
    op.create_index(op.f('ix_care_team_reason_reference_reference_id'), 'care_team_reason_reference', ['reference_id'], unique=False)
    op.create_table('care_team_telecom',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('care_team_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('system', sa.String(), nullable=True),
    sa.Column('value', sa.String(), nullable=True),
    sa.Column('use', sa.String(), nullable=True),
    sa.Column('rank', sa.Integer(), nullable=True),
    sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['care_team_id'], ['care_team.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_care_team_telecom_care_team_id'), 'care_team_telecom', ['care_team_id'], unique=False)
    op.create_table('care_team_participant_role',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('participant_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('coding_system', sa.String(), nullable=True),
    sa.Column('coding_code', sa.String(), nullable=True),
    sa.Column('coding_display', sa.String(), nullable=True),
    sa.Column('text', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['participant_id'], ['care_team_participant.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_care_team_participant_role_coding_code'), 'care_team_participant_role', ['coding_code'], unique=False)
    op.create_index(op.f('ix_care_team_participant_role_participant_id'), 'care_team_participant_role', ['participant_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_care_team_participant_role_participant_id'), table_name='care_team_participant_role')
    op.drop_index(op.f('ix_care_team_participant_role_coding_code'), table_name='care_team_participant_role')
    op.drop_table('care_team_participant_role')
    op.drop_index(op.f('ix_care_team_telecom_care_team_id'), table_name='care_team_telecom')
    op.drop_table('care_team_telecom')
    op.drop_index(op.f('ix_care_team_reason_reference_reference_id'), table_name='care_team_reason_reference')
    op.drop_index(op.f('ix_care_team_reason_reference_care_team_id'), table_name='care_team_reason_reference')
    op.drop_table('care_team_reason_reference')
    op.drop_index(op.f('ix_care_team_reason_code_care_team_id'), table_name='care_team_reason_code')
    op.drop_table('care_team_reason_code')
    op.drop_index(op.f('ix_care_team_participant_on_behalf_of_id'), table_name='care_team_participant')
    op.drop_index(op.f('ix_care_team_participant_member_id'), table_name='care_team_participant')
    op.drop_index(op.f('ix_care_team_participant_care_team_id'), table_name='care_team_participant')
    op.drop_table('care_team_participant')
    op.drop_index(op.f('ix_care_team_note_care_team_id'), table_name='care_team_note')
    op.drop_table('care_team_note')
    op.drop_index(op.f('ix_care_team_managing_organization_reference_id'), table_name='care_team_managing_organization')
    op.drop_index(op.f('ix_care_team_managing_organization_care_team_id'), table_name='care_team_managing_organization')
    op.drop_table('care_team_managing_organization')
    op.drop_index(op.f('ix_care_team_identifier_care_team_id'), table_name='care_team_identifier')
    op.drop_table('care_team_identifier')
    op.drop_index(op.f('ix_care_team_category_coding_code'), table_name='care_team_category')
    op.drop_index(op.f('ix_care_team_category_care_team_id'), table_name='care_team_category')
    op.drop_table('care_team_category')
    op.drop_index(op.f('ix_care_team_user_id'), table_name='care_team')
    op.drop_index(op.f('ix_care_team_subject_id'), table_name='care_team')
    op.drop_index(op.f('ix_care_team_status'), table_name='care_team')
    op.drop_index(op.f('ix_care_team_org_id'), table_name='care_team')
    op.drop_index(op.f('ix_care_team_name'), table_name='care_team')
    op.drop_index(op.f('ix_care_team_id'), table_name='care_team')
    op.drop_index(op.f('ix_care_team_encounter_id'), table_name='care_team')
    op.drop_index(op.f('ix_care_team_care_team_id'), table_name='care_team')
    op.drop_table('care_team')
    op.execute('DROP SEQUENCE IF EXISTS care_team_pub_seq')
    # ### end Alembic commands ###
    postgresql.ENUM(name='care_team_status').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='care_team_member_type').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='care_team_reason_reference_type').drop(op.get_bind(), checkfirst=True)
