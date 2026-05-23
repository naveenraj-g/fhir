"""add pg_trgm extension and trigram GIN index on terminology_concept.display

Revision ID: e5b2c3d1f8a9
Revises: d4e8f932a015
Create Date: 2026-05-23
"""
from typing import Union

from alembic import op

revision: str = "e5b2c3d1f8a9"
down_revision: Union[str, None] = "d4e8f932a015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.create_index(
        "ix_terminology_concept_display_trgm",
        "terminology_concept",
        ["display"],
        postgresql_using="gin",
        postgresql_ops={"display": "gin_trgm_ops"},
    )


def downgrade() -> None:
    op.drop_index(
        "ix_terminology_concept_display_trgm", table_name="terminology_concept"
    )
