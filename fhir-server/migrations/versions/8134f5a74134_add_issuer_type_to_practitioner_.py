"""add_issuer_type_to_practitioner_qualification

Revision ID: 8134f5a74134
Revises: 185352496e36
Create Date: 2026-05-15 18:19:28.113884

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8134f5a74134'
down_revision: Union[str, None] = '185352496e36'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_org_ref_type = postgresql.ENUM('Organization', name='organization_reference_type')


def upgrade() -> None:
    _org_ref_type.create(op.get_bind(), checkfirst=True)

    op.add_column('practitioner_qualification', sa.Column(
        'issuer_type',
        postgresql.ENUM('Organization', name='organization_reference_type', create_type=False),
        nullable=True,
    ))


def downgrade() -> None:
    op.drop_column('practitioner_qualification', 'issuer_type')
