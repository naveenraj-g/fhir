"""appointment_service_type_codeable_reference

Revision ID: 267d05eceab3
Revises: 745f04edb93c
Create Date: 2026-05-15 15:00:11.275818

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '267d05eceab3'
down_revision: Union[str, None] = '745f04edb93c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_service_type_ref_type = postgresql.ENUM(
    'HealthcareService',
    name='appointment_service_type_reference_type',
)


def upgrade() -> None:
    _service_type_ref_type.create(op.get_bind(), checkfirst=True)
    op.add_column(
        'appointment_service_type',
        sa.Column(
            'reference_type',
            postgresql.ENUM('HealthcareService', name='appointment_service_type_reference_type', create_type=False),
            nullable=True,
        ),
    )
    op.add_column('appointment_service_type', sa.Column('reference_id', sa.Integer(), nullable=True))
    op.add_column('appointment_service_type', sa.Column('reference_display', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('appointment_service_type', 'reference_display')
    op.drop_column('appointment_service_type', 'reference_id')
    op.drop_column('appointment_service_type', 'reference_type')
    _service_type_ref_type.drop(op.get_bind(), checkfirst=True)
