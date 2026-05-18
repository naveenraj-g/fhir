"""add document_reference tables

Revision ID: b76fa05a80cc
Revises: 21ff251274d9
Create Date: 2026-05-18 18:51:31.412324

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b76fa05a80cc'
down_revision: Union[str, None] = '21ff251274d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_dr_status = postgresql.ENUM('current', 'superseded', 'entered-in-error', name='document_reference_status')
_dr_doc_status = postgresql.ENUM('preliminary', 'final', 'amended', 'entered-in-error', name='document_reference_doc_status')
_dr_subject_type = postgresql.ENUM('Patient', 'Practitioner', 'Group', 'Device', name='document_reference_subject_reference_type')
_dr_authenticator_type = postgresql.ENUM('Practitioner', 'PractitionerRole', 'Organization', name='document_reference_authenticator_reference_type')
_dr_author_type = postgresql.ENUM('Practitioner', 'PractitionerRole', 'Organization', 'Device', 'Patient', 'RelatedPerson', name='document_reference_author_reference_type')
_dr_relates_to_code = postgresql.ENUM('replaces', 'transforms', 'signs', 'appends', name='document_reference_relates_to_code')
_dr_relates_to_target_type = postgresql.ENUM('DocumentReference', name='document_reference_relates_to_target_type')
_dr_context_encounter_type = postgresql.ENUM('Encounter', 'EpisodeOfCare', name='document_reference_context_encounter_type')
_dr_context_source_patient_info_type = postgresql.ENUM('Patient', name='document_reference_context_source_patient_info_type')
_org_ref_type = postgresql.ENUM('Organization', name='organization_reference_type')


def upgrade() -> None:
    _dr_status.create(op.get_bind(), checkfirst=True)
    _dr_doc_status.create(op.get_bind(), checkfirst=True)
    _dr_subject_type.create(op.get_bind(), checkfirst=True)
    _dr_authenticator_type.create(op.get_bind(), checkfirst=True)
    _dr_author_type.create(op.get_bind(), checkfirst=True)
    _dr_relates_to_code.create(op.get_bind(), checkfirst=True)
    _dr_relates_to_target_type.create(op.get_bind(), checkfirst=True)
    _dr_context_encounter_type.create(op.get_bind(), checkfirst=True)
    _dr_context_source_patient_info_type.create(op.get_bind(), checkfirst=True)

    op.execute("CREATE SEQUENCE IF NOT EXISTS document_reference_id_seq START WITH 320000 INCREMENT BY 1")

    op.create_table('document_reference',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('document_reference_id', sa.Integer(), server_default=sa.text("nextval('document_reference_id_seq')"), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('master_identifier_use', sa.String(), nullable=True),
    sa.Column('master_identifier_type_system', sa.String(), nullable=True),
    sa.Column('master_identifier_type_code', sa.String(), nullable=True),
    sa.Column('master_identifier_type_display', sa.String(), nullable=True),
    sa.Column('master_identifier_type_text', sa.String(), nullable=True),
    sa.Column('master_identifier_system', sa.String(), nullable=True),
    sa.Column('master_identifier_value', sa.String(), nullable=True),
    sa.Column('master_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('master_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('master_identifier_assigner', sa.String(), nullable=True),
    sa.Column('status', postgresql.ENUM('current', 'superseded', 'entered-in-error', name='document_reference_status', create_type=False), nullable=False),
    sa.Column('doc_status', postgresql.ENUM('preliminary', 'final', 'amended', 'entered-in-error', name='document_reference_doc_status', create_type=False), nullable=True),
    sa.Column('type_system', sa.String(), nullable=True),
    sa.Column('type_code', sa.String(), nullable=True),
    sa.Column('type_display', sa.String(), nullable=True),
    sa.Column('type_text', sa.String(), nullable=True),
    sa.Column('subject_type', postgresql.ENUM('Patient', 'Practitioner', 'Group', 'Device', name='document_reference_subject_reference_type', create_type=False), nullable=True),
    sa.Column('subject_id', sa.Integer(), nullable=True),
    sa.Column('subject_display', sa.String(), nullable=True),
    sa.Column('date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('authenticator_type', postgresql.ENUM('Practitioner', 'PractitionerRole', 'Organization', name='document_reference_authenticator_reference_type', create_type=False), nullable=True),
    sa.Column('authenticator_id', sa.Integer(), nullable=True),
    sa.Column('authenticator_display', sa.String(), nullable=True),
    sa.Column('custodian_type', postgresql.ENUM('Organization', name='organization_reference_type', create_type=False), nullable=True),
    sa.Column('custodian_id', sa.Integer(), nullable=True),
    sa.Column('custodian_display', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('context_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('context_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('context_facility_type_system', sa.String(), nullable=True),
    sa.Column('context_facility_type_code', sa.String(), nullable=True),
    sa.Column('context_facility_type_display', sa.String(), nullable=True),
    sa.Column('context_facility_type_text', sa.String(), nullable=True),
    sa.Column('context_practice_setting_system', sa.String(), nullable=True),
    sa.Column('context_practice_setting_code', sa.String(), nullable=True),
    sa.Column('context_practice_setting_display', sa.String(), nullable=True),
    sa.Column('context_practice_setting_text', sa.String(), nullable=True),
    sa.Column('context_source_patient_info_type', postgresql.ENUM('Patient', name='document_reference_context_source_patient_info_type', create_type=False), nullable=True),
    sa.Column('context_source_patient_info_id', sa.Integer(), nullable=True),
    sa.Column('context_source_patient_info_display', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_by', sa.String(), nullable=True),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['custodian_id'], ['organization.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_reference_custodian_id'), 'document_reference', ['custodian_id'], unique=False)
    op.create_index(op.f('ix_document_reference_document_reference_id'), 'document_reference', ['document_reference_id'], unique=True)
    op.create_index(op.f('ix_document_reference_id'), 'document_reference', ['id'], unique=False)
    op.create_index(op.f('ix_document_reference_org_id'), 'document_reference', ['org_id'], unique=False)
    op.create_index(op.f('ix_document_reference_user_id'), 'document_reference', ['user_id'], unique=False)

    op.create_table('document_reference_author',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('document_reference_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('reference_type', postgresql.ENUM('Practitioner', 'PractitionerRole', 'Organization', 'Device', 'Patient', 'RelatedPerson', name='document_reference_author_reference_type', create_type=False), nullable=True),
    sa.Column('reference_id', sa.Integer(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['document_reference_id'], ['document_reference.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_reference_author_document_reference_id'), 'document_reference_author', ['document_reference_id'], unique=False)

    op.create_table('document_reference_category',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('document_reference_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('coding_system', sa.String(), nullable=True),
    sa.Column('coding_code', sa.String(), nullable=True),
    sa.Column('coding_display', sa.String(), nullable=True),
    sa.Column('text', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['document_reference_id'], ['document_reference.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_reference_category_document_reference_id'), 'document_reference_category', ['document_reference_id'], unique=False)

    op.create_table('document_reference_content',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('document_reference_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('attachment_content_type', sa.String(), nullable=True),
    sa.Column('attachment_language', sa.String(), nullable=True),
    sa.Column('attachment_data', sa.Text(), nullable=True),
    sa.Column('attachment_url', sa.String(), nullable=True),
    sa.Column('attachment_size', sa.Integer(), nullable=True),
    sa.Column('attachment_hash', sa.String(), nullable=True),
    sa.Column('attachment_title', sa.String(), nullable=True),
    sa.Column('attachment_creation', sa.DateTime(timezone=True), nullable=True),
    sa.Column('format_system', sa.String(), nullable=True),
    sa.Column('format_version', sa.String(), nullable=True),
    sa.Column('format_code', sa.String(), nullable=True),
    sa.Column('format_display', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['document_reference_id'], ['document_reference.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_reference_content_document_reference_id'), 'document_reference_content', ['document_reference_id'], unique=False)

    op.create_table('document_reference_context_encounter',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('document_reference_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('reference_type', postgresql.ENUM('Encounter', 'EpisodeOfCare', name='document_reference_context_encounter_type', create_type=False), nullable=True),
    sa.Column('reference_id', sa.Integer(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['document_reference_id'], ['document_reference.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_reference_context_encounter_document_reference_id'), 'document_reference_context_encounter', ['document_reference_id'], unique=False)

    op.create_table('document_reference_context_event',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('document_reference_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('coding_system', sa.String(), nullable=True),
    sa.Column('coding_code', sa.String(), nullable=True),
    sa.Column('coding_display', sa.String(), nullable=True),
    sa.Column('text', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['document_reference_id'], ['document_reference.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_reference_context_event_document_reference_id'), 'document_reference_context_event', ['document_reference_id'], unique=False)

    op.create_table('document_reference_context_related',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('document_reference_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('reference_type', sa.String(), nullable=True),
    sa.Column('reference_id', sa.Integer(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['document_reference_id'], ['document_reference.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_reference_context_related_document_reference_id'), 'document_reference_context_related', ['document_reference_id'], unique=False)

    op.create_table('document_reference_identifier',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('document_reference_id', sa.Integer(), nullable=False),
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
    sa.ForeignKeyConstraint(['document_reference_id'], ['document_reference.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_reference_identifier_document_reference_id'), 'document_reference_identifier', ['document_reference_id'], unique=False)

    op.create_table('document_reference_relates_to',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('document_reference_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('code', postgresql.ENUM('replaces', 'transforms', 'signs', 'appends', name='document_reference_relates_to_code', create_type=False), nullable=False),
    sa.Column('target_type', postgresql.ENUM('DocumentReference', name='document_reference_relates_to_target_type', create_type=False), nullable=True),
    sa.Column('target_id', sa.Integer(), nullable=True),
    sa.Column('target_display', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['document_reference_id'], ['document_reference.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_reference_relates_to_document_reference_id'), 'document_reference_relates_to', ['document_reference_id'], unique=False)

    op.create_table('document_reference_security_label',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('document_reference_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('coding_system', sa.String(), nullable=True),
    sa.Column('coding_code', sa.String(), nullable=True),
    sa.Column('coding_display', sa.String(), nullable=True),
    sa.Column('text', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['document_reference_id'], ['document_reference.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_reference_security_label_document_reference_id'), 'document_reference_security_label', ['document_reference_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_document_reference_security_label_document_reference_id'), table_name='document_reference_security_label')
    op.drop_table('document_reference_security_label')
    op.drop_index(op.f('ix_document_reference_relates_to_document_reference_id'), table_name='document_reference_relates_to')
    op.drop_table('document_reference_relates_to')
    op.drop_index(op.f('ix_document_reference_identifier_document_reference_id'), table_name='document_reference_identifier')
    op.drop_table('document_reference_identifier')
    op.drop_index(op.f('ix_document_reference_context_related_document_reference_id'), table_name='document_reference_context_related')
    op.drop_table('document_reference_context_related')
    op.drop_index(op.f('ix_document_reference_context_event_document_reference_id'), table_name='document_reference_context_event')
    op.drop_table('document_reference_context_event')
    op.drop_index(op.f('ix_document_reference_context_encounter_document_reference_id'), table_name='document_reference_context_encounter')
    op.drop_table('document_reference_context_encounter')
    op.drop_index(op.f('ix_document_reference_content_document_reference_id'), table_name='document_reference_content')
    op.drop_table('document_reference_content')
    op.drop_index(op.f('ix_document_reference_category_document_reference_id'), table_name='document_reference_category')
    op.drop_table('document_reference_category')
    op.drop_index(op.f('ix_document_reference_author_document_reference_id'), table_name='document_reference_author')
    op.drop_table('document_reference_author')
    op.drop_index(op.f('ix_document_reference_user_id'), table_name='document_reference')
    op.drop_index(op.f('ix_document_reference_org_id'), table_name='document_reference')
    op.drop_index(op.f('ix_document_reference_id'), table_name='document_reference')
    op.drop_index(op.f('ix_document_reference_document_reference_id'), table_name='document_reference')
    op.drop_index(op.f('ix_document_reference_custodian_id'), table_name='document_reference')
    op.drop_table('document_reference')

    op.execute("DROP SEQUENCE IF EXISTS document_reference_id_seq")

    _dr_context_source_patient_info_type.drop(op.get_bind(), checkfirst=True)
    _dr_context_encounter_type.drop(op.get_bind(), checkfirst=True)
    _dr_relates_to_target_type.drop(op.get_bind(), checkfirst=True)
    _dr_relates_to_code.drop(op.get_bind(), checkfirst=True)
    _dr_author_type.drop(op.get_bind(), checkfirst=True)
    _dr_authenticator_type.drop(op.get_bind(), checkfirst=True)
    _dr_subject_type.drop(op.get_bind(), checkfirst=True)
    _dr_doc_status.drop(op.get_bind(), checkfirst=True)
    _dr_status.drop(op.get_bind(), checkfirst=True)
