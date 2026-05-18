"""add related_person tables

Revision ID: 2afa0e63f0a3
Revises: b08509de3a0b
Create Date: 2026-05-18 06:02:26.706989

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '2afa0e63f0a3'
down_revision: Union[str, None] = 'b08509de3a0b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# New enum — only one for RelatedPerson
_patient_ref = postgresql.ENUM('Patient', name='related_person_patient_reference_type')

# Shared enums — already exist in DB; never create/drop
_admin_gender = postgresql.ENUM(name='administrative_gender', create_type=False)
_identifier_use = postgresql.ENUM(name='identifier_use', create_type=False)
_human_name_use = postgresql.ENUM(name='human_name_use', create_type=False)
_contact_point_system = postgresql.ENUM(name='contact_point_system', create_type=False)
_contact_point_use = postgresql.ENUM(name='contact_point_use', create_type=False)
_address_use = postgresql.ENUM(name='address_use', create_type=False)
_address_type = postgresql.ENUM(name='address_type', create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    _patient_ref.create(bind, checkfirst=True)

    op.execute(
        "CREATE SEQUENCE IF NOT EXISTS related_person_id_seq START WITH 300000 INCREMENT BY 1"
    )

    op.create_table(
        'related_person',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('related_person_id', sa.Integer(), server_default=sa.text("nextval('related_person_id_seq')"), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True),
        sa.Column('patient_type', postgresql.ENUM('Patient', name='related_person_patient_reference_type', create_type=False), nullable=True),
        sa.Column('patient_id', sa.Integer(), nullable=True),
        sa.Column('patient_display', sa.String(), nullable=True),
        sa.Column('gender', postgresql.ENUM(name='administrative_gender', create_type=False), nullable=True),
        sa.Column('birth_date', sa.Date(), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['patient_id'], ['patient.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_related_person_id'), 'related_person', ['id'], unique=False)
    op.create_index(op.f('ix_related_person_org_id'), 'related_person', ['org_id'], unique=False)
    op.create_index(op.f('ix_related_person_patient_id'), 'related_person', ['patient_id'], unique=False)
    op.create_index(op.f('ix_related_person_related_person_id'), 'related_person', ['related_person_id'], unique=True)
    op.create_index(op.f('ix_related_person_user_id'), 'related_person', ['user_id'], unique=False)

    op.create_table(
        'related_person_identifier',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('related_person_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('use', postgresql.ENUM(name='identifier_use', create_type=False), nullable=True),
        sa.Column('type_system', sa.String(), nullable=True),
        sa.Column('type_code', sa.String(), nullable=True),
        sa.Column('type_display', sa.String(), nullable=True),
        sa.Column('type_text', sa.String(), nullable=True),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('value', sa.String(), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('assigner', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['related_person_id'], ['related_person.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_related_person_identifier_related_person_id'), 'related_person_identifier', ['related_person_id'], unique=False)

    op.create_table(
        'related_person_relationship',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('related_person_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['related_person_id'], ['related_person.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_related_person_relationship_related_person_id'), 'related_person_relationship', ['related_person_id'], unique=False)

    op.create_table(
        'related_person_name',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('related_person_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('use', postgresql.ENUM(name='human_name_use', create_type=False), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('family', sa.String(), nullable=True),
        sa.Column('given', sa.Text(), nullable=True),
        sa.Column('prefix', sa.Text(), nullable=True),
        sa.Column('suffix', sa.Text(), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['related_person_id'], ['related_person.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_related_person_name_related_person_id'), 'related_person_name', ['related_person_id'], unique=False)

    op.create_table(
        'related_person_telecom',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('related_person_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('system', postgresql.ENUM(name='contact_point_system', create_type=False), nullable=True),
        sa.Column('value', sa.String(), nullable=True),
        sa.Column('use', postgresql.ENUM(name='contact_point_use', create_type=False), nullable=True),
        sa.Column('rank', sa.Integer(), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['related_person_id'], ['related_person.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_related_person_telecom_related_person_id'), 'related_person_telecom', ['related_person_id'], unique=False)

    op.create_table(
        'related_person_address',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('related_person_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('use', postgresql.ENUM(name='address_use', create_type=False), nullable=True),
        sa.Column('type', postgresql.ENUM(name='address_type', create_type=False), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('line', sa.Text(), nullable=True),
        sa.Column('city', sa.String(), nullable=True),
        sa.Column('district', sa.String(), nullable=True),
        sa.Column('state', sa.String(), nullable=True),
        sa.Column('postal_code', sa.String(), nullable=True),
        sa.Column('country', sa.String(), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['related_person_id'], ['related_person.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_related_person_address_related_person_id'), 'related_person_address', ['related_person_id'], unique=False)

    op.create_table(
        'related_person_photo',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('related_person_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('content_type', sa.String(), nullable=True),
        sa.Column('language', sa.String(), nullable=True),
        sa.Column('data', sa.Text(), nullable=True),
        sa.Column('url', sa.String(), nullable=True),
        sa.Column('size', sa.Integer(), nullable=True),
        sa.Column('hash', sa.String(), nullable=True),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('creation', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['related_person_id'], ['related_person.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_related_person_photo_related_person_id'), 'related_person_photo', ['related_person_id'], unique=False)

    op.create_table(
        'related_person_communication',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('related_person_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('language_system', sa.String(), nullable=True),
        sa.Column('language_code', sa.String(), nullable=True),
        sa.Column('language_display', sa.String(), nullable=True),
        sa.Column('language_text', sa.String(), nullable=True),
        sa.Column('preferred', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['related_person_id'], ['related_person.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_related_person_communication_related_person_id'), 'related_person_communication', ['related_person_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_related_person_communication_related_person_id'), table_name='related_person_communication')
    op.drop_table('related_person_communication')
    op.drop_index(op.f('ix_related_person_photo_related_person_id'), table_name='related_person_photo')
    op.drop_table('related_person_photo')
    op.drop_index(op.f('ix_related_person_address_related_person_id'), table_name='related_person_address')
    op.drop_table('related_person_address')
    op.drop_index(op.f('ix_related_person_telecom_related_person_id'), table_name='related_person_telecom')
    op.drop_table('related_person_telecom')
    op.drop_index(op.f('ix_related_person_name_related_person_id'), table_name='related_person_name')
    op.drop_table('related_person_name')
    op.drop_index(op.f('ix_related_person_relationship_related_person_id'), table_name='related_person_relationship')
    op.drop_table('related_person_relationship')
    op.drop_index(op.f('ix_related_person_identifier_related_person_id'), table_name='related_person_identifier')
    op.drop_table('related_person_identifier')
    op.drop_index(op.f('ix_related_person_user_id'), table_name='related_person')
    op.drop_index(op.f('ix_related_person_related_person_id'), table_name='related_person')
    op.drop_index(op.f('ix_related_person_patient_id'), table_name='related_person')
    op.drop_index(op.f('ix_related_person_org_id'), table_name='related_person')
    op.drop_index(op.f('ix_related_person_id'), table_name='related_person')
    op.drop_table('related_person')
    op.execute("DROP SEQUENCE IF EXISTS related_person_id_seq")
    bind = op.get_bind()
    _patient_ref.drop(bind, checkfirst=True)
