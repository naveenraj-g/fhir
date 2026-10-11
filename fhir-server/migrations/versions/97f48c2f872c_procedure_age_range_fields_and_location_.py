"""procedure_age_range_fields_and_location_id

Revision ID: 97f48c2f872c
Revises: 5af1e4b943fe
Create Date: 2026-10-10 17:36:07.088107

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '97f48c2f872c'
down_revision: Union[str, None] = '5af1e4b943fe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_NEW_COLUMNS = (
    "performed_age_comparator",
    "performed_range_low_system",
    "performed_range_low_code",
    "performed_range_high_system",
    "performed_range_high_code",
)


def upgrade() -> None:
    for name in _NEW_COLUMNS:
        op.add_column('procedure', sa.Column(name, sa.String(), nullable=True))
    op.alter_column('procedure', 'location_reference_id', new_column_name='location_id')


def downgrade() -> None:
    op.alter_column('procedure', 'location_id', new_column_name='location_reference_id')
    for name in reversed(_NEW_COLUMNS):
        op.drop_column('procedure', name)
