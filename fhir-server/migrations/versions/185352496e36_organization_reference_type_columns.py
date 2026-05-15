"""organization_reference_type_columns

Revision ID: 185352496e36
Revises: 2799a9bf983d
Create Date: 2026-05-15 18:13:09.251124

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '185352496e36'
down_revision: Union[str, None] = '2799a9bf983d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_org_ref_type = postgresql.ENUM('Organization', name='organization_reference_type')


def upgrade() -> None:
    bind = op.get_bind()
    _org_ref_type.create(bind, checkfirst=True)

    op.add_column('encounter', sa.Column(
        'service_provider_type',
        postgresql.ENUM('Organization', name='organization_reference_type', create_type=False),
        nullable=True,
    ))
    op.add_column('patient', sa.Column(
        'managing_organization_type',
        postgresql.ENUM('Organization', name='organization_reference_type', create_type=False),
        nullable=True,
    ))
    op.add_column('patient_contact', sa.Column(
        'organization_type',
        postgresql.ENUM('Organization', name='organization_reference_type', create_type=False),
        nullable=True,
    ))


def downgrade() -> None:
    op.drop_column('patient_contact', 'organization_type')
    op.drop_column('patient', 'managing_organization_type')
    op.drop_column('encounter', 'service_provider_type')

    bind = op.get_bind()
    _org_ref_type.drop(bind, checkfirst=True)
