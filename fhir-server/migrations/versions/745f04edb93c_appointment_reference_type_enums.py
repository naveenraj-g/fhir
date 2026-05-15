"""appointment_reference_type_enums

Revision ID: 745f04edb93c
Revises: 40aa37fd680f
Create Date: 2026-05-15 14:53:14.438913

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '745f04edb93c'
down_revision: Union[str, None] = '40aa37fd680f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_reason_ref_type = postgresql.ENUM(
    'Condition', 'Procedure', 'Observation', 'ImmunizationRecommendation', 'DiagnosticReport',
    name='appointment_reason_reference_type',
)
_note_author_ref_type = postgresql.ENUM(
    'Practitioner', 'PractitionerRole', 'Patient', 'RelatedPerson', 'Organization',
    name='appointment_note_author_reference_type',
)
_pi_ref_type = postgresql.ENUM(
    'DocumentReference',
    name='appointment_pi_reference_type',
)


def upgrade() -> None:
    _reason_ref_type.create(op.get_bind(), checkfirst=True)
    _note_author_ref_type.create(op.get_bind(), checkfirst=True)
    _pi_ref_type.create(op.get_bind(), checkfirst=True)

    op.alter_column(
        'appointment_reason', 'reference_type',
        existing_type=sa.VARCHAR(),
        type_=_reason_ref_type,
        existing_nullable=True,
        postgresql_using='reference_type::appointment_reason_reference_type',
    )
    op.alter_column(
        'appointment_note', 'author_reference_type',
        existing_type=sa.VARCHAR(),
        type_=_note_author_ref_type,
        existing_nullable=True,
        postgresql_using='author_reference_type::appointment_note_author_reference_type',
    )
    op.alter_column(
        'appointment_patient_instruction', 'reference_type',
        existing_type=sa.VARCHAR(),
        type_=_pi_ref_type,
        existing_nullable=True,
        postgresql_using='reference_type::appointment_pi_reference_type',
    )


def downgrade() -> None:
    op.alter_column(
        'appointment_reason', 'reference_type',
        existing_type=_reason_ref_type,
        type_=sa.VARCHAR(),
        existing_nullable=True,
    )
    op.alter_column(
        'appointment_note', 'author_reference_type',
        existing_type=_note_author_ref_type,
        type_=sa.VARCHAR(),
        existing_nullable=True,
    )
    op.alter_column(
        'appointment_patient_instruction', 'reference_type',
        existing_type=_pi_ref_type,
        type_=sa.VARCHAR(),
        existing_nullable=True,
    )
    _reason_ref_type.drop(op.get_bind(), checkfirst=True)
    _note_author_ref_type.drop(op.get_bind(), checkfirst=True)
    _pi_ref_type.drop(op.get_bind(), checkfirst=True)
