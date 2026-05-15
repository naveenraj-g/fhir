"""appointment_based_on_reference_type_enum

Revision ID: 9084ef1a2f6d
Revises: 267d05eceab3
Create Date: 2026-05-15 15:08:38.214983

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9084ef1a2f6d'
down_revision: Union[str, None] = '267d05eceab3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_based_on_ref_type = postgresql.ENUM(
    'CarePlan', 'DeviceRequest', 'MedicationRequest', 'ServiceRequest',
    'RequestOrchestration', 'NutritionOrder', 'VisionPrescription',
    name='appointment_based_on_reference_type',
)


def upgrade() -> None:
    _based_on_ref_type.create(op.get_bind(), checkfirst=True)
    op.add_column(
        'appointment_based_on',
        sa.Column(
            'reference_type',
            postgresql.ENUM(
                'CarePlan', 'DeviceRequest', 'MedicationRequest', 'ServiceRequest',
                'RequestOrchestration', 'NutritionOrder', 'VisionPrescription',
                name='appointment_based_on_reference_type', create_type=False,
            ),
            nullable=True,
        ),
    )
    op.add_column('appointment_based_on', sa.Column('reference_id', sa.Integer(), nullable=True))
    op.add_column('appointment_based_on', sa.Column('reference_display', sa.String(), nullable=True))
    op.drop_column('appointment_based_on', 'service_request_id')
    op.drop_column('appointment_based_on', 'service_request_display')


def downgrade() -> None:
    op.add_column('appointment_based_on', sa.Column('service_request_display', sa.VARCHAR(), nullable=True))
    op.add_column('appointment_based_on', sa.Column('service_request_id', sa.INTEGER(), nullable=True))
    op.drop_column('appointment_based_on', 'reference_display')
    op.drop_column('appointment_based_on', 'reference_id')
    op.drop_column('appointment_based_on', 'reference_type')
    _based_on_ref_type.drop(op.get_bind(), checkfirst=True)
