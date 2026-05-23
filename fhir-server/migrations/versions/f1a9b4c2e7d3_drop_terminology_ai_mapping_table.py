"""drop terminology_ai_mapping table

Revision ID: f1a9b4c2e7d3
Revises: e5b2c3d1f8a9
Create Date: 2026-05-24
"""
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "f1a9b4c2e7d3"
down_revision: Union[str, None] = "e5b2c3d1f8a9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("terminology_ai_mapping")


def downgrade() -> None:
    op.create_table(
        "terminology_ai_mapping",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("phrase", sa.Text(), nullable=False),
        sa.Column("concept_id", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("source", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["concept_id"], ["terminology_concept.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_terminology_ai_mapping_phrase", "terminology_ai_mapping", ["phrase"])
    op.create_index("ix_terminology_ai_mapping_concept_id", "terminology_ai_mapping", ["concept_id"])
