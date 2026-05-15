"""refactor_qr_author_source_columns

Revision ID: 986e9cd5def8
Revises: 8134f5a74134
Create Date: 2026-05-15 18:32:08.018127

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '986e9cd5def8'
down_revision: Union[str, None] = '8134f5a74134'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# New enum types with correct TitleCase FHIR values
_author_ref_type = postgresql.ENUM(
    'Device', 'Practitioner', 'PractitionerRole', 'Patient', 'RelatedPerson', 'Organization',
    name='author_reference_type',
)
_source_ref_type = postgresql.ENUM(
    'Device', 'Organization', 'Patient', 'Practitioner', 'PractitionerRole', 'RelatedPerson',
    name='source_reference_type',
)


def upgrade() -> None:
    bind = op.get_bind()

    # Drop old columns (they used incorrectly-cased uppercase enum values)
    op.drop_column('questionnaire_response', 'author_reference_display')
    op.drop_column('questionnaire_response', 'author_reference_id')
    op.drop_column('questionnaire_response', 'author_reference_type')
    op.drop_column('questionnaire_response', 'source_reference_display')
    op.drop_column('questionnaire_response', 'source_reference_id')
    op.drop_column('questionnaire_response', 'source_reference_type')

    # Drop the incorrectly-valued enum types
    op.execute('DROP TYPE IF EXISTS author_reference_type')
    op.execute('DROP TYPE IF EXISTS source_reference_type')

    # Recreate with correct TitleCase FHIR values
    _author_ref_type.create(bind, checkfirst=True)
    _source_ref_type.create(bind, checkfirst=True)

    # Add renamed columns with correct enum types
    op.add_column('questionnaire_response', sa.Column(
        'author_type',
        postgresql.ENUM('Device', 'Practitioner', 'PractitionerRole', 'Patient', 'RelatedPerson', 'Organization',
                        name='author_reference_type', create_type=False),
        nullable=True,
    ))
    op.add_column('questionnaire_response', sa.Column('author_id', sa.Integer(), nullable=True))
    op.add_column('questionnaire_response', sa.Column('author_display', sa.String(), nullable=True))

    op.add_column('questionnaire_response', sa.Column(
        'source_type',
        postgresql.ENUM('Device', 'Organization', 'Patient', 'Practitioner', 'PractitionerRole', 'RelatedPerson',
                        name='source_reference_type', create_type=False),
        nullable=True,
    ))
    op.add_column('questionnaire_response', sa.Column('source_id', sa.Integer(), nullable=True))
    op.add_column('questionnaire_response', sa.Column('source_display', sa.String(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_column('questionnaire_response', 'source_display')
    op.drop_column('questionnaire_response', 'source_id')
    op.drop_column('questionnaire_response', 'source_type')
    op.drop_column('questionnaire_response', 'author_display')
    op.drop_column('questionnaire_response', 'author_id')
    op.drop_column('questionnaire_response', 'author_type')

    op.execute('DROP TYPE IF EXISTS author_reference_type')
    op.execute('DROP TYPE IF EXISTS source_reference_type')

    # Restore old incorrectly-cased types and columns
    op.execute("CREATE TYPE author_reference_type AS ENUM ('DEVICE', 'PRACTITIONER', 'PRACTITIONER_ROLE', 'PATIENT', 'RELATED_PERSON', 'ORGANIZATION')")
    op.execute("CREATE TYPE source_reference_type AS ENUM ('DEVICE', 'ORGANIZATION', 'PATIENT', 'PRACTITIONER', 'PRACTITIONER_ROLE', 'RELATED_PERSON')")

    op.add_column('questionnaire_response', sa.Column(
        'author_reference_type',
        postgresql.ENUM('DEVICE', 'PRACTITIONER', 'PRACTITIONER_ROLE', 'PATIENT', 'RELATED_PERSON', 'ORGANIZATION',
                        name='author_reference_type', create_type=False),
        nullable=True,
    ))
    op.add_column('questionnaire_response', sa.Column('author_reference_id', sa.Integer(), nullable=True))
    op.add_column('questionnaire_response', sa.Column('author_reference_display', sa.String(), nullable=True))
    op.add_column('questionnaire_response', sa.Column(
        'source_reference_type',
        postgresql.ENUM('DEVICE', 'ORGANIZATION', 'PATIENT', 'PRACTITIONER', 'PRACTITIONER_ROLE', 'RELATED_PERSON',
                        name='source_reference_type', create_type=False),
        nullable=True,
    ))
    op.add_column('questionnaire_response', sa.Column('source_reference_id', sa.Integer(), nullable=True))
    op.add_column('questionnaire_response', sa.Column('source_reference_display', sa.String(), nullable=True))
