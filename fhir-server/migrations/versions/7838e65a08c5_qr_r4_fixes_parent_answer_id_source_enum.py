"""qr_r4_fixes_parent_answer_id_source_enum

Revision ID: 7838e65a08c5
Revises: 986e9cd5def8
Create Date: 2026-05-15 18:54:27.172588

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7838e65a08c5'
down_revision: Union[str, None] = '986e9cd5def8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# R4 source enum — no Device or Organization (those are R5-only)
_source_ref_type_r4 = postgresql.ENUM(
    'Patient', 'Practitioner', 'PractitionerRole', 'RelatedPerson',
    name='source_reference_type',
)


def upgrade() -> None:
    # 1. value_type → nullable (R4 answer value[x] is 0..1)
    op.alter_column('questionnaire_response_answer', 'value_type',
                    existing_type=sa.VARCHAR(), nullable=True)

    # 2. parent_answer_id — items nested under an answer (R4 item.answer.item)
    op.add_column('questionnaire_response_item',
                  sa.Column('parent_answer_id', sa.Integer(), nullable=True))
    op.create_index(
        op.f('ix_questionnaire_response_item_parent_answer_id'),
        'questionnaire_response_item', ['parent_answer_id'], unique=False,
    )
    op.create_foreign_key(
        'fk_qr_item_parent_answer_id',
        'questionnaire_response_item', 'questionnaire_response_answer',
        ['parent_answer_id'], ['id'],
    )

    # 3. Fix source_reference_type PG enum — remove R5-only Device and Organization
    #    PostgreSQL cannot remove enum values; must drop column, drop type, recreate.
    op.drop_column('questionnaire_response', 'source_type')
    op.execute('DROP TYPE IF EXISTS source_reference_type')
    _source_ref_type_r4.create(op.get_bind(), checkfirst=True)
    op.add_column('questionnaire_response', sa.Column(
        'source_type',
        postgresql.ENUM('Patient', 'Practitioner', 'PractitionerRole', 'RelatedPerson',
                        name='source_reference_type', create_type=False),
        nullable=True,
    ))


def downgrade() -> None:
    # Reverse parent_answer_id
    op.drop_constraint('fk_qr_item_parent_answer_id', 'questionnaire_response_item', type_='foreignkey')
    op.drop_index(op.f('ix_questionnaire_response_item_parent_answer_id'),
                  table_name='questionnaire_response_item')
    op.drop_column('questionnaire_response_item', 'parent_answer_id')

    # Reverse value_type nullable
    op.alter_column('questionnaire_response_answer', 'value_type',
                    existing_type=sa.VARCHAR(), nullable=False)

    # Restore R5 source enum (with Device + Organization)
    op.drop_column('questionnaire_response', 'source_type')
    op.execute('DROP TYPE IF EXISTS source_reference_type')
    op.execute("CREATE TYPE source_reference_type AS ENUM ('Device', 'Organization', 'Patient', 'Practitioner', 'PractitionerRole', 'RelatedPerson')")
    op.add_column('questionnaire_response', sa.Column(
        'source_type',
        postgresql.ENUM('Device', 'Organization', 'Patient', 'Practitioner', 'PractitionerRole', 'RelatedPerson',
                        name='source_reference_type', create_type=False),
        nullable=True,
    ))
