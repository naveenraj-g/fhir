"""refactor_appointment_fhir_r4

Revision ID: dc849f11b34e
Revises: fe58b342c8f0
Create Date: 2026-05-14 22:25:22.308472

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'dc849f11b34e'
down_revision: Union[str, None] = 'fe58b342c8f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── New child/grandchild tables ──────────────────────────────────────────
    op.create_table('appointment_based_on',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('appointment_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('service_request_id', sa.Integer(), nullable=True),
        sa.Column('service_request_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointment.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_appointment_based_on_appointment_id'), 'appointment_based_on', ['appointment_id'], unique=False)

    op.create_table('appointment_identifier',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('appointment_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('use', sa.String(), nullable=True),
        sa.Column('type_system', sa.String(), nullable=True),
        sa.Column('type_code', sa.String(), nullable=True),
        sa.Column('type_display', sa.String(), nullable=True),
        sa.Column('type_text', sa.String(), nullable=True),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('value', sa.String(), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('assigner', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointment.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_appointment_identifier_appointment_id'), 'appointment_identifier', ['appointment_id'], unique=False)

    op.create_table('appointment_reason_reference',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('appointment_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('reference_type', sa.String(), nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointment.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_appointment_reason_reference_appointment_id'), 'appointment_reason_reference', ['appointment_id'], unique=False)

    op.create_table('appointment_requested_period',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('appointment_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointment.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_appointment_requested_period_appointment_id'), 'appointment_requested_period', ['appointment_id'], unique=False)

    op.create_table('appointment_service_category',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('appointment_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointment.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_appointment_service_category_appointment_id'), 'appointment_service_category', ['appointment_id'], unique=False)

    op.create_table('appointment_service_type',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('appointment_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointment.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_appointment_service_type_appointment_id'), 'appointment_service_type', ['appointment_id'], unique=False)

    op.create_table('appointment_slot',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('appointment_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('slot_id', sa.Integer(), nullable=True),
        sa.Column('slot_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointment.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_appointment_slot_appointment_id'), 'appointment_slot', ['appointment_id'], unique=False)

    op.create_table('appointment_specialty',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('appointment_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointment.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_appointment_specialty_appointment_id'), 'appointment_specialty', ['appointment_id'], unique=False)

    op.create_table('appointment_supporting_information',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('appointment_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('reference_type', sa.String(), nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointment.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_appointment_supporting_information_appointment_id'), 'appointment_supporting_information', ['appointment_id'], unique=False)

    op.create_table('appointment_participant_type',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('participant_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=True),
        sa.Column('coding_system', sa.String(), nullable=True),
        sa.Column('coding_code', sa.String(), nullable=True),
        sa.Column('coding_display', sa.String(), nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['participant_id'], ['appointment_participant.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_appointment_participant_type_participant_id'), 'appointment_participant_type', ['participant_id'], unique=False)

    # ── appointment: add new columns ─────────────────────────────────────────
    op.add_column('appointment', sa.Column('cancelation_reason_system', sa.String(), nullable=True))
    op.add_column('appointment', sa.Column('cancelation_reason_code', sa.String(), nullable=True))
    op.add_column('appointment', sa.Column('cancelation_reason_display', sa.String(), nullable=True))
    op.add_column('appointment', sa.Column('cancelation_reason_text', sa.String(), nullable=True))
    op.add_column('appointment', sa.Column('appointment_type_system', sa.String(), nullable=True))
    op.add_column('appointment', sa.Column('appointment_type_text', sa.String(), nullable=True))

    # ── appointment.status: UPPERCASE enum → lowercase enum (raw SQL required) ──
    # Old type: appointmentstatus  ('PROPOSED', 'PENDING', ..., 'ENTERED_IN_ERROR', 'CHECKED_IN', ...)
    # New type: appointment_status ('proposed', 'pending', ..., 'entered-in-error', 'checked-in', ...)
    op.execute("""
        CREATE TYPE appointment_status AS ENUM (
            'proposed', 'pending', 'booked', 'arrived', 'fulfilled',
            'cancelled', 'noshow', 'entered-in-error', 'checked-in', 'waitlist'
        )
    """)
    op.execute("""
        ALTER TABLE appointment
        ALTER COLUMN status TYPE appointment_status
        USING (
            CASE status::text
                WHEN 'PROPOSED'        THEN 'proposed'
                WHEN 'PENDING'         THEN 'pending'
                WHEN 'BOOKED'          THEN 'booked'
                WHEN 'ARRIVED'         THEN 'arrived'
                WHEN 'FULFILLED'       THEN 'fulfilled'
                WHEN 'CANCELLED'       THEN 'cancelled'
                WHEN 'NOSHOW'          THEN 'noshow'
                WHEN 'ENTERED_IN_ERROR' THEN 'entered-in-error'
                WHEN 'CHECKED_IN'      THEN 'checked-in'
                WHEN 'WAITLIST'        THEN 'waitlist'
                ELSE lower(status::text)
            END
        )::appointment_status
    """)
    op.execute("DROP TYPE IF EXISTS appointmentstatus")

    # ── appointment: drop removed columns ────────────────────────────────────
    op.drop_column('appointment', 'service_category_code')
    op.drop_column('appointment', 'service_category_display')
    op.drop_column('appointment', 'service_type_code')
    op.drop_column('appointment', 'service_type_display')
    op.drop_column('appointment', 'specialty_code')
    op.drop_column('appointment', 'specialty_display')
    op.drop_column('appointment', 'cancellation_reason')
    op.drop_column('appointment', 'cancellation_date')
    op.drop_column('appointment', 'recurrence_id')
    op.drop_column('appointment', 'occurrence_changed')

    # ── appointment_participant: add new columns (actor_type enum, actor_id) ─
    # Create the new enum type with the correct mixed-case VALUES first.
    op.execute("""
        CREATE TYPE appointment_participant_actor_type AS ENUM (
            'Patient', 'Practitioner', 'PractitionerRole',
            'RelatedPerson', 'Device', 'HealthcareService', 'Location'
        )
    """)
    op.add_column('appointment_participant', sa.Column(
        'actor_type',
        sa.Enum(
            'Patient', 'Practitioner', 'PractitionerRole',
            'RelatedPerson', 'Device', 'HealthcareService', 'Location',
            name='appointment_participant_actor_type',
            create_type=False,
        ),
        nullable=True,
    ))
    op.add_column('appointment_participant', sa.Column('actor_id', sa.Integer(), nullable=True))

    # ── appointment_participant: drop old columns ─────────────────────────────
    op.drop_column('appointment_participant', 'actor_reference_type')
    op.drop_column('appointment_participant', 'actor_reference_id')
    op.drop_column('appointment_participant', 'type_code')
    op.drop_column('appointment_participant', 'type_display')
    op.drop_column('appointment_participant', 'type_text')
    op.execute("DROP TYPE IF EXISTS appointmentparticipantactortype")


def downgrade() -> None:
    # ── appointment_participant: restore old columns ──────────────────────────
    op.execute("""
        CREATE TYPE appointmentparticipantactortype AS ENUM (
            'PATIENT', 'GROUP', 'PRACTITIONER', 'PRACTITIONER_ROLE',
            'CARE_TEAM', 'RELATED_PERSON', 'DEVICE', 'HEALTHCARE_SERVICE', 'LOCATION'
        )
    """)
    op.add_column('appointment_participant', sa.Column('type_text', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('appointment_participant', sa.Column(
        'actor_reference_type',
        postgresql.ENUM(
            'PATIENT', 'GROUP', 'PRACTITIONER', 'PRACTITIONER_ROLE',
            'CARE_TEAM', 'RELATED_PERSON', 'DEVICE', 'HEALTHCARE_SERVICE', 'LOCATION',
            name='appointmentparticipantactortype',
            create_type=False,
        ),
        autoincrement=False, nullable=True,
    ))
    op.add_column('appointment_participant', sa.Column('type_display', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('appointment_participant', sa.Column('type_code', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('appointment_participant', sa.Column('actor_reference_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_column('appointment_participant', 'actor_id')
    op.drop_column('appointment_participant', 'actor_type')
    op.execute("DROP TYPE IF EXISTS appointment_participant_actor_type")

    # ── appointment: restore old columns ─────────────────────────────────────
    op.add_column('appointment', sa.Column('cancellation_date', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
    op.add_column('appointment', sa.Column('service_type_code', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('appointment', sa.Column('service_category_display', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('appointment', sa.Column('specialty_display', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('appointment', sa.Column('service_type_display', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('appointment', sa.Column('occurrence_changed', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.add_column('appointment', sa.Column('recurrence_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('appointment', sa.Column('service_category_code', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('appointment', sa.Column('cancellation_reason', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('appointment', sa.Column('specialty_code', sa.VARCHAR(), autoincrement=False, nullable=True))

    # ── appointment.status: restore UPPERCASE enum ────────────────────────────
    op.execute("""
        CREATE TYPE appointmentstatus AS ENUM (
            'PROPOSED', 'PENDING', 'BOOKED', 'ARRIVED', 'FULFILLED',
            'CANCELLED', 'NOSHOW', 'ENTERED_IN_ERROR', 'CHECKED_IN', 'WAITLIST'
        )
    """)
    op.execute("""
        ALTER TABLE appointment
        ALTER COLUMN status TYPE appointmentstatus
        USING (
            CASE status::text
                WHEN 'proposed'       THEN 'PROPOSED'
                WHEN 'pending'        THEN 'PENDING'
                WHEN 'booked'         THEN 'BOOKED'
                WHEN 'arrived'        THEN 'ARRIVED'
                WHEN 'fulfilled'      THEN 'FULFILLED'
                WHEN 'cancelled'      THEN 'CANCELLED'
                WHEN 'noshow'         THEN 'NOSHOW'
                WHEN 'entered-in-error' THEN 'ENTERED_IN_ERROR'
                WHEN 'checked-in'     THEN 'CHECKED_IN'
                WHEN 'waitlist'       THEN 'WAITLIST'
                ELSE upper(status::text)
            END
        )::appointmentstatus
    """)
    op.execute("DROP TYPE IF EXISTS appointment_status")

    # ── appointment: drop new columns ─────────────────────────────────────────
    op.drop_column('appointment', 'appointment_type_text')
    op.drop_column('appointment', 'appointment_type_system')
    op.drop_column('appointment', 'cancelation_reason_text')
    op.drop_column('appointment', 'cancelation_reason_display')
    op.drop_column('appointment', 'cancelation_reason_code')
    op.drop_column('appointment', 'cancelation_reason_system')

    # ── drop new tables ───────────────────────────────────────────────────────
    op.drop_index(op.f('ix_appointment_participant_type_participant_id'), table_name='appointment_participant_type')
    op.drop_table('appointment_participant_type')
    op.drop_index(op.f('ix_appointment_supporting_information_appointment_id'), table_name='appointment_supporting_information')
    op.drop_table('appointment_supporting_information')
    op.drop_index(op.f('ix_appointment_specialty_appointment_id'), table_name='appointment_specialty')
    op.drop_table('appointment_specialty')
    op.drop_index(op.f('ix_appointment_slot_appointment_id'), table_name='appointment_slot')
    op.drop_table('appointment_slot')
    op.drop_index(op.f('ix_appointment_service_type_appointment_id'), table_name='appointment_service_type')
    op.drop_table('appointment_service_type')
    op.drop_index(op.f('ix_appointment_service_category_appointment_id'), table_name='appointment_service_category')
    op.drop_table('appointment_service_category')
    op.drop_index(op.f('ix_appointment_requested_period_appointment_id'), table_name='appointment_requested_period')
    op.drop_table('appointment_requested_period')
    op.drop_index(op.f('ix_appointment_reason_reference_appointment_id'), table_name='appointment_reason_reference')
    op.drop_table('appointment_reason_reference')
    op.drop_index(op.f('ix_appointment_identifier_appointment_id'), table_name='appointment_identifier')
    op.drop_table('appointment_identifier')
    op.drop_index(op.f('ix_appointment_based_on_appointment_id'), table_name='appointment_based_on')
    op.drop_table('appointment_based_on')
