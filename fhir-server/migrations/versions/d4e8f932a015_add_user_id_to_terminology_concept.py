"""add user_id to terminology_concept

Revision ID: d4e8f932a015
Revises: c3d7e921f04a
Create Date: 2026-05-21
"""
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "d4e8f932a015"
down_revision: Union[str, None] = "c3d7e921f04a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "terminology_concept",
        sa.Column("user_id", sa.String(), nullable=True),
    )
    op.create_index(
        "ix_terminology_concept_user_id",
        "terminology_concept",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_terminology_concept_user_id", table_name="terminology_concept")
    op.drop_column("terminology_concept", "user_id")
