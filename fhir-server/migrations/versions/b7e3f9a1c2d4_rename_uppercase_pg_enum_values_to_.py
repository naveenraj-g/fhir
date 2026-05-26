"""rename_uppercase_pg_enum_values_to_lowercase

Revision ID: b7e3f9a1c2d4
Revises: a1b2c3d4e5f6
Create Date: 2026-05-26 20:07:05.966108

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7e3f9a1c2d4'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _rename(type_name: str, old: str, new: str) -> None:
    op.execute(f"ALTER TYPE {type_name} RENAME VALUE '{old}' TO '{new}'")


def upgrade() -> None:
    # patient_gender: MALE/FEMALE/OTHER/UNKNOWN → lowercase
    _rename('patient_gender', 'MALE', 'male')
    _rename('patient_gender', 'FEMALE', 'female')
    _rename('patient_gender', 'OTHER', 'other')
    _rename('patient_gender', 'UNKNOWN', 'unknown')

    # patient_link_type: REPLACED_BY/REPLACES/REFER/SEEALSO → snake_case
    _rename('patient_link_type', 'REPLACED_BY', 'replaced_by')
    _rename('patient_link_type', 'REPLACES', 'replaces')
    _rename('patient_link_type', 'REFER', 'refer')
    _rename('patient_link_type', 'SEEALSO', 'seealso')

    # dr_status (DiagnosticReport.status): UPPERCASE → lowercase
    _rename('dr_status', 'REGISTERED', 'registered')
    _rename('dr_status', 'PARTIAL', 'partial')
    _rename('dr_status', 'PRELIMINARY', 'preliminary')
    _rename('dr_status', 'FINAL', 'final')
    _rename('dr_status', 'AMENDED', 'amended')
    _rename('dr_status', 'CORRECTED', 'corrected')
    _rename('dr_status', 'APPENDED', 'appended')
    _rename('dr_status', 'CANCELLED', 'cancelled')
    _rename('dr_status', 'ENTERED_IN_ERROR', 'entered_in_error')
    _rename('dr_status', 'UNKNOWN', 'unknown')

    # mr_status (MedicationRequest.status): UPPERCASE → lowercase
    _rename('mr_status', 'ACTIVE', 'active')
    _rename('mr_status', 'ON_HOLD', 'on_hold')
    _rename('mr_status', 'CANCELLED', 'cancelled')
    _rename('mr_status', 'COMPLETED', 'completed')
    _rename('mr_status', 'ENTERED_IN_ERROR', 'entered_in_error')
    _rename('mr_status', 'STOPPED', 'stopped')
    _rename('mr_status', 'DRAFT', 'draft')
    _rename('mr_status', 'UNKNOWN', 'unknown')

    # mr_intent (MedicationRequest.intent): UPPERCASE → lowercase
    _rename('mr_intent', 'PROPOSAL', 'proposal')
    _rename('mr_intent', 'PLAN', 'plan')
    _rename('mr_intent', 'ORDER', 'order')
    _rename('mr_intent', 'ORIGINAL_ORDER', 'original_order')
    _rename('mr_intent', 'REFLEX_ORDER', 'reflex_order')
    _rename('mr_intent', 'FILLER_ORDER', 'filler_order')
    _rename('mr_intent', 'INSTANCE_ORDER', 'instance_order')
    _rename('mr_intent', 'OPTION', 'option')

    # mr_priority (MedicationRequest.priority): UPPERCASE → lowercase
    _rename('mr_priority', 'ROUTINE', 'routine')
    _rename('mr_priority', 'URGENT', 'urgent')
    _rename('mr_priority', 'ASAP', 'asap')
    _rename('mr_priority', 'STAT', 'stat')

    # procedure_status: UPPERCASE → lowercase
    _rename('procedure_status', 'PREPARATION', 'preparation')
    _rename('procedure_status', 'IN_PROGRESS', 'in_progress')
    _rename('procedure_status', 'NOT_DONE', 'not_done')
    _rename('procedure_status', 'ON_HOLD', 'on_hold')
    _rename('procedure_status', 'STOPPED', 'stopped')
    _rename('procedure_status', 'COMPLETED', 'completed')
    _rename('procedure_status', 'ENTERED_IN_ERROR', 'entered_in_error')
    _rename('procedure_status', 'UNKNOWN', 'unknown')

    # sr_status (ServiceRequest.status): UPPERCASE → lowercase
    _rename('sr_status', 'DRAFT', 'draft')
    _rename('sr_status', 'ACTIVE', 'active')
    _rename('sr_status', 'ON_HOLD', 'on_hold')
    _rename('sr_status', 'REVOKED', 'revoked')
    _rename('sr_status', 'COMPLETED', 'completed')
    _rename('sr_status', 'ENTERED_IN_ERROR', 'entered_in_error')
    _rename('sr_status', 'UNKNOWN', 'unknown')

    # sr_intent (ServiceRequest.intent): UPPERCASE → lowercase
    _rename('sr_intent', 'PROPOSAL', 'proposal')
    _rename('sr_intent', 'PLAN', 'plan')
    _rename('sr_intent', 'DIRECTIVE', 'directive')
    _rename('sr_intent', 'ORDER', 'order')
    _rename('sr_intent', 'ORIGINAL_ORDER', 'original_order')
    _rename('sr_intent', 'REFLEX_ORDER', 'reflex_order')
    _rename('sr_intent', 'FILLER_ORDER', 'filler_order')
    _rename('sr_intent', 'INSTANCE_ORDER', 'instance_order')
    _rename('sr_intent', 'OPTION', 'option')

    # sr_priority (ServiceRequest.priority): UPPERCASE → lowercase
    _rename('sr_priority', 'ROUTINE', 'routine')
    _rename('sr_priority', 'URGENT', 'urgent')
    _rename('sr_priority', 'ASAP', 'asap')
    _rename('sr_priority', 'STAT', 'stat')

    # dr_req_status (DeviceRequest.status): UPPERCASE → lowercase
    _rename('dr_req_status', 'DRAFT', 'draft')
    _rename('dr_req_status', 'ACTIVE', 'active')
    _rename('dr_req_status', 'ON_HOLD', 'on_hold')
    _rename('dr_req_status', 'REVOKED', 'revoked')
    _rename('dr_req_status', 'COMPLETED', 'completed')
    _rename('dr_req_status', 'ENTERED_IN_ERROR', 'entered_in_error')
    _rename('dr_req_status', 'UNKNOWN', 'unknown')

    # dr_req_intent (DeviceRequest.intent): UPPERCASE → lowercase
    _rename('dr_req_intent', 'PROPOSAL', 'proposal')
    _rename('dr_req_intent', 'PLAN', 'plan')
    _rename('dr_req_intent', 'DIRECTIVE', 'directive')
    _rename('dr_req_intent', 'ORDER', 'order')
    _rename('dr_req_intent', 'ORIGINAL_ORDER', 'original_order')
    _rename('dr_req_intent', 'REFLEX_ORDER', 'reflex_order')
    _rename('dr_req_intent', 'FILLER_ORDER', 'filler_order')
    _rename('dr_req_intent', 'INSTANCE_ORDER', 'instance_order')
    _rename('dr_req_intent', 'OPTION', 'option')

    # dr_req_priority (DeviceRequest.priority): UPPERCASE → lowercase
    _rename('dr_req_priority', 'ROUTINE', 'routine')
    _rename('dr_req_priority', 'URGENT', 'urgent')
    _rename('dr_req_priority', 'ASAP', 'asap')
    _rename('dr_req_priority', 'STAT', 'stat')


def downgrade() -> None:
    # dr_req_priority
    _rename('dr_req_priority', 'routine', 'ROUTINE')
    _rename('dr_req_priority', 'urgent', 'URGENT')
    _rename('dr_req_priority', 'asap', 'ASAP')
    _rename('dr_req_priority', 'stat', 'STAT')

    # dr_req_intent
    _rename('dr_req_intent', 'proposal', 'PROPOSAL')
    _rename('dr_req_intent', 'plan', 'PLAN')
    _rename('dr_req_intent', 'directive', 'DIRECTIVE')
    _rename('dr_req_intent', 'order', 'ORDER')
    _rename('dr_req_intent', 'original_order', 'ORIGINAL_ORDER')
    _rename('dr_req_intent', 'reflex_order', 'REFLEX_ORDER')
    _rename('dr_req_intent', 'filler_order', 'FILLER_ORDER')
    _rename('dr_req_intent', 'instance_order', 'INSTANCE_ORDER')
    _rename('dr_req_intent', 'option', 'OPTION')

    # dr_req_status
    _rename('dr_req_status', 'draft', 'DRAFT')
    _rename('dr_req_status', 'active', 'ACTIVE')
    _rename('dr_req_status', 'on_hold', 'ON_HOLD')
    _rename('dr_req_status', 'revoked', 'REVOKED')
    _rename('dr_req_status', 'completed', 'COMPLETED')
    _rename('dr_req_status', 'entered_in_error', 'ENTERED_IN_ERROR')
    _rename('dr_req_status', 'unknown', 'UNKNOWN')

    # sr_priority
    _rename('sr_priority', 'routine', 'ROUTINE')
    _rename('sr_priority', 'urgent', 'URGENT')
    _rename('sr_priority', 'asap', 'ASAP')
    _rename('sr_priority', 'stat', 'STAT')

    # sr_intent
    _rename('sr_intent', 'proposal', 'PROPOSAL')
    _rename('sr_intent', 'plan', 'PLAN')
    _rename('sr_intent', 'directive', 'DIRECTIVE')
    _rename('sr_intent', 'order', 'ORDER')
    _rename('sr_intent', 'original_order', 'ORIGINAL_ORDER')
    _rename('sr_intent', 'reflex_order', 'REFLEX_ORDER')
    _rename('sr_intent', 'filler_order', 'FILLER_ORDER')
    _rename('sr_intent', 'instance_order', 'INSTANCE_ORDER')
    _rename('sr_intent', 'option', 'OPTION')

    # sr_status
    _rename('sr_status', 'draft', 'DRAFT')
    _rename('sr_status', 'active', 'ACTIVE')
    _rename('sr_status', 'on_hold', 'ON_HOLD')
    _rename('sr_status', 'revoked', 'REVOKED')
    _rename('sr_status', 'completed', 'COMPLETED')
    _rename('sr_status', 'entered_in_error', 'ENTERED_IN_ERROR')
    _rename('sr_status', 'unknown', 'UNKNOWN')

    # procedure_status
    _rename('procedure_status', 'preparation', 'PREPARATION')
    _rename('procedure_status', 'in_progress', 'IN_PROGRESS')
    _rename('procedure_status', 'not_done', 'NOT_DONE')
    _rename('procedure_status', 'on_hold', 'ON_HOLD')
    _rename('procedure_status', 'stopped', 'STOPPED')
    _rename('procedure_status', 'completed', 'COMPLETED')
    _rename('procedure_status', 'entered_in_error', 'ENTERED_IN_ERROR')
    _rename('procedure_status', 'unknown', 'UNKNOWN')

    # mr_priority
    _rename('mr_priority', 'routine', 'ROUTINE')
    _rename('mr_priority', 'urgent', 'URGENT')
    _rename('mr_priority', 'asap', 'ASAP')
    _rename('mr_priority', 'stat', 'STAT')

    # mr_intent
    _rename('mr_intent', 'proposal', 'PROPOSAL')
    _rename('mr_intent', 'plan', 'PLAN')
    _rename('mr_intent', 'order', 'ORDER')
    _rename('mr_intent', 'original_order', 'ORIGINAL_ORDER')
    _rename('mr_intent', 'reflex_order', 'REFLEX_ORDER')
    _rename('mr_intent', 'filler_order', 'FILLER_ORDER')
    _rename('mr_intent', 'instance_order', 'INSTANCE_ORDER')
    _rename('mr_intent', 'option', 'OPTION')

    # mr_status
    _rename('mr_status', 'active', 'ACTIVE')
    _rename('mr_status', 'on_hold', 'ON_HOLD')
    _rename('mr_status', 'cancelled', 'CANCELLED')
    _rename('mr_status', 'completed', 'COMPLETED')
    _rename('mr_status', 'entered_in_error', 'ENTERED_IN_ERROR')
    _rename('mr_status', 'stopped', 'STOPPED')
    _rename('mr_status', 'draft', 'DRAFT')
    _rename('mr_status', 'unknown', 'UNKNOWN')

    # dr_status
    _rename('dr_status', 'registered', 'REGISTERED')
    _rename('dr_status', 'partial', 'PARTIAL')
    _rename('dr_status', 'preliminary', 'PRELIMINARY')
    _rename('dr_status', 'final', 'FINAL')
    _rename('dr_status', 'amended', 'AMENDED')
    _rename('dr_status', 'corrected', 'CORRECTED')
    _rename('dr_status', 'appended', 'APPENDED')
    _rename('dr_status', 'cancelled', 'CANCELLED')
    _rename('dr_status', 'entered_in_error', 'ENTERED_IN_ERROR')
    _rename('dr_status', 'unknown', 'UNKNOWN')

    # patient_link_type
    _rename('patient_link_type', 'replaced_by', 'REPLACED_BY')
    _rename('patient_link_type', 'replaces', 'REPLACES')
    _rename('patient_link_type', 'refer', 'REFER')
    _rename('patient_link_type', 'seealso', 'SEEALSO')

    # patient_gender
    _rename('patient_gender', 'male', 'MALE')
    _rename('patient_gender', 'female', 'FEMALE')
    _rename('patient_gender', 'other', 'OTHER')
    _rename('patient_gender', 'unknown', 'UNKNOWN')
