"""refactor_procedure_enums_and_identifier_fields

Revision ID: 2522e6ba4657
Revises: 421ad17e9861
Create Date: 2026-05-15 21:23:10.986161

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '2522e6ba4657'
down_revision: Union[str, None] = '421ad17e9861'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Declare all new enum types (TitleCase FHIR values)
_location_ref = postgresql.ENUM('Location', name='procedure_location_ref_type')
_based_on_ref = postgresql.ENUM('CarePlan', 'ServiceRequest', name='procedure_based_on_ref_type')
_part_of_ref = postgresql.ENUM(
    'Procedure', 'Observation', 'MedicationAdministration',
    name='procedure_part_of_ref_type',
)
_on_behalf_of = postgresql.ENUM('Organization', name='procedure_on_behalf_of_type')
_reason_ref = postgresql.ENUM(
    'Condition', 'Observation', 'Procedure', 'DiagnosticReport', 'DocumentReference',
    name='procedure_reason_ref_type',
)
_report_ref = postgresql.ENUM(
    'DiagnosticReport', 'DocumentReference', 'Composition',
    name='procedure_report_ref_type',
)
_complication_detail_ref = postgresql.ENUM('Condition', name='procedure_complication_detail_ref_type')
_note_author_ref = postgresql.ENUM(
    'Practitioner', 'Patient', 'RelatedPerson', 'Organization',
    name='procedure_note_author_ref_type',
)
_focal_device_ref = postgresql.ENUM('Device', name='procedure_focal_device_ref_type')
_used_ref = postgresql.ENUM('Device', 'Medication', 'Substance', name='procedure_used_ref_type')


def upgrade() -> None:
    bind = op.get_bind()

    # ── 1. Main table: add location_type column ────────────────────────────────
    _location_ref.create(bind, checkfirst=True)
    op.add_column('procedure', sa.Column(
        'location_type',
        postgresql.ENUM('Location', name='procedure_location_ref_type', create_type=False),
        nullable=True,
    ))

    # ── 2. procedure_identifier: add type_text ─────────────────────────────────
    op.add_column('procedure_identifier', sa.Column('type_text', sa.String(), nullable=True))

    # ── 3. procedure_based_on: String → Enum ──────────────────────────────────
    _based_on_ref.create(bind, checkfirst=True)
    op.alter_column(
        'procedure_based_on', 'reference_type',
        existing_type=sa.VARCHAR(),
        type_=postgresql.ENUM('CarePlan', 'ServiceRequest',
                              name='procedure_based_on_ref_type', create_type=False),
        existing_nullable=True,
        postgresql_using='reference_type::procedure_based_on_ref_type',
    )

    # ── 4. procedure_part_of: String → Enum ───────────────────────────────────
    _part_of_ref.create(bind, checkfirst=True)
    op.alter_column(
        'procedure_part_of', 'reference_type',
        existing_type=sa.VARCHAR(),
        type_=postgresql.ENUM('Procedure', 'Observation', 'MedicationAdministration',
                              name='procedure_part_of_ref_type', create_type=False),
        existing_nullable=True,
        postgresql_using='reference_type::procedure_part_of_ref_type',
    )

    # ── 5. procedure_performer: add on_behalf_of_type ─────────────────────────
    _on_behalf_of.create(bind, checkfirst=True)
    op.add_column('procedure_performer', sa.Column(
        'on_behalf_of_type',
        postgresql.ENUM('Organization', name='procedure_on_behalf_of_type', create_type=False),
        nullable=True,
    ))

    # ── 6. procedure_reason_reference: String → Enum ──────────────────────────
    _reason_ref.create(bind, checkfirst=True)
    op.alter_column(
        'procedure_reason_reference', 'reference_type',
        existing_type=sa.VARCHAR(),
        type_=postgresql.ENUM(
            'Condition', 'Observation', 'Procedure', 'DiagnosticReport', 'DocumentReference',
            name='procedure_reason_ref_type', create_type=False,
        ),
        existing_nullable=True,
        postgresql_using='reference_type::procedure_reason_ref_type',
    )

    # ── 7. procedure_report: String → Enum ────────────────────────────────────
    _report_ref.create(bind, checkfirst=True)
    op.alter_column(
        'procedure_report', 'reference_type',
        existing_type=sa.VARCHAR(),
        type_=postgresql.ENUM('DiagnosticReport', 'DocumentReference', 'Composition',
                              name='procedure_report_ref_type', create_type=False),
        existing_nullable=True,
        postgresql_using='reference_type::procedure_report_ref_type',
    )

    # ── 8. procedure_complication_detail: String(default="Condition") → Enum ──
    _complication_detail_ref.create(bind, checkfirst=True)
    op.alter_column(
        'procedure_complication_detail', 'reference_type',
        existing_type=sa.VARCHAR(),
        type_=postgresql.ENUM('Condition', name='procedure_complication_detail_ref_type', create_type=False),
        existing_nullable=True,
        postgresql_using='reference_type::procedure_complication_detail_ref_type',
    )

    # ── 9. procedure_note: String → Enum + rename author_display ──────────────
    _note_author_ref.create(bind, checkfirst=True)
    op.alter_column(
        'procedure_note', 'author_reference_type',
        existing_type=sa.VARCHAR(),
        type_=postgresql.ENUM(
            'Practitioner', 'Patient', 'RelatedPerson', 'Organization',
            name='procedure_note_author_ref_type', create_type=False,
        ),
        existing_nullable=True,
        postgresql_using='author_reference_type::procedure_note_author_ref_type',
    )
    op.alter_column('procedure_note', 'author_display',
                    new_column_name='author_reference_display')

    # ── 10. procedure_focal_device: String(default="Device") → Enum
    #        + rename manipulated_display → manipulated_reference_display ───────
    _focal_device_ref.create(bind, checkfirst=True)
    op.alter_column(
        'procedure_focal_device', 'manipulated_reference_type',
        existing_type=sa.VARCHAR(),
        type_=postgresql.ENUM('Device', name='procedure_focal_device_ref_type', create_type=False),
        existing_nullable=True,
        postgresql_using='manipulated_reference_type::procedure_focal_device_ref_type',
    )
    op.alter_column('procedure_focal_device', 'manipulated_display',
                    new_column_name='manipulated_reference_display')

    # ── 11. procedure_used_reference: String → Enum ────────────────────────────
    _used_ref.create(bind, checkfirst=True)
    op.alter_column(
        'procedure_used_reference', 'reference_type',
        existing_type=sa.VARCHAR(),
        type_=postgresql.ENUM('Device', 'Medication', 'Substance',
                              name='procedure_used_ref_type', create_type=False),
        existing_nullable=True,
        postgresql_using='reference_type::procedure_used_ref_type',
    )


def downgrade() -> None:
    bind = op.get_bind()

    # ── Reverse used_reference ─────────────────────────────────────────────────
    op.alter_column(
        'procedure_used_reference', 'reference_type',
        existing_type=postgresql.ENUM('Device', 'Medication', 'Substance',
                                      name='procedure_used_ref_type', create_type=False),
        type_=sa.VARCHAR(),
        existing_nullable=True,
    )
    _used_ref.drop(bind, checkfirst=True)

    # ── Reverse focal_device ───────────────────────────────────────────────────
    op.alter_column('procedure_focal_device', 'manipulated_reference_display',
                    new_column_name='manipulated_display')
    op.alter_column(
        'procedure_focal_device', 'manipulated_reference_type',
        existing_type=postgresql.ENUM('Device', name='procedure_focal_device_ref_type', create_type=False),
        type_=sa.VARCHAR(),
        existing_nullable=True,
    )
    _focal_device_ref.drop(bind, checkfirst=True)

    # ── Reverse note ───────────────────────────────────────────────────────────
    op.alter_column('procedure_note', 'author_reference_display',
                    new_column_name='author_display')
    op.alter_column(
        'procedure_note', 'author_reference_type',
        existing_type=postgresql.ENUM(
            'Practitioner', 'Patient', 'RelatedPerson', 'Organization',
            name='procedure_note_author_ref_type', create_type=False,
        ),
        type_=sa.VARCHAR(),
        existing_nullable=True,
    )
    _note_author_ref.drop(bind, checkfirst=True)

    # ── Reverse complication_detail ────────────────────────────────────────────
    op.alter_column(
        'procedure_complication_detail', 'reference_type',
        existing_type=postgresql.ENUM('Condition', name='procedure_complication_detail_ref_type', create_type=False),
        type_=sa.VARCHAR(),
        existing_nullable=True,
    )
    _complication_detail_ref.drop(bind, checkfirst=True)

    # ── Reverse report ─────────────────────────────────────────────────────────
    op.alter_column(
        'procedure_report', 'reference_type',
        existing_type=postgresql.ENUM('DiagnosticReport', 'DocumentReference', 'Composition',
                                      name='procedure_report_ref_type', create_type=False),
        type_=sa.VARCHAR(),
        existing_nullable=True,
    )
    _report_ref.drop(bind, checkfirst=True)

    # ── Reverse reason_reference ───────────────────────────────────────────────
    op.alter_column(
        'procedure_reason_reference', 'reference_type',
        existing_type=postgresql.ENUM(
            'Condition', 'Observation', 'Procedure', 'DiagnosticReport', 'DocumentReference',
            name='procedure_reason_ref_type', create_type=False,
        ),
        type_=sa.VARCHAR(),
        existing_nullable=True,
    )
    _reason_ref.drop(bind, checkfirst=True)

    # ── Reverse performer on_behalf_of_type ────────────────────────────────────
    op.drop_column('procedure_performer', 'on_behalf_of_type')
    _on_behalf_of.drop(bind, checkfirst=True)

    # ── Reverse part_of ────────────────────────────────────────────────────────
    op.alter_column(
        'procedure_part_of', 'reference_type',
        existing_type=postgresql.ENUM('Procedure', 'Observation', 'MedicationAdministration',
                                      name='procedure_part_of_ref_type', create_type=False),
        type_=sa.VARCHAR(),
        existing_nullable=True,
    )
    _part_of_ref.drop(bind, checkfirst=True)

    # ── Reverse based_on ───────────────────────────────────────────────────────
    op.alter_column(
        'procedure_based_on', 'reference_type',
        existing_type=postgresql.ENUM('CarePlan', 'ServiceRequest',
                                      name='procedure_based_on_ref_type', create_type=False),
        type_=sa.VARCHAR(),
        existing_nullable=True,
    )
    _based_on_ref.drop(bind, checkfirst=True)

    # ── Reverse identifier type_text ───────────────────────────────────────────
    op.drop_column('procedure_identifier', 'type_text')

    # ── Reverse location_type ──────────────────────────────────────────────────
    op.drop_column('procedure', 'location_type')
    _location_ref.drop(bind, checkfirst=True)
