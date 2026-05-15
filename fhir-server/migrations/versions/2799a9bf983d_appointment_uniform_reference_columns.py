"""appointment_uniform_reference_columns

Revision ID: 2799a9bf983d
Revises: 98454fe4e107
Create Date: 2026-05-15 18:00:12.939004

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2799a9bf983d'
down_revision: Union[str, None] = '98454fe4e107'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# New enum types for the 3 pure-reference child tables
_account_ref_type = postgresql.ENUM('Account', name='appointment_account_reference_type')
_replaces_ref_type = postgresql.ENUM('Appointment', name='appointment_replaces_reference_type')
_slot_ref_type = postgresql.ENUM('Slot', name='appointment_slot_reference_type')

# appointment_participant_actor_type already exists in DB — no create/drop needed;
# we only rename the columns actor_type/actor_id/actor_display → reference_type/reference_id/reference_display


def upgrade() -> None:
    bind = op.get_bind()
    _account_ref_type.create(bind, checkfirst=True)
    _replaces_ref_type.create(bind, checkfirst=True)
    _slot_ref_type.create(bind, checkfirst=True)

    # appointment_account: account_id + account_display → reference_type + reference_id + reference_display
    op.add_column('appointment_account', sa.Column(
        'reference_type',
        postgresql.ENUM('Account', name='appointment_account_reference_type', create_type=False),
        nullable=True,
    ))
    op.add_column('appointment_account', sa.Column('reference_id', sa.Integer(), nullable=True))
    op.add_column('appointment_account', sa.Column('reference_display', sa.String(), nullable=True))
    op.drop_column('appointment_account', 'account_display')
    op.drop_column('appointment_account', 'account_id')

    # appointment_replaces: replaced_appointment_id + replaced_appointment_display → reference_type + reference_id + reference_display
    op.add_column('appointment_replaces', sa.Column(
        'reference_type',
        postgresql.ENUM('Appointment', name='appointment_replaces_reference_type', create_type=False),
        nullable=True,
    ))
    op.add_column('appointment_replaces', sa.Column('reference_id', sa.Integer(), nullable=True))
    op.add_column('appointment_replaces', sa.Column('reference_display', sa.String(), nullable=True))
    op.drop_column('appointment_replaces', 'replaced_appointment_id')
    op.drop_column('appointment_replaces', 'replaced_appointment_display')

    # appointment_slot: slot_id + slot_display → reference_type + reference_id + reference_display
    op.add_column('appointment_slot', sa.Column(
        'reference_type',
        postgresql.ENUM('Slot', name='appointment_slot_reference_type', create_type=False),
        nullable=True,
    ))
    op.add_column('appointment_slot', sa.Column('reference_id', sa.Integer(), nullable=True))
    op.add_column('appointment_slot', sa.Column('reference_display', sa.String(), nullable=True))
    op.drop_column('appointment_slot', 'slot_display')
    op.drop_column('appointment_slot', 'slot_id')

    # appointment_participant: rename actor_type/actor_id/actor_display → reference_type/reference_id/reference_display
    # Uses existing appointment_participant_actor_type enum — no create needed
    op.add_column('appointment_participant', sa.Column(
        'reference_type',
        postgresql.ENUM(
            'Patient', 'Practitioner', 'PractitionerRole', 'RelatedPerson',
            'Device', 'HealthcareService', 'Location', 'Group', 'CareTeam',
            name='appointment_participant_actor_type',
            create_type=False,
        ),
        nullable=True,
    ))
    op.add_column('appointment_participant', sa.Column('reference_id', sa.Integer(), nullable=True))
    op.add_column('appointment_participant', sa.Column('reference_display', sa.String(), nullable=True))
    op.drop_column('appointment_participant', 'actor_display')
    op.drop_column('appointment_participant', 'actor_type')
    op.drop_column('appointment_participant', 'actor_id')


def downgrade() -> None:
    # appointment_participant: restore actor_type/actor_id/actor_display
    op.add_column('appointment_participant', sa.Column(
        'actor_type',
        postgresql.ENUM(
            'Patient', 'Practitioner', 'PractitionerRole', 'RelatedPerson',
            'Device', 'HealthcareService', 'Location', 'Group', 'CareTeam',
            name='appointment_participant_actor_type',
            create_type=False,
        ),
        autoincrement=False, nullable=True,
    ))
    op.add_column('appointment_participant', sa.Column('actor_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('appointment_participant', sa.Column('actor_display', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_column('appointment_participant', 'reference_display')
    op.drop_column('appointment_participant', 'reference_id')
    op.drop_column('appointment_participant', 'reference_type')

    # appointment_slot: restore slot_id + slot_display
    op.add_column('appointment_slot', sa.Column('slot_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('appointment_slot', sa.Column('slot_display', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_column('appointment_slot', 'reference_display')
    op.drop_column('appointment_slot', 'reference_id')
    op.drop_column('appointment_slot', 'reference_type')

    # appointment_replaces: restore replaced_appointment_id + replaced_appointment_display
    op.add_column('appointment_replaces', sa.Column('replaced_appointment_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('appointment_replaces', sa.Column('replaced_appointment_display', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_column('appointment_replaces', 'reference_display')
    op.drop_column('appointment_replaces', 'reference_id')
    op.drop_column('appointment_replaces', 'reference_type')

    # appointment_account: restore account_id + account_display
    op.add_column('appointment_account', sa.Column('account_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('appointment_account', sa.Column('account_display', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_column('appointment_account', 'reference_display')
    op.drop_column('appointment_account', 'reference_id')
    op.drop_column('appointment_account', 'reference_type')

    bind = op.get_bind()
    _slot_ref_type.drop(bind, checkfirst=True)
    _replaces_ref_type.drop(bind, checkfirst=True)
    _account_ref_type.drop(bind, checkfirst=True)
