"""fix_organization_references_to_enum

Revision ID: 2cba83ec392a
Revises: 7536981d5a01
Create Date: 2026-05-15 23:16:18.626707

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '2cba83ec392a'
down_revision: Union[str, None] = '7536981d5a01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Shared enum — already exists in the DB; never create or drop it here
_org_ref_type = postgresql.ENUM('Organization', name='organization_reference_type', create_type=False)


def upgrade() -> None:
    # ── healthcare_service: add provided_by_type + VARCHAR → Integer ──────────
    op.add_column('healthcare_service', sa.Column(
        'provided_by_type', _org_ref_type, nullable=True,
    ))
    op.alter_column(
        'healthcare_service', 'provided_by_id',
        existing_type=sa.VARCHAR(),
        type_=sa.Integer(),
        existing_nullable=True,
        postgresql_using='provided_by_id::integer',
    )

    # ── practitioner_role: add organization_type + VARCHAR → Integer ──────────
    op.add_column('practitioner_role', sa.Column(
        'organization_type', _org_ref_type, nullable=True,
    ))
    op.alter_column(
        'practitioner_role', 'organization_id',
        existing_type=sa.VARCHAR(),
        type_=sa.Integer(),
        existing_nullable=True,
        postgresql_using='organization_id::integer',
    )

    # ── practitioner_role_contact: add organization_type + VARCHAR → Integer ──
    op.add_column('practitioner_role_contact', sa.Column(
        'organization_type', _org_ref_type, nullable=True,
    ))
    op.alter_column(
        'practitioner_role_contact', 'organization_id',
        existing_type=sa.VARCHAR(),
        type_=sa.Integer(),
        existing_nullable=True,
        postgresql_using='organization_id::integer',
    )


def downgrade() -> None:
    # ── practitioner_role_contact ─────────────────────────────────────────────
    op.alter_column(
        'practitioner_role_contact', 'organization_id',
        existing_type=sa.Integer(),
        type_=sa.VARCHAR(),
        existing_nullable=True,
    )
    op.drop_column('practitioner_role_contact', 'organization_type')

    # ── practitioner_role ─────────────────────────────────────────────────────
    op.alter_column(
        'practitioner_role', 'organization_id',
        existing_type=sa.Integer(),
        type_=sa.VARCHAR(),
        existing_nullable=True,
    )
    op.drop_column('practitioner_role', 'organization_type')

    # ── healthcare_service ────────────────────────────────────────────────────
    op.alter_column(
        'healthcare_service', 'provided_by_id',
        existing_type=sa.Integer(),
        type_=sa.VARCHAR(),
        existing_nullable=True,
    )
    op.drop_column('healthcare_service', 'provided_by_type')
