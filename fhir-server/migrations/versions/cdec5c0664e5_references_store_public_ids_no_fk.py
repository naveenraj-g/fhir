"""references_store_public_ids_no_fk

Revision ID: cdec5c0664e5
Revises: f586e8ee64f9
Create Date: 2026-10-10 19:21:08.871930

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cdec5c0664e5'
down_revision: Union[str, None] = 'f586e8ee64f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# References to OTHER resources are stored as type / public id / display only — never as a real foreign key.
# (table, column, referenced table, referenced public-id column)
_REFS = (
    ('procedure', 'encounter_id', 'encounter', 'encounter_id'),
    ('flag', 'encounter_id', 'encounter', 'encounter_id'),
    ('risk_assessment', 'encounter_id', 'encounter', 'encounter_id'),
    ('questionnaire_response', 'encounter_id', 'encounter', 'encounter_id'),
    ('episode_of_care', 'managing_organization_id', 'organization', 'organization_id'),
)


def _drop_fk(table: str, column: str) -> None:
    """Drop whichever foreign-key constraint covers `table.column` (the name is auto-generated)."""
    inspector = sa.inspect(op.get_bind())
    for fk in inspector.get_foreign_keys(table):
        if fk['constrained_columns'] == [column] and fk.get('name'):
            op.drop_constraint(fk['name'], table, type_='foreignkey')


def upgrade() -> None:
    for table, column, ref_table, ref_public in _REFS:
        # The column held the referenced row's INTERNAL id; rewrite it to the PUBLIC id first.
        op.execute(
            f'UPDATE {table} t SET {column} = r.{ref_public} FROM {ref_table} r WHERE r.id = t.{column}'
        )
        _drop_fk(table, column)


def downgrade() -> None:
    for table, column, ref_table, ref_public in _REFS:
        # Public ids with no matching row cannot satisfy the FK, so they are cleared.
        op.execute(
            f'UPDATE {table} t SET {column} = NULL '
            f'WHERE t.{column} IS NOT NULL AND NOT EXISTS (SELECT 1 FROM {ref_table} r WHERE r.{ref_public} = t.{column})'
        )
        op.execute(
            f'UPDATE {table} t SET {column} = r.id FROM {ref_table} r WHERE r.{ref_public} = t.{column}'
        )
        op.create_foreign_key(None, table, ref_table, [column], ['id'])
