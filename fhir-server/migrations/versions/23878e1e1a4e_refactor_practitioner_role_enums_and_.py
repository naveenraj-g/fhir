"""refactor_practitioner_role_enums_and_fields

Revision ID: 23878e1e1a4e
Revises: e3b169890e0d
Create Date: 2026-05-15 23:01:20.194265

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '23878e1e1a4e'
down_revision: Union[str, None] = 'e3b169890e0d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_location_ref_type = postgresql.ENUM('Location', name='pr_location_ref_type')
_healthcare_service_ref_type = postgresql.ENUM('HealthcareService', name='pr_healthcare_service_ref_type')
_endpoint_ref_type = postgresql.ENUM('Endpoint', name='pr_endpoint_ref_type')


def upgrade() -> None:
    bind = op.get_bind()

    # ── 1. practitioner_role: add availability_exceptions + index org_id ──────
    op.add_column('practitioner_role', sa.Column('availability_exceptions', sa.String(), nullable=True))
    op.create_index(op.f('ix_practitioner_role_org_id'), 'practitioner_role', ['org_id'], unique=False)

    # ── 2. practitioner_role_location: rename + add reference_type Enum ───────
    op.alter_column('practitioner_role_location', 'location_ref_id', new_column_name='reference_id')
    op.alter_column('practitioner_role_location', 'location_display', new_column_name='reference_display')
    _location_ref_type.create(bind, checkfirst=True)
    op.add_column('practitioner_role_location', sa.Column(
        'reference_type',
        postgresql.ENUM('Location', name='pr_location_ref_type', create_type=False),
        nullable=True,
    ))

    # ── 3. practitioner_role_healthcare_service: rename + add reference_type ──
    op.alter_column('practitioner_role_healthcare_service', 'service_ref_id', new_column_name='reference_id')
    op.alter_column('practitioner_role_healthcare_service', 'service_display', new_column_name='reference_display')
    _healthcare_service_ref_type.create(bind, checkfirst=True)
    op.add_column('practitioner_role_healthcare_service', sa.Column(
        'reference_type',
        postgresql.ENUM('HealthcareService', name='pr_healthcare_service_ref_type', create_type=False),
        nullable=True,
    ))

    # ── 4. practitioner_role_endpoint: rename + add reference_type Enum ───────
    op.alter_column('practitioner_role_endpoint', 'endpoint_ref_id', new_column_name='reference_id')
    op.alter_column('practitioner_role_endpoint', 'endpoint_display', new_column_name='reference_display')
    _endpoint_ref_type.create(bind, checkfirst=True)
    op.add_column('practitioner_role_endpoint', sa.Column(
        'reference_type',
        postgresql.ENUM('Endpoint', name='pr_endpoint_ref_type', create_type=False),
        nullable=True,
    ))


def downgrade() -> None:
    bind = op.get_bind()

    # ── Reverse endpoint ──────────────────────────────────────────────────────
    op.drop_column('practitioner_role_endpoint', 'reference_type')
    _endpoint_ref_type.drop(bind, checkfirst=True)
    op.alter_column('practitioner_role_endpoint', 'reference_display', new_column_name='endpoint_display')
    op.alter_column('practitioner_role_endpoint', 'reference_id', new_column_name='endpoint_ref_id')

    # ── Reverse healthcare_service ────────────────────────────────────────────
    op.drop_column('practitioner_role_healthcare_service', 'reference_type')
    _healthcare_service_ref_type.drop(bind, checkfirst=True)
    op.alter_column('practitioner_role_healthcare_service', 'reference_display', new_column_name='service_display')
    op.alter_column('practitioner_role_healthcare_service', 'reference_id', new_column_name='service_ref_id')

    # ── Reverse location ──────────────────────────────────────────────────────
    op.drop_column('practitioner_role_location', 'reference_type')
    _location_ref_type.drop(bind, checkfirst=True)
    op.alter_column('practitioner_role_location', 'reference_display', new_column_name='location_display')
    op.alter_column('practitioner_role_location', 'reference_id', new_column_name='location_ref_id')

    # ── Reverse main table ────────────────────────────────────────────────────
    op.drop_index(op.f('ix_practitioner_role_org_id'), table_name='practitioner_role')
    op.drop_column('practitioner_role', 'availability_exceptions')
