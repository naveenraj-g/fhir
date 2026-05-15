"""practitioner_enum_types_and_qualification_identifiers

Revision ID: 13e0246ea539
Revises: 59f3c0503d96
Create Date: 2026-05-15 13:57:15.326355

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '13e0246ea539'
down_revision: Union[str, None] = '59f3c0503d96'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Existing PostgreSQL enum types — create_type=False prevents redundant CREATE TYPE.
_address_use = postgresql.ENUM('home', 'work', 'temp', 'old', 'billing', name='address_use', create_type=False)
_address_type = postgresql.ENUM('postal', 'physical', 'both', name='address_type', create_type=False)
_human_name_use = postgresql.ENUM('usual', 'official', 'temp', 'nickname', 'anonymous', 'old', 'maiden', name='human_name_use', create_type=False)
_contact_point_system = postgresql.ENUM('phone', 'fax', 'email', 'pager', 'url', 'sms', 'other', name='contact_point_system', create_type=False)
_contact_point_use = postgresql.ENUM('home', 'work', 'temp', 'old', 'mobile', name='contact_point_use', create_type=False)
_identifier_use = postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False)
# administrative_gender is new — created explicitly in upgrade().
_administrative_gender = postgresql.ENUM('male', 'female', 'other', 'unknown', name='administrative_gender', create_type=False)


def upgrade() -> None:
    # Create the new administrative_gender enum type.
    op.execute("CREATE TYPE administrative_gender AS ENUM ('male', 'female', 'other', 'unknown')")

    # Create grandchild table for qualification identifiers (0..*).
    op.create_table(
        'practitioner_qualification_identifier',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('qualification_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('use', _identifier_use, nullable=True),
        sa.Column('type_system', sa.String(), nullable=True),
        sa.Column('type_code', sa.String(), nullable=True),
        sa.Column('type_display', sa.String(), nullable=True),
        sa.Column('type_text', sa.String(), nullable=True),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('value', sa.String(), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('assigner', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['qualification_id'], ['practitioner_qualification.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_practitioner_qualification_identifier_qualification_id'),
        'practitioner_qualification_identifier',
        ['qualification_id'],
        unique=False,
    )

    # Drop flat qualification identifier columns — replaced by the grandchild table.
    op.drop_column('practitioner_qualification', 'identifier_value')
    op.drop_column('practitioner_qualification', 'identifier_system')

    # ALTER VARCHAR columns to proper PostgreSQL enum types.
    # Each ALTER requires a USING clause so PostgreSQL knows how to cast existing values.

    op.alter_column('practitioner', 'gender',
                    existing_type=sa.VARCHAR(), type_=_administrative_gender,
                    postgresql_using='gender::administrative_gender', existing_nullable=True)

    op.alter_column('practitioner_name', 'use',
                    existing_type=sa.VARCHAR(), type_=_human_name_use,
                    postgresql_using='use::human_name_use', existing_nullable=True)

    op.alter_column('practitioner_identifier', 'use',
                    existing_type=sa.VARCHAR(), type_=_identifier_use,
                    postgresql_using='use::identifier_use', existing_nullable=True)

    op.alter_column('practitioner_telecom', 'system',
                    existing_type=sa.VARCHAR(), type_=_contact_point_system,
                    postgresql_using='system::contact_point_system', existing_nullable=True)
    op.alter_column('practitioner_telecom', 'use',
                    existing_type=sa.VARCHAR(), type_=_contact_point_use,
                    postgresql_using='use::contact_point_use', existing_nullable=True)

    op.alter_column('practitioner_address', 'use',
                    existing_type=sa.VARCHAR(), type_=_address_use,
                    postgresql_using='use::address_use', existing_nullable=True)
    op.alter_column('practitioner_address', 'type',
                    existing_type=sa.VARCHAR(), type_=_address_type,
                    postgresql_using='type::address_type', existing_nullable=True)


def downgrade() -> None:
    op.alter_column('practitioner_address', 'type',
                    existing_type=_address_type, type_=sa.VARCHAR(),
                    postgresql_using='type::varchar', existing_nullable=True)
    op.alter_column('practitioner_address', 'use',
                    existing_type=_address_use, type_=sa.VARCHAR(),
                    postgresql_using='use::varchar', existing_nullable=True)

    op.alter_column('practitioner_telecom', 'use',
                    existing_type=_contact_point_use, type_=sa.VARCHAR(),
                    postgresql_using='use::varchar', existing_nullable=True)
    op.alter_column('practitioner_telecom', 'system',
                    existing_type=_contact_point_system, type_=sa.VARCHAR(),
                    postgresql_using='system::varchar', existing_nullable=True)

    op.alter_column('practitioner_identifier', 'use',
                    existing_type=_identifier_use, type_=sa.VARCHAR(),
                    postgresql_using='use::varchar', existing_nullable=True)

    op.alter_column('practitioner_name', 'use',
                    existing_type=_human_name_use, type_=sa.VARCHAR(),
                    postgresql_using='use::varchar', existing_nullable=True)

    op.alter_column('practitioner', 'gender',
                    existing_type=_administrative_gender, type_=sa.VARCHAR(),
                    postgresql_using='gender::varchar', existing_nullable=True)
    op.execute("DROP TYPE IF EXISTS administrative_gender")

    op.drop_index(op.f('ix_practitioner_qualification_identifier_qualification_id'),
                  table_name='practitioner_qualification_identifier')
    op.drop_table('practitioner_qualification_identifier')

    op.add_column('practitioner_qualification', sa.Column('identifier_system', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('practitioner_qualification', sa.Column('identifier_value', sa.VARCHAR(), autoincrement=False, nullable=True))
