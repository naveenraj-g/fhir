"""refactor_diagnostic_report_enums_and_identifier_fields

Revision ID: e3b169890e0d
Revises: 74f166a2b077
Create Date: 2026-05-15 22:57:59.199710

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'e3b169890e0d'
down_revision: Union[str, None] = '74f166a2b077'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_based_on_ref_type = postgresql.ENUM(
    'CarePlan', 'ImmunizationRecommendation', 'MedicationRequest', 'NutritionOrder', 'ServiceRequest',
    name='dr_based_on_ref_type',
)
_imaging_study_ref_type = postgresql.ENUM('ImagingStudy', name='dr_imaging_study_ref_type')
_media_link_ref_type = postgresql.ENUM('Media', name='dr_media_link_ref_type')
_result_ref_type = postgresql.ENUM('Observation', name='dr_result_ref_type')
_specimen_ref_type = postgresql.ENUM('Specimen', name='dr_specimen_ref_type')


def upgrade() -> None:
    bind = op.get_bind()

    # ── 1. diagnostic_report_based_on: reference_type VARCHAR → Enum ──────────
    _based_on_ref_type.create(bind, checkfirst=True)
    op.alter_column(
        'diagnostic_report_based_on', 'reference_type',
        existing_type=sa.VARCHAR(),
        type_=postgresql.ENUM(
            'CarePlan', 'ImmunizationRecommendation', 'MedicationRequest', 'NutritionOrder', 'ServiceRequest',
            name='dr_based_on_ref_type', create_type=False,
        ),
        existing_nullable=True,
        postgresql_using='reference_type::dr_based_on_ref_type',
    )

    # ── 2. diagnostic_report_identifier: add type_text ────────────────────────
    op.add_column('diagnostic_report_identifier', sa.Column('type_text', sa.String(), nullable=True))

    # ── 3. diagnostic_report_imaging_study: reference_type VARCHAR → Enum ─────
    _imaging_study_ref_type.create(bind, checkfirst=True)
    op.alter_column(
        'diagnostic_report_imaging_study', 'reference_type',
        existing_type=sa.VARCHAR(),
        type_=postgresql.ENUM('ImagingStudy', name='dr_imaging_study_ref_type', create_type=False),
        existing_nullable=True,
        postgresql_using='reference_type::dr_imaging_study_ref_type',
    )

    # ── 4. diagnostic_report_media: rename link_display → link_reference_display
    op.alter_column('diagnostic_report_media', 'link_display',
                    new_column_name='link_reference_display')

    # ── 5. diagnostic_report_media: link_reference_type VARCHAR → Enum ────────
    _media_link_ref_type.create(bind, checkfirst=True)
    op.alter_column(
        'diagnostic_report_media', 'link_reference_type',
        existing_type=sa.VARCHAR(),
        type_=postgresql.ENUM('Media', name='dr_media_link_ref_type', create_type=False),
        existing_nullable=True,
        postgresql_using='link_reference_type::dr_media_link_ref_type',
    )

    # ── 6. diagnostic_report_result: reference_type VARCHAR → Enum ───────────
    _result_ref_type.create(bind, checkfirst=True)
    op.alter_column(
        'diagnostic_report_result', 'reference_type',
        existing_type=sa.VARCHAR(),
        type_=postgresql.ENUM('Observation', name='dr_result_ref_type', create_type=False),
        existing_nullable=True,
        postgresql_using='reference_type::dr_result_ref_type',
    )

    # ── 7. diagnostic_report_specimen: reference_type VARCHAR → Enum ─────────
    _specimen_ref_type.create(bind, checkfirst=True)
    op.alter_column(
        'diagnostic_report_specimen', 'reference_type',
        existing_type=sa.VARCHAR(),
        type_=postgresql.ENUM('Specimen', name='dr_specimen_ref_type', create_type=False),
        existing_nullable=True,
        postgresql_using='reference_type::dr_specimen_ref_type',
    )


def downgrade() -> None:
    bind = op.get_bind()

    # ── Reverse specimen enum ─────────────────────────────────────────────────
    op.alter_column(
        'diagnostic_report_specimen', 'reference_type',
        existing_type=postgresql.ENUM('Specimen', name='dr_specimen_ref_type', create_type=False),
        type_=sa.VARCHAR(),
        existing_nullable=True,
    )
    _specimen_ref_type.drop(bind, checkfirst=True)

    # ── Reverse result enum ───────────────────────────────────────────────────
    op.alter_column(
        'diagnostic_report_result', 'reference_type',
        existing_type=postgresql.ENUM('Observation', name='dr_result_ref_type', create_type=False),
        type_=sa.VARCHAR(),
        existing_nullable=True,
    )
    _result_ref_type.drop(bind, checkfirst=True)

    # ── Reverse media link_reference_type enum ────────────────────────────────
    op.alter_column(
        'diagnostic_report_media', 'link_reference_type',
        existing_type=postgresql.ENUM('Media', name='dr_media_link_ref_type', create_type=False),
        type_=sa.VARCHAR(),
        existing_nullable=True,
    )
    _media_link_ref_type.drop(bind, checkfirst=True)

    # ── Reverse media link_reference_display rename ───────────────────────────
    op.alter_column('diagnostic_report_media', 'link_reference_display',
                    new_column_name='link_display')

    # ── Reverse imaging_study enum ────────────────────────────────────────────
    op.alter_column(
        'diagnostic_report_imaging_study', 'reference_type',
        existing_type=postgresql.ENUM('ImagingStudy', name='dr_imaging_study_ref_type', create_type=False),
        type_=sa.VARCHAR(),
        existing_nullable=True,
    )
    _imaging_study_ref_type.drop(bind, checkfirst=True)

    # ── Reverse identifier type_text ──────────────────────────────────────────
    op.drop_column('diagnostic_report_identifier', 'type_text')

    # ── Reverse based_on enum ─────────────────────────────────────────────────
    op.alter_column(
        'diagnostic_report_based_on', 'reference_type',
        existing_type=postgresql.ENUM(
            'CarePlan', 'ImmunizationRecommendation', 'MedicationRequest', 'NutritionOrder', 'ServiceRequest',
            name='dr_based_on_ref_type', create_type=False,
        ),
        type_=sa.VARCHAR(),
        existing_nullable=True,
    )
    _based_on_ref_type.drop(bind, checkfirst=True)
