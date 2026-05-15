"""refactor_condition_enums_and_identifier_fields

Revision ID: 60bbcdee864b
Revises: 2522e6ba4657
Create Date: 2026-05-15 22:42:52.527101

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '60bbcdee864b'
down_revision: Union[str, None] = '2522e6ba4657'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_note_author_ref = postgresql.ENUM(
    'Practitioner', 'Patient', 'RelatedPerson', 'Organization',
    name='condition_note_author_ref_type',
)


def upgrade() -> None:
    bind = op.get_bind()

    # ── 1. Main table: add missing CodeableConcept text columns ──────────────
    op.add_column('condition', sa.Column('clinical_status_text', sa.String(), nullable=True))
    op.add_column('condition', sa.Column('verification_status_text', sa.String(), nullable=True))

    # ── 2. condition_identifier: add type_text ────────────────────────────────
    op.add_column('condition_identifier', sa.Column('type_text', sa.String(), nullable=True))

    # ── 3. condition_note: String → Enum + rename author_display ─────────────
    _note_author_ref.create(bind, checkfirst=True)
    op.alter_column(
        'condition_note', 'author_reference_type',
        existing_type=sa.VARCHAR(),
        type_=postgresql.ENUM(
            'Practitioner', 'Patient', 'RelatedPerson', 'Organization',
            name='condition_note_author_ref_type', create_type=False,
        ),
        existing_nullable=True,
        postgresql_using='author_reference_type::condition_note_author_ref_type',
    )
    op.alter_column('condition_note', 'author_display',
                    new_column_name='author_reference_display')


def downgrade() -> None:
    bind = op.get_bind()

    # ── Reverse note ──────────────────────────────────────────────────────────
    op.alter_column('condition_note', 'author_reference_display',
                    new_column_name='author_display')
    op.alter_column(
        'condition_note', 'author_reference_type',
        existing_type=postgresql.ENUM(
            'Practitioner', 'Patient', 'RelatedPerson', 'Organization',
            name='condition_note_author_ref_type', create_type=False,
        ),
        type_=sa.VARCHAR(),
        existing_nullable=True,
    )
    _note_author_ref.drop(bind, checkfirst=True)

    # ── Reverse added columns ─────────────────────────────────────────────────
    op.drop_column('condition_identifier', 'type_text')
    op.drop_column('condition', 'verification_status_text')
    op.drop_column('condition', 'clinical_status_text')
