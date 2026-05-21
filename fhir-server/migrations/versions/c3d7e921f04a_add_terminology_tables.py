"""add terminology tables

Revision ID: c3d7e921f04a
Revises: 6fe394d10fac
Create Date: 2026-05-21 10:00:00.000000

Creates 12 tables for the FHIR terminology platform:
  terminology_code_system, terminology_concept, terminology_concept_synonym,
  terminology_concept_translation, terminology_relationship, terminology_value_set,
  terminology_value_set_concept, terminology_field_binding, terminology_ai_mapping,
  terminology_concept_embedding, terminology_audit_log, terminology_concept_map

Uses two partial unique indexes on terminology_concept to correctly handle
NULL org_id (standard global codes) vs non-NULL org_id (org-specific codes).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c3d7e921f04a"
down_revision: Union[str, None] = "6fe394d10fac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. terminology_code_system ─────────────────────────────────────────────
    op.create_table(
        "terminology_code_system",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("canonical_url", sa.String, nullable=False),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("title", sa.String, nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("version", sa.String, nullable=True),
        sa.Column("fhir_version", sa.String, nullable=True),
        sa.Column("publisher", sa.String, nullable=True),
        sa.Column("jurisdiction", sa.String, nullable=True),
        sa.Column("content_mode", sa.String, nullable=True),
        sa.Column("experimental", sa.Boolean, server_default=sa.false()),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("canonical_url", name="uq_terminology_code_system_url"),
    )
    op.create_index(
        "ix_terminology_code_system_canonical_url",
        "terminology_code_system",
        ["canonical_url"],
    )

    # ── 2. terminology_concept ─────────────────────────────────────────────────
    op.create_table(
        "terminology_concept",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "code_system_id",
            sa.Integer,
            sa.ForeignKey("terminology_code_system.id"),
            nullable=False,
        ),
        sa.Column("code", sa.String, nullable=False),
        sa.Column("display", sa.String, nullable=False),
        sa.Column("definition", sa.Text, nullable=True),
        sa.Column("active", sa.Boolean, server_default=sa.true()),
        sa.Column("deprecated", sa.Boolean, server_default=sa.false()),
        sa.Column(
            "parent_concept_id",
            sa.Integer,
            sa.ForeignKey("terminology_concept.id"),
            nullable=True,
        ),
        sa.Column(
            "search_vector", postgresql.TSVECTOR, nullable=True
        ),
        sa.Column("org_id", sa.String, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_terminology_concept_code_system_id",
        "terminology_concept",
        ["code_system_id"],
    )
    op.create_index("ix_terminology_concept_code", "terminology_concept", ["code"])
    op.create_index("ix_terminology_concept_org_id", "terminology_concept", ["org_id"])
    op.create_index(
        "ix_terminology_concept_parent_concept_id",
        "terminology_concept",
        ["parent_concept_id"],
    )
    # GIN index for full-text search via tsvector
    op.create_index(
        "ix_terminology_concept_search_vector",
        "terminology_concept",
        ["search_vector"],
        postgresql_using="gin",
    )
    # Partial unique indexes — correctly handle NULL org_id in PostgreSQL
    # (a plain UNIQUE(code_system_id, code, org_id) would allow duplicate globals
    #  because NULL != NULL in standard unique constraints)
    op.execute(
        """
        CREATE UNIQUE INDEX uq_tc_global
        ON terminology_concept (code_system_id, code)
        WHERE org_id IS NULL
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_tc_org
        ON terminology_concept (code_system_id, code, org_id)
        WHERE org_id IS NOT NULL
        """
    )

    # ── 3. terminology_concept_synonym ─────────────────────────────────────────
    op.create_table(
        "terminology_concept_synonym",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "concept_id",
            sa.Integer,
            sa.ForeignKey("terminology_concept.id"),
            nullable=False,
        ),
        sa.Column("synonym", sa.String, nullable=False),
    )
    op.create_index(
        "ix_terminology_concept_synonym_concept_id",
        "terminology_concept_synonym",
        ["concept_id"],
    )

    # ── 4. terminology_concept_translation ────────────────────────────────────
    op.create_table(
        "terminology_concept_translation",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "concept_id",
            sa.Integer,
            sa.ForeignKey("terminology_concept.id"),
            nullable=False,
        ),
        sa.Column("language_code", sa.String, nullable=False),
        sa.Column("display", sa.String, nullable=False),
        sa.UniqueConstraint(
            "concept_id",
            "language_code",
            name="uq_terminology_concept_translation",
        ),
    )
    op.create_index(
        "ix_terminology_concept_translation_concept_id",
        "terminology_concept_translation",
        ["concept_id"],
    )

    # ── 5. terminology_relationship ───────────────────────────────────────────
    op.create_table(
        "terminology_relationship",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "parent_concept_id",
            sa.Integer,
            sa.ForeignKey("terminology_concept.id"),
            nullable=False,
        ),
        sa.Column(
            "child_concept_id",
            sa.Integer,
            sa.ForeignKey("terminology_concept.id"),
            nullable=False,
        ),
        sa.Column("relationship_type", sa.String, nullable=False),
        sa.UniqueConstraint(
            "parent_concept_id",
            "child_concept_id",
            "relationship_type",
            name="uq_terminology_relationship",
        ),
    )
    op.create_index(
        "ix_terminology_relationship_parent",
        "terminology_relationship",
        ["parent_concept_id"],
    )
    op.create_index(
        "ix_terminology_relationship_child",
        "terminology_relationship",
        ["child_concept_id"],
    )

    # ── 6. terminology_value_set ──────────────────────────────────────────────
    op.create_table(
        "terminology_value_set",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("canonical_url", sa.String, nullable=False),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("title", sa.String, nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("version", sa.String, nullable=True),
        sa.Column("fhir_version", sa.String, nullable=True),
        sa.Column("binding_strength", sa.String, nullable=False),
        sa.Column("experimental", sa.Boolean, server_default=sa.false()),
        sa.Column("active", sa.Boolean, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("canonical_url", name="uq_terminology_value_set_url"),
    )
    op.create_index(
        "ix_terminology_value_set_canonical_url",
        "terminology_value_set",
        ["canonical_url"],
    )

    # ── 7. terminology_value_set_concept ──────────────────────────────────────
    op.create_table(
        "terminology_value_set_concept",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "value_set_id",
            sa.Integer,
            sa.ForeignKey("terminology_value_set.id"),
            nullable=False,
        ),
        sa.Column(
            "concept_id",
            sa.Integer,
            sa.ForeignKey("terminology_concept.id"),
            nullable=False,
        ),
        sa.Column("active", sa.Boolean, server_default=sa.true()),
        sa.UniqueConstraint(
            "value_set_id", "concept_id", name="uq_terminology_value_set_concept"
        ),
    )
    op.create_index(
        "ix_terminology_value_set_concept_vs",
        "terminology_value_set_concept",
        ["value_set_id"],
    )
    op.create_index(
        "ix_terminology_value_set_concept_c",
        "terminology_value_set_concept",
        ["concept_id"],
    )

    # ── 8. terminology_field_binding ──────────────────────────────────────────
    op.create_table(
        "terminology_field_binding",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("resource_type", sa.String, nullable=False),
        sa.Column("field_name", sa.String, nullable=False),
        sa.Column(
            "value_set_id",
            sa.Integer,
            sa.ForeignKey("terminology_value_set.id"),
            nullable=False,
        ),
        sa.Column("binding_strength", sa.String, nullable=False),
        sa.Column("multiple_allowed", sa.Boolean, server_default=sa.false()),
        sa.Column("active", sa.Boolean, server_default=sa.true()),
        sa.UniqueConstraint(
            "resource_type", "field_name", name="uq_terminology_field_binding"
        ),
    )
    op.create_index(
        "ix_terminology_field_binding_resource_type",
        "terminology_field_binding",
        ["resource_type"],
    )

    # ── 9. terminology_ai_mapping ─────────────────────────────────────────────
    op.create_table(
        "terminology_ai_mapping",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("phrase", sa.Text, nullable=False),
        sa.Column(
            "concept_id",
            sa.Integer,
            sa.ForeignKey("terminology_concept.id"),
            nullable=False,
        ),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column("source", sa.String, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_terminology_ai_mapping_concept_id",
        "terminology_ai_mapping",
        ["concept_id"],
    )

    # ── 10. terminology_concept_embedding ─────────────────────────────────────
    op.create_table(
        "terminology_concept_embedding",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "concept_id",
            sa.Integer,
            sa.ForeignKey("terminology_concept.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("embedding", postgresql.JSONB, nullable=True),
        sa.Column("model", sa.String, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_terminology_concept_embedding_concept_id",
        "terminology_concept_embedding",
        ["concept_id"],
    )

    # ── 11. terminology_audit_log ─────────────────────────────────────────────
    op.create_table(
        "terminology_audit_log",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("action", sa.String, nullable=False),
        sa.Column(
            "concept_id",
            sa.Integer,
            sa.ForeignKey("terminology_concept.id"),
            nullable=True,
        ),
        sa.Column(
            "value_set_id",
            sa.Integer,
            sa.ForeignKey("terminology_value_set.id"),
            nullable=True,
        ),
        sa.Column("performed_by", sa.String, nullable=True),
        sa.Column("old_value", postgresql.JSONB, nullable=True),
        sa.Column("new_value", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_terminology_audit_log_action", "terminology_audit_log", ["action"]
    )
    op.create_index(
        "ix_terminology_audit_log_concept_id",
        "terminology_audit_log",
        ["concept_id"],
    )

    # ── 12. terminology_concept_map ───────────────────────────────────────────
    op.create_table(
        "terminology_concept_map",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "source_concept_id",
            sa.Integer,
            sa.ForeignKey("terminology_concept.id"),
            nullable=False,
        ),
        sa.Column(
            "target_concept_id",
            sa.Integer,
            sa.ForeignKey("terminology_concept.id"),
            nullable=False,
        ),
        sa.Column("mapping_type", sa.String, nullable=True),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "source_concept_id",
            "target_concept_id",
            "mapping_type",
            name="uq_terminology_concept_map",
        ),
    )
    op.create_index(
        "ix_terminology_concept_map_source",
        "terminology_concept_map",
        ["source_concept_id"],
    )
    op.create_index(
        "ix_terminology_concept_map_target",
        "terminology_concept_map",
        ["target_concept_id"],
    )


def downgrade() -> None:
    op.drop_table("terminology_concept_map")
    op.drop_table("terminology_audit_log")
    op.drop_table("terminology_concept_embedding")
    op.drop_table("terminology_ai_mapping")
    op.drop_table("terminology_field_binding")
    op.drop_table("terminology_value_set_concept")
    op.drop_table("terminology_value_set")
    op.drop_table("terminology_relationship")
    op.drop_table("terminology_concept_translation")
    op.drop_table("terminology_concept_synonym")
    op.drop_table("terminology_concept")
    op.drop_table("terminology_code_system")
