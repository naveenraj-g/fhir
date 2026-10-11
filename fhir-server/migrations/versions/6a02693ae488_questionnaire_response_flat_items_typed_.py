"""questionnaire_response_flat_items_typed_answers

Revision ID: 6a02693ae488
Revises: ebb3973f96ef
Create Date: 2026-10-10 18:03:59.382738

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6a02693ae488'
down_revision: Union[str, None] = 'ebb3973f96ef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


QR = 'questionnaire_response'
ITEM = 'questionnaire_response_item'
ANSWER = 'questionnaire_response_answer'


def upgrade() -> None:
    # questionnaire is 0..1 in R4
    op.alter_column(QR, 'questionnaire', existing_type=sa.String(), nullable=True)
    op.create_index(op.f('ix_questionnaire_response_questionnaire'), QR, ['questionnaire'], unique=False)

    # subject is Reference(Any): the enum (Patient|Group) becomes a free string.
    # The shared 'subject_reference_type' PG type is still used by Encounter/Appointment — do NOT drop it.
    op.alter_column(QR, 'subject_type', existing_type=sa.Enum('Patient', 'Group', name='subject_reference_type'),
                    type_=sa.String(), existing_nullable=True, postgresql_using='subject_type::text')

    # item: stable sibling order across the flat (all-depth) item rows. Existing rows keep insertion order.
    op.add_column(ITEM, sa.Column('position', sa.Integer(), nullable=False, server_default='0'))
    op.execute(f'UPDATE {ITEM} SET position = id')

    # answer: date / time / uri get their own typed columns instead of sharing value_string.
    op.add_column(ANSWER, sa.Column('value_date', sa.Date(), nullable=True))
    op.add_column(ANSWER, sa.Column('value_time', sa.String(), nullable=True))
    op.add_column(ANSWER, sa.Column('value_uri', sa.String(), nullable=True))
    op.execute(
        f"UPDATE {ANSWER} SET value_date = value_string::date, value_string = NULL "
        f"WHERE value_type = 'date' AND value_string ~ '^[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}$'"
    )
    op.execute(f"UPDATE {ANSWER} SET value_time = value_string, value_string = NULL WHERE value_type = 'time'")
    op.execute(f"UPDATE {ANSWER} SET value_uri = value_string, value_string = NULL WHERE value_type = 'uri'")


def downgrade() -> None:
    # Fold the typed columns back into value_string.
    op.execute(f"UPDATE {ANSWER} SET value_string = value_date::text WHERE value_type = 'date' AND value_date IS NOT NULL")
    op.execute(f"UPDATE {ANSWER} SET value_string = value_time WHERE value_type = 'time'")
    op.execute(f"UPDATE {ANSWER} SET value_string = value_uri WHERE value_type = 'uri'")
    op.drop_column(ANSWER, 'value_uri')
    op.drop_column(ANSWER, 'value_time')
    op.drop_column(ANSWER, 'value_date')
    op.drop_column(ITEM, 'position')

    # Subjects of types the old enum cannot hold are cleared before narrowing the column back.
    op.execute(f"UPDATE {QR} SET subject_type = NULL, subject_id = NULL WHERE subject_type NOT IN ('Patient', 'Group')")
    op.alter_column(QR, 'subject_type', existing_type=sa.String(),
                    type_=sa.Enum('Patient', 'Group', name='subject_reference_type'),
                    existing_nullable=True, postgresql_using='subject_type::subject_reference_type')

    op.drop_index(op.f('ix_questionnaire_response_questionnaire'), table_name=QR)
    op.execute(f"UPDATE {QR} SET questionnaire = '' WHERE questionnaire IS NULL")
    op.alter_column(QR, 'questionnaire', existing_type=sa.String(), nullable=False)
