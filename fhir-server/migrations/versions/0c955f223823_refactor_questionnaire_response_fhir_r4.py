"""refactor_questionnaire_response_fhir_r4

Revision ID: 0c955f223823
Revises: dc849f11b34e
Create Date: 2026-05-14 22:48:27.052464

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0c955f223823'
down_revision: Union[str, None] = 'dc849f11b34e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # op.create_table auto-creates its enum types — clean up any orphaned types
    # from a previously failed run before letting create_table recreate them.
    op.execute("DROP TYPE IF EXISTS qr_based_on_reference_type")
    op.execute("DROP TYPE IF EXISTS qr_part_of_reference_type")

    op.create_table(
        'questionnaire_response_based_on',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('response_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('reference_type', sa.Enum('CarePlan', 'ServiceRequest', name='qr_based_on_reference_type'), nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['response_id'], ['questionnaire_response.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_questionnaire_response_based_on_response_id'),
        'questionnaire_response_based_on', ['response_id'], unique=False,
    )

    op.create_table(
        'questionnaire_response_part_of',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('response_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('reference_type', sa.Enum('Observation', 'Procedure', name='qr_part_of_reference_type'), nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['response_id'], ['questionnaire_response.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_questionnaire_response_part_of_response_id'),
        'questionnaire_response_part_of', ['response_id'], unique=False,
    )

    # identifier_use is used in op.add_column — must be pre-created manually
    op.execute("DROP TYPE IF EXISTS identifier_use")
    op.execute("CREATE TYPE identifier_use AS ENUM ('usual', 'official', 'temp', 'secondary', 'old')")

    op.add_column('questionnaire_response', sa.Column(
        'identifier_use',
        sa.Enum('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False),
        nullable=True,
    ))
    op.add_column('questionnaire_response', sa.Column('identifier_type_system', sa.String(), nullable=True))
    op.add_column('questionnaire_response', sa.Column('identifier_type_code', sa.String(), nullable=True))
    op.add_column('questionnaire_response', sa.Column('identifier_type_display', sa.String(), nullable=True))
    op.add_column('questionnaire_response', sa.Column('identifier_type_text', sa.String(), nullable=True))
    op.add_column('questionnaire_response', sa.Column('identifier_system', sa.String(), nullable=True))
    op.add_column('questionnaire_response', sa.Column('identifier_value', sa.String(), nullable=True))
    op.add_column('questionnaire_response', sa.Column('identifier_period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('questionnaire_response', sa.Column('identifier_period_end', sa.DateTime(timezone=True), nullable=True))
    op.add_column('questionnaire_response', sa.Column('identifier_assigner', sa.String(), nullable=True))

    # valueAttachment columns on questionnaire_response_answer
    op.add_column('questionnaire_response_answer', sa.Column('value_attachment_content_type', sa.String(), nullable=True))
    op.add_column('questionnaire_response_answer', sa.Column('value_attachment_language', sa.String(), nullable=True))
    op.add_column('questionnaire_response_answer', sa.Column('value_attachment_data', sa.Text(), nullable=True))
    op.add_column('questionnaire_response_answer', sa.Column('value_attachment_url', sa.String(), nullable=True))
    op.add_column('questionnaire_response_answer', sa.Column('value_attachment_size', sa.Integer(), nullable=True))
    op.add_column('questionnaire_response_answer', sa.Column('value_attachment_hash', sa.String(), nullable=True))
    op.add_column('questionnaire_response_answer', sa.Column('value_attachment_title', sa.String(), nullable=True))
    op.add_column('questionnaire_response_answer', sa.Column('value_attachment_creation', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('questionnaire_response_answer', 'value_attachment_creation')
    op.drop_column('questionnaire_response_answer', 'value_attachment_title')
    op.drop_column('questionnaire_response_answer', 'value_attachment_hash')
    op.drop_column('questionnaire_response_answer', 'value_attachment_size')
    op.drop_column('questionnaire_response_answer', 'value_attachment_url')
    op.drop_column('questionnaire_response_answer', 'value_attachment_data')
    op.drop_column('questionnaire_response_answer', 'value_attachment_language')
    op.drop_column('questionnaire_response_answer', 'value_attachment_content_type')
    op.drop_column('questionnaire_response', 'identifier_assigner')
    op.drop_column('questionnaire_response', 'identifier_period_end')
    op.drop_column('questionnaire_response', 'identifier_period_start')
    op.drop_column('questionnaire_response', 'identifier_value')
    op.drop_column('questionnaire_response', 'identifier_system')
    op.drop_column('questionnaire_response', 'identifier_type_text')
    op.drop_column('questionnaire_response', 'identifier_type_display')
    op.drop_column('questionnaire_response', 'identifier_type_code')
    op.drop_column('questionnaire_response', 'identifier_type_system')
    op.drop_column('questionnaire_response', 'identifier_use')
    op.drop_index(op.f('ix_questionnaire_response_part_of_response_id'), table_name='questionnaire_response_part_of')
    op.drop_table('questionnaire_response_part_of')
    op.drop_index(op.f('ix_questionnaire_response_based_on_response_id'), table_name='questionnaire_response_based_on')
    op.drop_table('questionnaire_response_based_on')
    op.execute("DROP TYPE IF EXISTS identifier_use")
    op.execute("DROP TYPE IF EXISTS qr_based_on_reference_type")
    op.execute("DROP TYPE IF EXISTS qr_part_of_reference_type")
