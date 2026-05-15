"""encounter_uniform_reference_columns

Revision ID: 98454fe4e107
Revises: 719a592d7843
Create Date: 2026-05-15 17:41:40.224973

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '98454fe4e107'
down_revision: Union[str, None] = '719a592d7843'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# New enum types for the 5 pure-reference child tables
_account_ref_type = postgresql.ENUM('Account', name='encounter_account_reference_type')
_appointment_ref_type = postgresql.ENUM('Appointment', name='encounter_appointment_ref_reference_type')
_care_team_ref_type = postgresql.ENUM('CareTeam', name='encounter_care_team_reference_type')
_episode_of_care_ref_type = postgresql.ENUM('EpisodeOfCare', name='encounter_episode_of_care_reference_type')
_location_ref_type = postgresql.ENUM('Location', name='encounter_location_reference_type')

# encounter_participant_reference_type already exists in DB (created by previous migration)
# No need to create or drop it — we only rename the column from actor_type → reference_type


def upgrade() -> None:
    bind = op.get_bind()
    _account_ref_type.create(bind, checkfirst=True)
    _appointment_ref_type.create(bind, checkfirst=True)
    _care_team_ref_type.create(bind, checkfirst=True)
    _episode_of_care_ref_type.create(bind, checkfirst=True)
    _location_ref_type.create(bind, checkfirst=True)

    # encounter_account: account_id + account_display → reference_type + reference_id + reference_display
    op.add_column('encounter_account', sa.Column(
        'reference_type',
        postgresql.ENUM('Account', name='encounter_account_reference_type', create_type=False),
        nullable=True,
    ))
    op.add_column('encounter_account', sa.Column('reference_id', sa.Integer(), nullable=True))
    op.add_column('encounter_account', sa.Column('reference_display', sa.String(), nullable=True))
    op.drop_column('encounter_account', 'account_id')
    op.drop_column('encounter_account', 'account_display')

    # encounter_appointment_ref: appointment_id + appointment_display → reference_type + reference_id + reference_display
    op.add_column('encounter_appointment_ref', sa.Column(
        'reference_type',
        postgresql.ENUM('Appointment', name='encounter_appointment_ref_reference_type', create_type=False),
        nullable=True,
    ))
    op.add_column('encounter_appointment_ref', sa.Column('reference_id', sa.Integer(), nullable=True))
    op.add_column('encounter_appointment_ref', sa.Column('reference_display', sa.String(), nullable=True))
    op.drop_column('encounter_appointment_ref', 'appointment_id')
    op.drop_column('encounter_appointment_ref', 'appointment_display')

    # encounter_care_team: care_team_id + care_team_display → reference_type + reference_id + reference_display
    op.add_column('encounter_care_team', sa.Column(
        'reference_type',
        postgresql.ENUM('CareTeam', name='encounter_care_team_reference_type', create_type=False),
        nullable=True,
    ))
    op.add_column('encounter_care_team', sa.Column('reference_id', sa.Integer(), nullable=True))
    op.add_column('encounter_care_team', sa.Column('reference_display', sa.String(), nullable=True))
    op.drop_column('encounter_care_team', 'care_team_id')
    op.drop_column('encounter_care_team', 'care_team_display')

    # encounter_episode_of_care: episode_of_care_id + display → reference_type + reference_id + reference_display
    op.add_column('encounter_episode_of_care', sa.Column(
        'reference_type',
        postgresql.ENUM('EpisodeOfCare', name='encounter_episode_of_care_reference_type', create_type=False),
        nullable=True,
    ))
    op.add_column('encounter_episode_of_care', sa.Column('reference_id', sa.Integer(), nullable=True))
    op.add_column('encounter_episode_of_care', sa.Column('reference_display', sa.String(), nullable=True))
    op.drop_column('encounter_episode_of_care', 'display')
    op.drop_column('encounter_episode_of_care', 'episode_of_care_id')

    # encounter_location: location_id + location_display → reference_type + reference_id + reference_display
    op.add_column('encounter_location', sa.Column(
        'reference_type',
        postgresql.ENUM('Location', name='encounter_location_reference_type', create_type=False),
        nullable=True,
    ))
    op.add_column('encounter_location', sa.Column('reference_id', sa.Integer(), nullable=True))
    op.add_column('encounter_location', sa.Column('reference_display', sa.String(), nullable=True))
    op.drop_column('encounter_location', 'location_id')
    op.drop_column('encounter_location', 'location_display')

    # encounter_participant: rename actor_type/actor_id/actor_display → reference_type/reference_id/reference_display
    # Uses existing encounter_participant_reference_type enum — no create needed
    op.add_column('encounter_participant', sa.Column(
        'reference_type',
        postgresql.ENUM(
            'Patient', 'Group', 'RelatedPerson', 'Practitioner',
            'PractitionerRole', 'Device', 'HealthcareService',
            name='encounter_participant_reference_type',
            create_type=False,
        ),
        nullable=True,
    ))
    op.add_column('encounter_participant', sa.Column('reference_id', sa.Integer(), nullable=True))
    op.add_column('encounter_participant', sa.Column('reference_display', sa.String(), nullable=True))
    op.drop_column('encounter_participant', 'actor_display')
    op.drop_column('encounter_participant', 'actor_id')
    op.drop_column('encounter_participant', 'actor_type')


def downgrade() -> None:
    # encounter_participant: restore actor_type/actor_id/actor_display
    op.add_column('encounter_participant', sa.Column(
        'actor_type',
        postgresql.ENUM(
            'Patient', 'Group', 'RelatedPerson', 'Practitioner',
            'PractitionerRole', 'Device', 'HealthcareService',
            name='encounter_participant_reference_type',
            create_type=False,
        ),
        autoincrement=False, nullable=True,
    ))
    op.add_column('encounter_participant', sa.Column('actor_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('encounter_participant', sa.Column('actor_display', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_column('encounter_participant', 'reference_display')
    op.drop_column('encounter_participant', 'reference_id')
    op.drop_column('encounter_participant', 'reference_type')

    # encounter_location: restore location_id + location_display
    op.add_column('encounter_location', sa.Column('location_display', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('encounter_location', sa.Column('location_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_column('encounter_location', 'reference_display')
    op.drop_column('encounter_location', 'reference_id')
    op.drop_column('encounter_location', 'reference_type')

    # encounter_episode_of_care: restore episode_of_care_id + display
    op.add_column('encounter_episode_of_care', sa.Column('episode_of_care_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('encounter_episode_of_care', sa.Column('display', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_column('encounter_episode_of_care', 'reference_display')
    op.drop_column('encounter_episode_of_care', 'reference_id')
    op.drop_column('encounter_episode_of_care', 'reference_type')

    # encounter_care_team: restore care_team_id + care_team_display
    op.add_column('encounter_care_team', sa.Column('care_team_display', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('encounter_care_team', sa.Column('care_team_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_column('encounter_care_team', 'reference_display')
    op.drop_column('encounter_care_team', 'reference_id')
    op.drop_column('encounter_care_team', 'reference_type')

    # encounter_appointment_ref: restore appointment_id + appointment_display
    op.add_column('encounter_appointment_ref', sa.Column('appointment_display', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('encounter_appointment_ref', sa.Column('appointment_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_column('encounter_appointment_ref', 'reference_display')
    op.drop_column('encounter_appointment_ref', 'reference_id')
    op.drop_column('encounter_appointment_ref', 'reference_type')

    # encounter_account: restore account_id + account_display
    op.add_column('encounter_account', sa.Column('account_display', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('encounter_account', sa.Column('account_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_column('encounter_account', 'reference_display')
    op.drop_column('encounter_account', 'reference_id')
    op.drop_column('encounter_account', 'reference_type')

    bind = op.get_bind()
    _location_ref_type.drop(bind, checkfirst=True)
    _episode_of_care_ref_type.drop(bind, checkfirst=True)
    _care_team_ref_type.drop(bind, checkfirst=True)
    _appointment_ref_type.drop(bind, checkfirst=True)
    _account_ref_type.drop(bind, checkfirst=True)
