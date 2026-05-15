"""patient_enum_types_and_type_text

Revision ID: 59f3c0503d96
Revises: 1211bf284768
Create Date: 2026-05-15 13:45:06.651017

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '59f3c0503d96'
down_revision: Union[str, None] = '1211bf284768'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# All enum types referenced here already exist in the DB — create_type=False prevents
# Alembic from issuing a redundant CREATE TYPE.
_address_use = postgresql.ENUM('home', 'work', 'temp', 'old', 'billing', name='address_use', create_type=False)
_address_type = postgresql.ENUM('postal', 'physical', 'both', name='address_type', create_type=False)
_human_name_use = postgresql.ENUM('usual', 'official', 'temp', 'nickname', 'anonymous', 'old', 'maiden', name='human_name_use', create_type=False)
_contact_point_system = postgresql.ENUM('phone', 'fax', 'email', 'pager', 'url', 'sms', 'other', name='contact_point_system', create_type=False)
_contact_point_use = postgresql.ENUM('home', 'work', 'temp', 'old', 'mobile', name='contact_point_use', create_type=False)
_identifier_use = postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False)
# patient_gender was created when the patient table was first created (lowercase values).
_patient_gender = postgresql.ENUM('male', 'female', 'other', 'unknown', name='patient_gender', create_type=False)


def upgrade() -> None:
    # Add missing type_text column to patient_identifier first.
    op.add_column('patient_identifier', sa.Column('type_text', sa.String(), nullable=True))

    # ALTER VARCHAR columns to proper PostgreSQL enum types.
    # Each ALTER requires a USING clause so PostgreSQL knows how to cast existing values.

    op.alter_column('patient_address', 'use',
                    existing_type=sa.VARCHAR(), type_=_address_use,
                    postgresql_using='use::address_use', existing_nullable=True)
    op.alter_column('patient_address', 'type',
                    existing_type=sa.VARCHAR(), type_=_address_type,
                    postgresql_using='type::address_type', existing_nullable=True)

    op.alter_column('patient_contact', 'name_use',
                    existing_type=sa.VARCHAR(), type_=_human_name_use,
                    postgresql_using='name_use::human_name_use', existing_nullable=True)
    op.alter_column('patient_contact', 'address_use',
                    existing_type=sa.VARCHAR(), type_=_address_use,
                    postgresql_using='address_use::address_use', existing_nullable=True)
    op.alter_column('patient_contact', 'address_type',
                    existing_type=sa.VARCHAR(), type_=_address_type,
                    postgresql_using='address_type::address_type', existing_nullable=True)
    op.alter_column('patient_contact', 'gender',
                    existing_type=sa.VARCHAR(), type_=_patient_gender,
                    postgresql_using='gender::patient_gender', existing_nullable=True)

    op.alter_column('patient_contact_telecom', 'system',
                    existing_type=sa.VARCHAR(), type_=_contact_point_system,
                    postgresql_using='system::contact_point_system', existing_nullable=True)
    op.alter_column('patient_contact_telecom', 'use',
                    existing_type=sa.VARCHAR(), type_=_contact_point_use,
                    postgresql_using='use::contact_point_use', existing_nullable=True)

    op.alter_column('patient_identifier', 'use',
                    existing_type=sa.VARCHAR(), type_=_identifier_use,
                    postgresql_using='use::identifier_use', existing_nullable=True)

    op.alter_column('patient_name', 'use',
                    existing_type=sa.VARCHAR(), type_=_human_name_use,
                    postgresql_using='use::human_name_use', existing_nullable=True)

    op.alter_column('patient_telecom', 'system',
                    existing_type=sa.VARCHAR(), type_=_contact_point_system,
                    postgresql_using='system::contact_point_system', existing_nullable=True)
    op.alter_column('patient_telecom', 'use',
                    existing_type=sa.VARCHAR(), type_=_contact_point_use,
                    postgresql_using='use::contact_point_use', existing_nullable=True)


def downgrade() -> None:
    op.alter_column('patient_telecom', 'use',
                    existing_type=_contact_point_use, type_=sa.VARCHAR(),
                    postgresql_using='use::varchar', existing_nullable=True)
    op.alter_column('patient_telecom', 'system',
                    existing_type=_contact_point_system, type_=sa.VARCHAR(),
                    postgresql_using='system::varchar', existing_nullable=True)

    op.alter_column('patient_name', 'use',
                    existing_type=_human_name_use, type_=sa.VARCHAR(),
                    postgresql_using='use::varchar', existing_nullable=True)

    op.alter_column('patient_identifier', 'use',
                    existing_type=_identifier_use, type_=sa.VARCHAR(),
                    postgresql_using='use::varchar', existing_nullable=True)
    op.drop_column('patient_identifier', 'type_text')

    op.alter_column('patient_contact_telecom', 'use',
                    existing_type=_contact_point_use, type_=sa.VARCHAR(),
                    postgresql_using='use::varchar', existing_nullable=True)
    op.alter_column('patient_contact_telecom', 'system',
                    existing_type=_contact_point_system, type_=sa.VARCHAR(),
                    postgresql_using='system::varchar', existing_nullable=True)

    op.alter_column('patient_contact', 'gender',
                    existing_type=_patient_gender, type_=sa.VARCHAR(),
                    postgresql_using='gender::varchar', existing_nullable=True)
    op.alter_column('patient_contact', 'address_type',
                    existing_type=_address_type, type_=sa.VARCHAR(),
                    postgresql_using='address_type::varchar', existing_nullable=True)
    op.alter_column('patient_contact', 'address_use',
                    existing_type=_address_use, type_=sa.VARCHAR(),
                    postgresql_using='address_use::varchar', existing_nullable=True)
    op.alter_column('patient_contact', 'name_use',
                    existing_type=_human_name_use, type_=sa.VARCHAR(),
                    postgresql_using='name_use::varchar', existing_nullable=True)

    op.alter_column('patient_address', 'type',
                    existing_type=_address_type, type_=sa.VARCHAR(),
                    postgresql_using='type::varchar', existing_nullable=True)
    op.alter_column('patient_address', 'use',
                    existing_type=_address_use, type_=sa.VARCHAR(),
                    postgresql_using='use::varchar', existing_nullable=True)
