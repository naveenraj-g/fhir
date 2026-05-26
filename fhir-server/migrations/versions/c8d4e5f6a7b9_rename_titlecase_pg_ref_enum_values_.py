"""rename_titlecase_pg_reference_type_enum_values_to_uppercase

Revision ID: c8d4e5f6a7b9
Revises: b7e3f9a1c2d4
Create Date: 2026-05-26 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c8d4e5f6a7b9'
down_revision: Union[str, None] = 'b7e3f9a1c2d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _rename(type_name: str, old: str, new: str) -> None:
    """Rename PG enum value only if it exists with the old name."""
    op.execute(sa.text(
        f"""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_enum e
                JOIN pg_type t ON e.enumtypid = t.oid
                WHERE t.typname = '{type_name}' AND e.enumlabel = '{old}'
            ) THEN
                ALTER TYPE {type_name} RENAME VALUE '{old}' TO '{new}';
            END IF;
        END $$;
        """
    ))


def upgrade() -> None:
    # allergy_intolerance_participant_reference_type
    _rename('allergy_intolerance_participant_reference_type', 'Patient', 'PATIENT')
    _rename('allergy_intolerance_participant_reference_type', 'Practitioner', 'PRACTITIONER')
    _rename('allergy_intolerance_participant_reference_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    _rename('allergy_intolerance_participant_reference_type', 'RelatedPerson', 'RELATED_PERSON')
    # allergy_intolerance_patient_reference_type
    _rename('allergy_intolerance_patient_reference_type', 'Patient', 'PATIENT')
    # appointment_account_reference_type
    _rename('appointment_account_reference_type', 'Account', 'ACCOUNT')
    # appointment_based_on_reference_type
    _rename('appointment_based_on_reference_type', 'CarePlan', 'CARE_PLAN')
    _rename('appointment_based_on_reference_type', 'DeviceRequest', 'DEVICE_REQUEST')
    _rename('appointment_based_on_reference_type', 'MedicationRequest', 'MEDICATION_REQUEST')
    _rename('appointment_based_on_reference_type', 'NutritionOrder', 'NUTRITION_ORDER')
    _rename('appointment_based_on_reference_type', 'RequestOrchestration', 'REQUEST_ORCHESTRATION')
    _rename('appointment_based_on_reference_type', 'ServiceRequest', 'SERVICE_REQUEST')
    _rename('appointment_based_on_reference_type', 'VisionPrescription', 'VISION_PRESCRIPTION')
    # appointment_note_author_reference_type
    _rename('appointment_note_author_reference_type', 'Organization', 'ORGANIZATION')
    _rename('appointment_note_author_reference_type', 'Patient', 'PATIENT')
    _rename('appointment_note_author_reference_type', 'Practitioner', 'PRACTITIONER')
    _rename('appointment_note_author_reference_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    _rename('appointment_note_author_reference_type', 'RelatedPerson', 'RELATED_PERSON')
    # appointment_participant_actor_type
    _rename('appointment_participant_actor_type', 'CareTeam', 'CARE_TEAM')
    _rename('appointment_participant_actor_type', 'Device', 'DEVICE')
    _rename('appointment_participant_actor_type', 'Group', 'GROUP')
    _rename('appointment_participant_actor_type', 'HealthcareService', 'HEALTHCARE_SERVICE')
    _rename('appointment_participant_actor_type', 'Location', 'LOCATION')
    _rename('appointment_participant_actor_type', 'Patient', 'PATIENT')
    _rename('appointment_participant_actor_type', 'Practitioner', 'PRACTITIONER')
    _rename('appointment_participant_actor_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    _rename('appointment_participant_actor_type', 'RelatedPerson', 'RELATED_PERSON')
    # appointment_pi_reference_type
    _rename('appointment_pi_reference_type', 'Binary', 'BINARY')
    _rename('appointment_pi_reference_type', 'Communication', 'COMMUNICATION')
    _rename('appointment_pi_reference_type', 'DocumentReference', 'DOCUMENT_REFERENCE')
    # appointment_reason_reference_type
    _rename('appointment_reason_reference_type', 'Condition', 'CONDITION')
    _rename('appointment_reason_reference_type', 'DiagnosticReport', 'DIAGNOSTIC_REPORT')
    _rename('appointment_reason_reference_type', 'ImmunizationRecommendation', 'IMMUNIZATION_RECOMMENDATION')
    _rename('appointment_reason_reference_type', 'Observation', 'OBSERVATION')
    _rename('appointment_reason_reference_type', 'Procedure', 'PROCEDURE')
    # appointment_replaces_reference_type
    _rename('appointment_replaces_reference_type', 'Appointment', 'APPOINTMENT')
    # appointment_service_type_reference_type
    _rename('appointment_service_type_reference_type', 'HealthcareService', 'HEALTHCARE_SERVICE')
    # appointment_slot_reference_type
    _rename('appointment_slot_reference_type', 'Slot', 'SLOT')
    # audit_event_location_reference_type
    _rename('audit_event_location_reference_type', 'Location', 'LOCATION')
    # audit_event_who_reference_type
    _rename('audit_event_who_reference_type', 'Device', 'DEVICE')
    _rename('audit_event_who_reference_type', 'Organization', 'ORGANIZATION')
    _rename('audit_event_who_reference_type', 'Patient', 'PATIENT')
    _rename('audit_event_who_reference_type', 'Practitioner', 'PRACTITIONER')
    _rename('audit_event_who_reference_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    _rename('audit_event_who_reference_type', 'RelatedPerson', 'RELATED_PERSON')
    # author_reference_type
    _rename('author_reference_type', 'Device', 'DEVICE')
    _rename('author_reference_type', 'Organization', 'ORGANIZATION')
    _rename('author_reference_type', 'Patient', 'PATIENT')
    _rename('author_reference_type', 'Practitioner', 'PRACTITIONER')
    _rename('author_reference_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    _rename('author_reference_type', 'RelatedPerson', 'RELATED_PERSON')
    # care_plan_activity_reference_type
    _rename('care_plan_activity_reference_type', 'Appointment', 'APPOINTMENT')
    _rename('care_plan_activity_reference_type', 'CommunicationRequest', 'COMMUNICATION_REQUEST')
    _rename('care_plan_activity_reference_type', 'DeviceRequest', 'DEVICE_REQUEST')
    _rename('care_plan_activity_reference_type', 'MedicationRequest', 'MEDICATION_REQUEST')
    _rename('care_plan_activity_reference_type', 'NutritionOrder', 'NUTRITION_ORDER')
    _rename('care_plan_activity_reference_type', 'RequestGroup', 'REQUEST_GROUP')
    _rename('care_plan_activity_reference_type', 'ServiceRequest', 'SERVICE_REQUEST')
    _rename('care_plan_activity_reference_type', 'Task', 'TASK')
    _rename('care_plan_activity_reference_type', 'VisionPrescription', 'VISION_PRESCRIPTION')
    # care_plan_addresses_reference_type
    _rename('care_plan_addresses_reference_type', 'Condition', 'CONDITION')
    # care_plan_author_reference_type
    _rename('care_plan_author_reference_type', 'CareTeam', 'CARE_TEAM')
    _rename('care_plan_author_reference_type', 'Device', 'DEVICE')
    _rename('care_plan_author_reference_type', 'Organization', 'ORGANIZATION')
    _rename('care_plan_author_reference_type', 'Patient', 'PATIENT')
    _rename('care_plan_author_reference_type', 'Practitioner', 'PRACTITIONER')
    _rename('care_plan_author_reference_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    _rename('care_plan_author_reference_type', 'RelatedPerson', 'RELATED_PERSON')
    # care_plan_based_on_reference_type
    _rename('care_plan_based_on_reference_type', 'CarePlan', 'CARE_PLAN')
    # care_plan_care_team_reference_type
    _rename('care_plan_care_team_reference_type', 'CareTeam', 'CARE_TEAM')
    # care_plan_contributor_reference_type
    _rename('care_plan_contributor_reference_type', 'CareTeam', 'CARE_TEAM')
    _rename('care_plan_contributor_reference_type', 'Device', 'DEVICE')
    _rename('care_plan_contributor_reference_type', 'Organization', 'ORGANIZATION')
    _rename('care_plan_contributor_reference_type', 'Patient', 'PATIENT')
    _rename('care_plan_contributor_reference_type', 'Practitioner', 'PRACTITIONER')
    _rename('care_plan_contributor_reference_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    _rename('care_plan_contributor_reference_type', 'RelatedPerson', 'RELATED_PERSON')
    # care_plan_detail_goal_reference_type
    _rename('care_plan_detail_goal_reference_type', 'Goal', 'GOAL')
    # care_plan_detail_location_reference_type
    _rename('care_plan_detail_location_reference_type', 'Location', 'LOCATION')
    # care_plan_detail_performer_reference_type
    _rename('care_plan_detail_performer_reference_type', 'CareTeam', 'CARE_TEAM')
    _rename('care_plan_detail_performer_reference_type', 'Device', 'DEVICE')
    _rename('care_plan_detail_performer_reference_type', 'HealthcareService', 'HEALTHCARE_SERVICE')
    _rename('care_plan_detail_performer_reference_type', 'Organization', 'ORGANIZATION')
    _rename('care_plan_detail_performer_reference_type', 'Patient', 'PATIENT')
    _rename('care_plan_detail_performer_reference_type', 'Practitioner', 'PRACTITIONER')
    _rename('care_plan_detail_performer_reference_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    _rename('care_plan_detail_performer_reference_type', 'RelatedPerson', 'RELATED_PERSON')
    # care_plan_detail_product_reference_type
    _rename('care_plan_detail_product_reference_type', 'Medication', 'MEDICATION')
    _rename('care_plan_detail_product_reference_type', 'Substance', 'SUBSTANCE')
    # care_plan_detail_reason_reference_type
    _rename('care_plan_detail_reason_reference_type', 'Condition', 'CONDITION')
    _rename('care_plan_detail_reason_reference_type', 'DiagnosticReport', 'DIAGNOSTIC_REPORT')
    _rename('care_plan_detail_reason_reference_type', 'DocumentReference', 'DOCUMENT_REFERENCE')
    _rename('care_plan_detail_reason_reference_type', 'Observation', 'OBSERVATION')
    # care_plan_goal_reference_type
    _rename('care_plan_goal_reference_type', 'Goal', 'GOAL')
    # care_plan_part_of_reference_type
    _rename('care_plan_part_of_reference_type', 'CarePlan', 'CARE_PLAN')
    # care_plan_replaces_reference_type
    _rename('care_plan_replaces_reference_type', 'CarePlan', 'CARE_PLAN')
    # care_plan_subject_reference_type
    _rename('care_plan_subject_reference_type', 'Group', 'GROUP')
    _rename('care_plan_subject_reference_type', 'Patient', 'PATIENT')
    # claim_device_ref_type
    _rename('claim_device_ref_type', 'Device', 'DEVICE')
    # claim_diagnosis_condition_ref_type
    _rename('claim_diagnosis_condition_ref_type', 'Condition', 'CONDITION')
    # claim_enterer_ref_type
    _rename('claim_enterer_ref_type', 'Practitioner', 'PRACTITIONER')
    _rename('claim_enterer_ref_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    # claim_insurance_claim_response_ref_type
    _rename('claim_insurance_claim_response_ref_type', 'ClaimResponse', 'CLAIM_RESPONSE')
    # claim_insurance_coverage_ref_type
    _rename('claim_insurance_coverage_ref_type', 'Coverage', 'COVERAGE')
    # claim_item_encounter_ref_type
    _rename('claim_item_encounter_ref_type', 'Encounter', 'ENCOUNTER')
    # claim_location_ref_type
    _rename('claim_location_ref_type', 'Location', 'LOCATION')
    # claim_patient_ref_type
    _rename('claim_patient_ref_type', 'Patient', 'PATIENT')
    # claim_payee_party_ref_type
    _rename('claim_payee_party_ref_type', 'Organization', 'ORGANIZATION')
    _rename('claim_payee_party_ref_type', 'Patient', 'PATIENT')
    _rename('claim_payee_party_ref_type', 'Practitioner', 'PRACTITIONER')
    _rename('claim_payee_party_ref_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    _rename('claim_payee_party_ref_type', 'RelatedPerson', 'RELATED_PERSON')
    # claim_prescription_ref_type
    _rename('claim_prescription_ref_type', 'DeviceRequest', 'DEVICE_REQUEST')
    _rename('claim_prescription_ref_type', 'MedicationRequest', 'MEDICATION_REQUEST')
    _rename('claim_prescription_ref_type', 'VisionPrescription', 'VISION_PRESCRIPTION')
    # claim_procedure_ref_type
    _rename('claim_procedure_ref_type', 'Procedure', 'PROCEDURE')
    # claim_provider_ref_type
    _rename('claim_provider_ref_type', 'Organization', 'ORGANIZATION')
    _rename('claim_provider_ref_type', 'Practitioner', 'PRACTITIONER')
    _rename('claim_provider_ref_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    # claim_referral_ref_type
    _rename('claim_referral_ref_type', 'ServiceRequest', 'SERVICE_REQUEST')
    # claim_related_claim_ref_type
    _rename('claim_related_claim_ref_type', 'Claim', 'CLAIM')
    # claim_response_add_item_location_ref_type
    _rename('claim_response_add_item_location_ref_type', 'Location', 'LOCATION')
    # claim_response_add_item_provider_ref_type
    _rename('claim_response_add_item_provider_ref_type', 'Organization', 'ORGANIZATION')
    _rename('claim_response_add_item_provider_ref_type', 'Practitioner', 'PRACTITIONER')
    _rename('claim_response_add_item_provider_ref_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    # claim_response_comm_req_ref_type
    _rename('claim_response_comm_req_ref_type', 'CommunicationRequest', 'COMMUNICATION_REQUEST')
    # claim_response_insurance_coverage_ref_type
    _rename('claim_response_insurance_coverage_ref_type', 'Coverage', 'COVERAGE')
    # claim_response_insurance_cr_ref_type
    _rename('claim_response_insurance_cr_ref_type', 'ClaimResponse', 'CLAIM_RESPONSE')
    # claim_response_patient_ref_type
    _rename('claim_response_patient_ref_type', 'Patient', 'PATIENT')
    # claim_response_request_ref_type
    _rename('claim_response_request_ref_type', 'Claim', 'CLAIM')
    # claim_response_requestor_ref_type
    _rename('claim_response_requestor_ref_type', 'Organization', 'ORGANIZATION')
    _rename('claim_response_requestor_ref_type', 'Practitioner', 'PRACTITIONER')
    _rename('claim_response_requestor_ref_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    # condition_asserter_type
    _rename('condition_asserter_type', 'Patient', 'PATIENT')
    _rename('condition_asserter_type', 'Practitioner', 'PRACTITIONER')
    _rename('condition_asserter_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    _rename('condition_asserter_type', 'RelatedPerson', 'RELATED_PERSON')
    # condition_note_author_ref_type
    _rename('condition_note_author_ref_type', 'Organization', 'ORGANIZATION')
    _rename('condition_note_author_ref_type', 'Patient', 'PATIENT')
    _rename('condition_note_author_ref_type', 'Practitioner', 'PRACTITIONER')
    _rename('condition_note_author_ref_type', 'RelatedPerson', 'RELATED_PERSON')
    # condition_recorder_type
    _rename('condition_recorder_type', 'Patient', 'PATIENT')
    _rename('condition_recorder_type', 'Practitioner', 'PRACTITIONER')
    _rename('condition_recorder_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    _rename('condition_recorder_type', 'RelatedPerson', 'RELATED_PERSON')
    # condition_stage_assessment_type
    _rename('condition_stage_assessment_type', 'ClinicalImpression', 'CLINICAL_IMPRESSION')
    _rename('condition_stage_assessment_type', 'DiagnosticReport', 'DIAGNOSTIC_REPORT')
    _rename('condition_stage_assessment_type', 'Observation', 'OBSERVATION')
    # condition_subject_type
    _rename('condition_subject_type', 'Group', 'GROUP')
    _rename('condition_subject_type', 'Patient', 'PATIENT')
    # coverage_beneficiary_reference_type
    _rename('coverage_beneficiary_reference_type', 'Patient', 'PATIENT')
    # coverage_contract_reference_type
    _rename('coverage_contract_reference_type', 'Contract', 'CONTRACT')
    # coverage_payor_reference_type
    _rename('coverage_payor_reference_type', 'Organization', 'ORGANIZATION')
    _rename('coverage_payor_reference_type', 'Patient', 'PATIENT')
    _rename('coverage_payor_reference_type', 'RelatedPerson', 'RELATED_PERSON')
    # coverage_policy_holder_reference_type
    _rename('coverage_policy_holder_reference_type', 'Organization', 'ORGANIZATION')
    _rename('coverage_policy_holder_reference_type', 'Patient', 'PATIENT')
    _rename('coverage_policy_holder_reference_type', 'RelatedPerson', 'RELATED_PERSON')
    # coverage_subscriber_reference_type
    _rename('coverage_subscriber_reference_type', 'Patient', 'PATIENT')
    _rename('coverage_subscriber_reference_type', 'RelatedPerson', 'RELATED_PERSON')
    # document_reference_authenticator_reference_type
    _rename('document_reference_authenticator_reference_type', 'Organization', 'ORGANIZATION')
    _rename('document_reference_authenticator_reference_type', 'Practitioner', 'PRACTITIONER')
    _rename('document_reference_authenticator_reference_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    # document_reference_author_reference_type
    _rename('document_reference_author_reference_type', 'Device', 'DEVICE')
    _rename('document_reference_author_reference_type', 'Organization', 'ORGANIZATION')
    _rename('document_reference_author_reference_type', 'Patient', 'PATIENT')
    _rename('document_reference_author_reference_type', 'Practitioner', 'PRACTITIONER')
    _rename('document_reference_author_reference_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    _rename('document_reference_author_reference_type', 'RelatedPerson', 'RELATED_PERSON')
    # document_reference_context_encounter_type
    _rename('document_reference_context_encounter_type', 'Encounter', 'ENCOUNTER')
    _rename('document_reference_context_encounter_type', 'EpisodeOfCare', 'EPISODE_OF_CARE')
    # document_reference_context_source_patient_info_type
    _rename('document_reference_context_source_patient_info_type', 'Patient', 'PATIENT')
    # document_reference_relates_to_target_type
    _rename('document_reference_relates_to_target_type', 'DocumentReference', 'DOCUMENT_REFERENCE')
    # document_reference_subject_reference_type
    _rename('document_reference_subject_reference_type', 'Device', 'DEVICE')
    _rename('document_reference_subject_reference_type', 'Group', 'GROUP')
    _rename('document_reference_subject_reference_type', 'Patient', 'PATIENT')
    _rename('document_reference_subject_reference_type', 'Practitioner', 'PRACTITIONER')
    # dr_based_on_ref_type
    _rename('dr_based_on_ref_type', 'CarePlan', 'CARE_PLAN')
    _rename('dr_based_on_ref_type', 'ImmunizationRecommendation', 'IMMUNIZATION_RECOMMENDATION')
    _rename('dr_based_on_ref_type', 'MedicationRequest', 'MEDICATION_REQUEST')
    _rename('dr_based_on_ref_type', 'NutritionOrder', 'NUTRITION_ORDER')
    _rename('dr_based_on_ref_type', 'ServiceRequest', 'SERVICE_REQUEST')
    # dr_code_ref_type
    _rename('dr_code_ref_type', 'Device', 'DEVICE')
    # dr_imaging_study_ref_type
    _rename('dr_imaging_study_ref_type', 'ImagingStudy', 'IMAGING_STUDY')
    # dr_insurance_ref_type
    _rename('dr_insurance_ref_type', 'ClaimResponse', 'CLAIM_RESPONSE')
    _rename('dr_insurance_ref_type', 'Coverage', 'COVERAGE')
    # dr_interpreter_type
    _rename('dr_interpreter_type', 'CareTeam', 'CARE_TEAM')
    _rename('dr_interpreter_type', 'Organization', 'ORGANIZATION')
    _rename('dr_interpreter_type', 'Practitioner', 'PRACTITIONER')
    _rename('dr_interpreter_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    # dr_media_link_ref_type
    _rename('dr_media_link_ref_type', 'Media', 'MEDIA')
    # dr_note_author_ref_type
    _rename('dr_note_author_ref_type', 'Organization', 'ORGANIZATION')
    _rename('dr_note_author_ref_type', 'Patient', 'PATIENT')
    _rename('dr_note_author_ref_type', 'Practitioner', 'PRACTITIONER')
    _rename('dr_note_author_ref_type', 'RelatedPerson', 'RELATED_PERSON')
    # dr_performer_type
    _rename('dr_performer_type', 'CareTeam', 'CARE_TEAM')
    _rename('dr_performer_type', 'Organization', 'ORGANIZATION')
    _rename('dr_performer_type', 'Practitioner', 'PRACTITIONER')
    _rename('dr_performer_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    # dr_reason_ref_type
    _rename('dr_reason_ref_type', 'Condition', 'CONDITION')
    _rename('dr_reason_ref_type', 'DiagnosticReport', 'DIAGNOSTIC_REPORT')
    _rename('dr_reason_ref_type', 'DocumentReference', 'DOCUMENT_REFERENCE')
    _rename('dr_reason_ref_type', 'Observation', 'OBSERVATION')
    # dr_relevant_history_ref_type
    _rename('dr_relevant_history_ref_type', 'Provenance', 'PROVENANCE')
    # dr_req_performer_ref_type
    _rename('dr_req_performer_ref_type', 'CareTeam', 'CARE_TEAM')
    _rename('dr_req_performer_ref_type', 'Device', 'DEVICE')
    _rename('dr_req_performer_ref_type', 'HealthcareService', 'HEALTHCARE_SERVICE')
    _rename('dr_req_performer_ref_type', 'Organization', 'ORGANIZATION')
    _rename('dr_req_performer_ref_type', 'Patient', 'PATIENT')
    _rename('dr_req_performer_ref_type', 'Practitioner', 'PRACTITIONER')
    _rename('dr_req_performer_ref_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    _rename('dr_req_performer_ref_type', 'RelatedPerson', 'RELATED_PERSON')
    # dr_req_requester_type
    _rename('dr_req_requester_type', 'Device', 'DEVICE')
    _rename('dr_req_requester_type', 'Organization', 'ORGANIZATION')
    _rename('dr_req_requester_type', 'Practitioner', 'PRACTITIONER')
    _rename('dr_req_requester_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    # dr_req_subject_type
    _rename('dr_req_subject_type', 'Device', 'DEVICE')
    _rename('dr_req_subject_type', 'Group', 'GROUP')
    _rename('dr_req_subject_type', 'Location', 'LOCATION')
    _rename('dr_req_subject_type', 'Patient', 'PATIENT')
    # dr_result_ref_type
    _rename('dr_result_ref_type', 'Observation', 'OBSERVATION')
    # dr_specimen_ref_type
    _rename('dr_specimen_ref_type', 'Specimen', 'SPECIMEN')
    # dr_subject_type
    _rename('dr_subject_type', 'Device', 'DEVICE')
    _rename('dr_subject_type', 'Group', 'GROUP')
    _rename('dr_subject_type', 'Location', 'LOCATION')
    _rename('dr_subject_type', 'Patient', 'PATIENT')
    # encounter_account_reference_type
    _rename('encounter_account_reference_type', 'Account', 'ACCOUNT')
    # encounter_appointment_ref_reference_type
    _rename('encounter_appointment_ref_reference_type', 'Appointment', 'APPOINTMENT')
    # encounter_based_on_reference_type
    _rename('encounter_based_on_reference_type', 'CarePlan', 'CARE_PLAN')
    _rename('encounter_based_on_reference_type', 'DeviceRequest', 'DEVICE_REQUEST')
    _rename('encounter_based_on_reference_type', 'MedicationRequest', 'MEDICATION_REQUEST')
    _rename('encounter_based_on_reference_type', 'NutritionOrder', 'NUTRITION_ORDER')
    _rename('encounter_based_on_reference_type', 'RequestOrchestration', 'REQUEST_ORCHESTRATION')
    _rename('encounter_based_on_reference_type', 'ServiceRequest', 'SERVICE_REQUEST')
    _rename('encounter_based_on_reference_type', 'VisionPrescription', 'VISION_PRESCRIPTION')
    # encounter_care_team_reference_type
    _rename('encounter_care_team_reference_type', 'CareTeam', 'CARE_TEAM')
    # encounter_diagnosis_condition_type
    _rename('encounter_diagnosis_condition_type', 'Condition', 'CONDITION')
    # encounter_episode_of_care_reference_type
    _rename('encounter_episode_of_care_reference_type', 'EpisodeOfCare', 'EPISODE_OF_CARE')
    # encounter_location_reference_type
    _rename('encounter_location_reference_type', 'Location', 'LOCATION')
    # encounter_participant_reference_type
    _rename('encounter_participant_reference_type', 'Device', 'DEVICE')
    _rename('encounter_participant_reference_type', 'Group', 'GROUP')
    _rename('encounter_participant_reference_type', 'HealthcareService', 'HEALTHCARE_SERVICE')
    _rename('encounter_participant_reference_type', 'Patient', 'PATIENT')
    _rename('encounter_participant_reference_type', 'Practitioner', 'PRACTITIONER')
    _rename('encounter_participant_reference_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    _rename('encounter_participant_reference_type', 'RelatedPerson', 'RELATED_PERSON')
    # encounter_reason_value_reference_type
    _rename('encounter_reason_value_reference_type', 'Condition', 'CONDITION')
    _rename('encounter_reason_value_reference_type', 'DiagnosticReport', 'DIAGNOSTIC_REPORT')
    _rename('encounter_reason_value_reference_type', 'Observation', 'OBSERVATION')
    _rename('encounter_reason_value_reference_type', 'Procedure', 'PROCEDURE')
    # encounter_reference_type
    _rename('encounter_reference_type', 'Encounter', 'ENCOUNTER')
    # encounter_service_type_reference_type
    _rename('encounter_service_type_reference_type', 'HealthcareService', 'HEALTHCARE_SERVICE')
    # episode_of_care_account_reference_type
    _rename('episode_of_care_account_reference_type', 'Account', 'ACCOUNT')
    # episode_of_care_care_manager_reference_type
    _rename('episode_of_care_care_manager_reference_type', 'Practitioner', 'PRACTITIONER')
    _rename('episode_of_care_care_manager_reference_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    # episode_of_care_diagnosis_reference_type
    _rename('episode_of_care_diagnosis_reference_type', 'Condition', 'CONDITION')
    # episode_of_care_patient_reference_type
    _rename('episode_of_care_patient_reference_type', 'Patient', 'PATIENT')
    # episode_of_care_referral_request_reference_type
    _rename('episode_of_care_referral_request_reference_type', 'ServiceRequest', 'SERVICE_REQUEST')
    # episode_of_care_team_reference_type
    _rename('episode_of_care_team_reference_type', 'CareTeam', 'CARE_TEAM')
    # hs_coverage_area_ref_type
    _rename('hs_coverage_area_ref_type', 'Location', 'LOCATION')
    # hs_endpoint_ref_type
    _rename('hs_endpoint_ref_type', 'Endpoint', 'ENDPOINT')
    # hs_location_ref_type
    _rename('hs_location_ref_type', 'Location', 'LOCATION')
    # immunization_location_reference_type
    _rename('immunization_location_reference_type', 'Location', 'LOCATION')
    # immunization_patient_reference_type
    _rename('immunization_patient_reference_type', 'Patient', 'PATIENT')
    # immunization_performer_actor_reference_type
    _rename('immunization_performer_actor_reference_type', 'Organization', 'ORGANIZATION')
    _rename('immunization_performer_actor_reference_type', 'Practitioner', 'PRACTITIONER')
    _rename('immunization_performer_actor_reference_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    # immunization_reaction_detail_reference_type
    _rename('immunization_reaction_detail_reference_type', 'Observation', 'OBSERVATION')
    # immunization_reason_reference_type
    _rename('immunization_reason_reference_type', 'Condition', 'CONDITION')
    _rename('immunization_reason_reference_type', 'DiagnosticReport', 'DIAGNOSTIC_REPORT')
    _rename('immunization_reason_reference_type', 'Observation', 'OBSERVATION')
    # invoice_account_reference_type
    _rename('invoice_account_reference_type', 'Account', 'ACCOUNT')
    # invoice_line_item_chargeitem_ref_type
    _rename('invoice_line_item_chargeitem_ref_type', 'ChargeItem', 'CHARGE_ITEM')
    # invoice_participant_actor_reference_type
    _rename('invoice_participant_actor_reference_type', 'Device', 'DEVICE')
    _rename('invoice_participant_actor_reference_type', 'Organization', 'ORGANIZATION')
    _rename('invoice_participant_actor_reference_type', 'Patient', 'PATIENT')
    _rename('invoice_participant_actor_reference_type', 'Practitioner', 'PRACTITIONER')
    _rename('invoice_participant_actor_reference_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    _rename('invoice_participant_actor_reference_type', 'RelatedPerson', 'RELATED_PERSON')
    # invoice_recipient_reference_type
    _rename('invoice_recipient_reference_type', 'Organization', 'ORGANIZATION')
    _rename('invoice_recipient_reference_type', 'Patient', 'PATIENT')
    _rename('invoice_recipient_reference_type', 'RelatedPerson', 'RELATED_PERSON')
    # invoice_subject_reference_type
    _rename('invoice_subject_reference_type', 'Group', 'GROUP')
    _rename('invoice_subject_reference_type', 'Patient', 'PATIENT')
    # location_endpoint_reference_type
    _rename('location_endpoint_reference_type', 'Endpoint', 'ENDPOINT')
    # location_part_of_reference_type
    _rename('location_part_of_reference_type', 'Location', 'LOCATION')
    # medication_ingredient_item_reference_type
    _rename('medication_ingredient_item_reference_type', 'Medication', 'MEDICATION')
    _rename('medication_ingredient_item_reference_type', 'Substance', 'SUBSTANCE')
    # mr_based_on_ref_type
    _rename('mr_based_on_ref_type', 'CarePlan', 'CARE_PLAN')
    _rename('mr_based_on_ref_type', 'ImmunizationRecommendation', 'IMMUNIZATION_RECOMMENDATION')
    _rename('mr_based_on_ref_type', 'MedicationRequest', 'MEDICATION_REQUEST')
    _rename('mr_based_on_ref_type', 'ServiceRequest', 'SERVICE_REQUEST')
    # mr_detected_issue_ref_type
    _rename('mr_detected_issue_ref_type', 'DetectedIssue', 'DETECTED_ISSUE')
    # mr_dispense_performer_type
    _rename('mr_dispense_performer_type', 'Organization', 'ORGANIZATION')
    # mr_event_history_ref_type
    _rename('mr_event_history_ref_type', 'Provenance', 'PROVENANCE')
    # mr_insurance_ref_type
    _rename('mr_insurance_ref_type', 'ClaimResponse', 'CLAIM_RESPONSE')
    _rename('mr_insurance_ref_type', 'Coverage', 'COVERAGE')
    # mr_medication_ref_type
    _rename('mr_medication_ref_type', 'Medication', 'MEDICATION')
    # mr_note_author_ref_type
    _rename('mr_note_author_ref_type', 'Organization', 'ORGANIZATION')
    _rename('mr_note_author_ref_type', 'Patient', 'PATIENT')
    _rename('mr_note_author_ref_type', 'Practitioner', 'PRACTITIONER')
    _rename('mr_note_author_ref_type', 'RelatedPerson', 'RELATED_PERSON')
    # mr_performer_type
    _rename('mr_performer_type', 'CareTeam', 'CARE_TEAM')
    _rename('mr_performer_type', 'Device', 'DEVICE')
    _rename('mr_performer_type', 'Organization', 'ORGANIZATION')
    _rename('mr_performer_type', 'Patient', 'PATIENT')
    _rename('mr_performer_type', 'Practitioner', 'PRACTITIONER')
    _rename('mr_performer_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    _rename('mr_performer_type', 'RelatedPerson', 'RELATED_PERSON')
    # mr_prior_prescription_type
    _rename('mr_prior_prescription_type', 'MedicationRequest', 'MEDICATION_REQUEST')
    # mr_reason_ref_type
    _rename('mr_reason_ref_type', 'Condition', 'CONDITION')
    _rename('mr_reason_ref_type', 'Observation', 'OBSERVATION')
    # mr_recorder_type
    _rename('mr_recorder_type', 'Practitioner', 'PRACTITIONER')
    _rename('mr_recorder_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    # mr_reported_ref_type
    _rename('mr_reported_ref_type', 'Organization', 'ORGANIZATION')
    _rename('mr_reported_ref_type', 'Patient', 'PATIENT')
    _rename('mr_reported_ref_type', 'Practitioner', 'PRACTITIONER')
    _rename('mr_reported_ref_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    _rename('mr_reported_ref_type', 'RelatedPerson', 'RELATED_PERSON')
    # mr_requester_type
    _rename('mr_requester_type', 'Device', 'DEVICE')
    _rename('mr_requester_type', 'Organization', 'ORGANIZATION')
    _rename('mr_requester_type', 'Patient', 'PATIENT')
    _rename('mr_requester_type', 'Practitioner', 'PRACTITIONER')
    _rename('mr_requester_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    _rename('mr_requester_type', 'RelatedPerson', 'RELATED_PERSON')
    # mr_subject_type
    _rename('mr_subject_type', 'Group', 'GROUP')
    _rename('mr_subject_type', 'Patient', 'PATIENT')
    # obs_based_on_ref_type
    _rename('obs_based_on_ref_type', 'CarePlan', 'CARE_PLAN')
    _rename('obs_based_on_ref_type', 'DeviceRequest', 'DEVICE_REQUEST')
    _rename('obs_based_on_ref_type', 'ImmunizationRecommendation', 'IMMUNIZATION_RECOMMENDATION')
    _rename('obs_based_on_ref_type', 'MedicationRequest', 'MEDICATION_REQUEST')
    _rename('obs_based_on_ref_type', 'NutritionOrder', 'NUTRITION_ORDER')
    _rename('obs_based_on_ref_type', 'ServiceRequest', 'SERVICE_REQUEST')
    # obs_derived_from_ref_type
    _rename('obs_derived_from_ref_type', 'DocumentReference', 'DOCUMENT_REFERENCE')
    _rename('obs_derived_from_ref_type', 'ImagingStudy', 'IMAGING_STUDY')
    _rename('obs_derived_from_ref_type', 'Media', 'MEDIA')
    _rename('obs_derived_from_ref_type', 'MolecularSequence', 'MOLECULAR_SEQUENCE')
    _rename('obs_derived_from_ref_type', 'Observation', 'OBSERVATION')
    _rename('obs_derived_from_ref_type', 'QuestionnaireResponse', 'QUESTIONNAIRE_RESPONSE')
    # obs_device_ref_type
    _rename('obs_device_ref_type', 'Device', 'DEVICE')
    _rename('obs_device_ref_type', 'DeviceMetric', 'DEVICE_METRIC')
    # obs_encounter_ref_type
    _rename('obs_encounter_ref_type', 'Encounter', 'ENCOUNTER')
    # obs_has_member_ref_type
    _rename('obs_has_member_ref_type', 'MolecularSequence', 'MOLECULAR_SEQUENCE')
    _rename('obs_has_member_ref_type', 'Observation', 'OBSERVATION')
    _rename('obs_has_member_ref_type', 'QuestionnaireResponse', 'QUESTIONNAIRE_RESPONSE')
    # obs_part_of_ref_type
    _rename('obs_part_of_ref_type', 'ImagingStudy', 'IMAGING_STUDY')
    _rename('obs_part_of_ref_type', 'Immunization', 'IMMUNIZATION')
    _rename('obs_part_of_ref_type', 'MedicationAdministration', 'MEDICATION_ADMINISTRATION')
    _rename('obs_part_of_ref_type', 'MedicationDispense', 'MEDICATION_DISPENSE')
    _rename('obs_part_of_ref_type', 'MedicationStatement', 'MEDICATION_STATEMENT')
    _rename('obs_part_of_ref_type', 'Procedure', 'PROCEDURE')
    # obs_performer_ref_type
    _rename('obs_performer_ref_type', 'CareTeam', 'CARE_TEAM')
    _rename('obs_performer_ref_type', 'Organization', 'ORGANIZATION')
    _rename('obs_performer_ref_type', 'Patient', 'PATIENT')
    _rename('obs_performer_ref_type', 'Practitioner', 'PRACTITIONER')
    _rename('obs_performer_ref_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    _rename('obs_performer_ref_type', 'RelatedPerson', 'RELATED_PERSON')
    # obs_specimen_ref_type
    _rename('obs_specimen_ref_type', 'Specimen', 'SPECIMEN')
    # obs_subject_ref_type
    _rename('obs_subject_ref_type', 'Device', 'DEVICE')
    _rename('obs_subject_ref_type', 'Group', 'GROUP')
    _rename('obs_subject_ref_type', 'Location', 'LOCATION')
    _rename('obs_subject_ref_type', 'Patient', 'PATIENT')
    # organization_endpoint_ref_type
    _rename('organization_endpoint_ref_type', 'Endpoint', 'ENDPOINT')
    # organization_reference_type
    _rename('organization_reference_type', 'Organization', 'ORGANIZATION')
    # patient_gp_type
    _rename('patient_gp_type', 'Organization', 'ORGANIZATION')
    _rename('patient_gp_type', 'Practitioner', 'PRACTITIONER')
    _rename('patient_gp_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    # patient_link_other_type
    _rename('patient_link_other_type', 'Patient', 'PATIENT')
    _rename('patient_link_other_type', 'RelatedPerson', 'RELATED_PERSON')
    # pr_endpoint_ref_type
    _rename('pr_endpoint_ref_type', 'Endpoint', 'ENDPOINT')
    # pr_healthcare_service_ref_type
    _rename('pr_healthcare_service_ref_type', 'HealthcareService', 'HEALTHCARE_SERVICE')
    # pr_location_ref_type
    _rename('pr_location_ref_type', 'Location', 'LOCATION')
    # procedure_asserter_type
    _rename('procedure_asserter_type', 'Patient', 'PATIENT')
    _rename('procedure_asserter_type', 'Practitioner', 'PRACTITIONER')
    _rename('procedure_asserter_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    _rename('procedure_asserter_type', 'RelatedPerson', 'RELATED_PERSON')
    # procedure_based_on_ref_type
    _rename('procedure_based_on_ref_type', 'CarePlan', 'CARE_PLAN')
    _rename('procedure_based_on_ref_type', 'ServiceRequest', 'SERVICE_REQUEST')
    # procedure_complication_detail_ref_type
    _rename('procedure_complication_detail_ref_type', 'Condition', 'CONDITION')
    # procedure_focal_device_ref_type
    _rename('procedure_focal_device_ref_type', 'Device', 'DEVICE')
    # procedure_location_ref_type
    _rename('procedure_location_ref_type', 'Location', 'LOCATION')
    # procedure_note_author_ref_type
    _rename('procedure_note_author_ref_type', 'Organization', 'ORGANIZATION')
    _rename('procedure_note_author_ref_type', 'Patient', 'PATIENT')
    _rename('procedure_note_author_ref_type', 'Practitioner', 'PRACTITIONER')
    _rename('procedure_note_author_ref_type', 'RelatedPerson', 'RELATED_PERSON')
    # procedure_on_behalf_of_type
    _rename('procedure_on_behalf_of_type', 'Organization', 'ORGANIZATION')
    # procedure_part_of_ref_type
    _rename('procedure_part_of_ref_type', 'MedicationAdministration', 'MEDICATION_ADMINISTRATION')
    _rename('procedure_part_of_ref_type', 'Observation', 'OBSERVATION')
    _rename('procedure_part_of_ref_type', 'Procedure', 'PROCEDURE')
    # procedure_performer_actor_type
    _rename('procedure_performer_actor_type', 'Device', 'DEVICE')
    _rename('procedure_performer_actor_type', 'Organization', 'ORGANIZATION')
    _rename('procedure_performer_actor_type', 'Patient', 'PATIENT')
    _rename('procedure_performer_actor_type', 'Practitioner', 'PRACTITIONER')
    _rename('procedure_performer_actor_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    _rename('procedure_performer_actor_type', 'RelatedPerson', 'RELATED_PERSON')
    # procedure_reason_ref_type
    _rename('procedure_reason_ref_type', 'Condition', 'CONDITION')
    _rename('procedure_reason_ref_type', 'DiagnosticReport', 'DIAGNOSTIC_REPORT')
    _rename('procedure_reason_ref_type', 'DocumentReference', 'DOCUMENT_REFERENCE')
    _rename('procedure_reason_ref_type', 'Observation', 'OBSERVATION')
    _rename('procedure_reason_ref_type', 'Procedure', 'PROCEDURE')
    # procedure_recorder_type
    _rename('procedure_recorder_type', 'Patient', 'PATIENT')
    _rename('procedure_recorder_type', 'Practitioner', 'PRACTITIONER')
    _rename('procedure_recorder_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    _rename('procedure_recorder_type', 'RelatedPerson', 'RELATED_PERSON')
    # procedure_report_ref_type
    _rename('procedure_report_ref_type', 'Composition', 'COMPOSITION')
    _rename('procedure_report_ref_type', 'DiagnosticReport', 'DIAGNOSTIC_REPORT')
    _rename('procedure_report_ref_type', 'DocumentReference', 'DOCUMENT_REFERENCE')
    # procedure_subject_type
    _rename('procedure_subject_type', 'Group', 'GROUP')
    _rename('procedure_subject_type', 'Patient', 'PATIENT')
    # procedure_used_ref_type
    _rename('procedure_used_ref_type', 'Device', 'DEVICE')
    _rename('procedure_used_ref_type', 'Medication', 'MEDICATION')
    _rename('procedure_used_ref_type', 'Substance', 'SUBSTANCE')
    # provenance_agent_who_reference_type
    _rename('provenance_agent_who_reference_type', 'Device', 'DEVICE')
    _rename('provenance_agent_who_reference_type', 'Organization', 'ORGANIZATION')
    _rename('provenance_agent_who_reference_type', 'Patient', 'PATIENT')
    _rename('provenance_agent_who_reference_type', 'Practitioner', 'PRACTITIONER')
    _rename('provenance_agent_who_reference_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    _rename('provenance_agent_who_reference_type', 'RelatedPerson', 'RELATED_PERSON')
    # provenance_location_reference_type
    _rename('provenance_location_reference_type', 'Location', 'LOCATION')
    # qr_based_on_reference_type
    _rename('qr_based_on_reference_type', 'CarePlan', 'CARE_PLAN')
    _rename('qr_based_on_reference_type', 'ServiceRequest', 'SERVICE_REQUEST')
    # qr_part_of_reference_type
    _rename('qr_part_of_reference_type', 'Observation', 'OBSERVATION')
    _rename('qr_part_of_reference_type', 'Procedure', 'PROCEDURE')
    # related_person_patient_reference_type
    _rename('related_person_patient_reference_type', 'Patient', 'PATIENT')
    # schedule_actor_reference_type
    _rename('schedule_actor_reference_type', 'Device', 'DEVICE')
    _rename('schedule_actor_reference_type', 'HealthcareService', 'HEALTHCARE_SERVICE')
    _rename('schedule_actor_reference_type', 'Location', 'LOCATION')
    _rename('schedule_actor_reference_type', 'Patient', 'PATIENT')
    _rename('schedule_actor_reference_type', 'Practitioner', 'PRACTITIONER')
    _rename('schedule_actor_reference_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    _rename('schedule_actor_reference_type', 'RelatedPerson', 'RELATED_PERSON')
    # slot_schedule_reference_type
    _rename('slot_schedule_reference_type', 'Schedule', 'SCHEDULE')
    # source_reference_type
    _rename('source_reference_type', 'Patient', 'PATIENT')
    _rename('source_reference_type', 'Practitioner', 'PRACTITIONER')
    _rename('source_reference_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    _rename('source_reference_type', 'RelatedPerson', 'RELATED_PERSON')
    # specimen_collector_reference_type
    _rename('specimen_collector_reference_type', 'Practitioner', 'PRACTITIONER')
    _rename('specimen_collector_reference_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    # specimen_container_additive_reference_type
    _rename('specimen_container_additive_reference_type', 'Substance', 'SUBSTANCE')
    # specimen_parent_reference_type
    _rename('specimen_parent_reference_type', 'Specimen', 'SPECIMEN')
    # specimen_processing_additive_reference_type
    _rename('specimen_processing_additive_reference_type', 'Substance', 'SUBSTANCE')
    # specimen_request_reference_type
    _rename('specimen_request_reference_type', 'ServiceRequest', 'SERVICE_REQUEST')
    # specimen_subject_reference_type
    _rename('specimen_subject_reference_type', 'Device', 'DEVICE')
    _rename('specimen_subject_reference_type', 'Group', 'GROUP')
    _rename('specimen_subject_reference_type', 'Location', 'LOCATION')
    _rename('specimen_subject_reference_type', 'Patient', 'PATIENT')
    _rename('specimen_subject_reference_type', 'Substance', 'SUBSTANCE')
    # sr_based_on_ref_type
    _rename('sr_based_on_ref_type', 'CarePlan', 'CARE_PLAN')
    _rename('sr_based_on_ref_type', 'MedicationRequest', 'MEDICATION_REQUEST')
    _rename('sr_based_on_ref_type', 'ServiceRequest', 'SERVICE_REQUEST')
    # sr_insurance_ref_type
    _rename('sr_insurance_ref_type', 'ClaimResponse', 'CLAIM_RESPONSE')
    _rename('sr_insurance_ref_type', 'Coverage', 'COVERAGE')
    # sr_location_ref_type
    _rename('sr_location_ref_type', 'Location', 'LOCATION')
    # sr_note_author_ref_type
    _rename('sr_note_author_ref_type', 'Organization', 'ORGANIZATION')
    _rename('sr_note_author_ref_type', 'Patient', 'PATIENT')
    _rename('sr_note_author_ref_type', 'Practitioner', 'PRACTITIONER')
    _rename('sr_note_author_ref_type', 'RelatedPerson', 'RELATED_PERSON')
    # sr_performer_ref_type
    _rename('sr_performer_ref_type', 'CareTeam', 'CARE_TEAM')
    _rename('sr_performer_ref_type', 'Device', 'DEVICE')
    _rename('sr_performer_ref_type', 'HealthcareService', 'HEALTHCARE_SERVICE')
    _rename('sr_performer_ref_type', 'Organization', 'ORGANIZATION')
    _rename('sr_performer_ref_type', 'Patient', 'PATIENT')
    _rename('sr_performer_ref_type', 'Practitioner', 'PRACTITIONER')
    _rename('sr_performer_ref_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    _rename('sr_performer_ref_type', 'RelatedPerson', 'RELATED_PERSON')
    # sr_reason_ref_type
    _rename('sr_reason_ref_type', 'Condition', 'CONDITION')
    _rename('sr_reason_ref_type', 'DiagnosticReport', 'DIAGNOSTIC_REPORT')
    _rename('sr_reason_ref_type', 'DocumentReference', 'DOCUMENT_REFERENCE')
    _rename('sr_reason_ref_type', 'Observation', 'OBSERVATION')
    # sr_relevant_history_ref_type
    _rename('sr_relevant_history_ref_type', 'Provenance', 'PROVENANCE')
    # sr_replaces_ref_type
    _rename('sr_replaces_ref_type', 'ServiceRequest', 'SERVICE_REQUEST')
    # sr_requester_type
    _rename('sr_requester_type', 'Device', 'DEVICE')
    _rename('sr_requester_type', 'Organization', 'ORGANIZATION')
    _rename('sr_requester_type', 'Patient', 'PATIENT')
    _rename('sr_requester_type', 'Practitioner', 'PRACTITIONER')
    _rename('sr_requester_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    _rename('sr_requester_type', 'RelatedPerson', 'RELATED_PERSON')
    # sr_specimen_ref_type
    _rename('sr_specimen_ref_type', 'Specimen', 'SPECIMEN')
    # sr_subject_type
    _rename('sr_subject_type', 'Device', 'DEVICE')
    _rename('sr_subject_type', 'Group', 'GROUP')
    _rename('sr_subject_type', 'Location', 'LOCATION')
    _rename('sr_subject_type', 'Patient', 'PATIENT')
    # subject_reference_type
    _rename('subject_reference_type', 'Group', 'GROUP')
    _rename('subject_reference_type', 'Patient', 'PATIENT')
    # task_insurance_reference_type
    _rename('task_insurance_reference_type', 'ClaimResponse', 'CLAIM_RESPONSE')
    _rename('task_insurance_reference_type', 'Coverage', 'COVERAGE')
    # task_location_reference_type
    _rename('task_location_reference_type', 'Location', 'LOCATION')
    # task_owner_reference_type
    _rename('task_owner_reference_type', 'CareTeam', 'CARE_TEAM')
    _rename('task_owner_reference_type', 'Device', 'DEVICE')
    _rename('task_owner_reference_type', 'HealthcareService', 'HEALTHCARE_SERVICE')
    _rename('task_owner_reference_type', 'Organization', 'ORGANIZATION')
    _rename('task_owner_reference_type', 'Patient', 'PATIENT')
    _rename('task_owner_reference_type', 'Practitioner', 'PRACTITIONER')
    _rename('task_owner_reference_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    _rename('task_owner_reference_type', 'RelatedPerson', 'RELATED_PERSON')
    # task_part_of_reference_type
    _rename('task_part_of_reference_type', 'Task', 'TASK')
    # task_relevant_history_reference_type
    _rename('task_relevant_history_reference_type', 'Provenance', 'PROVENANCE')
    # task_requester_reference_type
    _rename('task_requester_reference_type', 'Device', 'DEVICE')
    _rename('task_requester_reference_type', 'Organization', 'ORGANIZATION')
    _rename('task_requester_reference_type', 'Patient', 'PATIENT')
    _rename('task_requester_reference_type', 'Practitioner', 'PRACTITIONER')
    _rename('task_requester_reference_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    _rename('task_requester_reference_type', 'RelatedPerson', 'RELATED_PERSON')
    # task_restriction_recipient_reference_type
    _rename('task_restriction_recipient_reference_type', 'Group', 'GROUP')
    _rename('task_restriction_recipient_reference_type', 'Organization', 'ORGANIZATION')
    _rename('task_restriction_recipient_reference_type', 'Patient', 'PATIENT')
    _rename('task_restriction_recipient_reference_type', 'Practitioner', 'PRACTITIONER')
    _rename('task_restriction_recipient_reference_type', 'PractitionerRole', 'PRACTITIONER_ROLE')
    _rename('task_restriction_recipient_reference_type', 'RelatedPerson', 'RELATED_PERSON')


def downgrade() -> None:
    # task_restriction_recipient_reference_type
    _rename('task_restriction_recipient_reference_type', 'RELATED_PERSON', 'RelatedPerson')
    _rename('task_restriction_recipient_reference_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('task_restriction_recipient_reference_type', 'PRACTITIONER', 'Practitioner')
    _rename('task_restriction_recipient_reference_type', 'PATIENT', 'Patient')
    _rename('task_restriction_recipient_reference_type', 'ORGANIZATION', 'Organization')
    _rename('task_restriction_recipient_reference_type', 'GROUP', 'Group')
    # task_requester_reference_type
    _rename('task_requester_reference_type', 'RELATED_PERSON', 'RelatedPerson')
    _rename('task_requester_reference_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('task_requester_reference_type', 'PRACTITIONER', 'Practitioner')
    _rename('task_requester_reference_type', 'PATIENT', 'Patient')
    _rename('task_requester_reference_type', 'ORGANIZATION', 'Organization')
    _rename('task_requester_reference_type', 'DEVICE', 'Device')
    # task_relevant_history_reference_type
    _rename('task_relevant_history_reference_type', 'PROVENANCE', 'Provenance')
    # task_part_of_reference_type
    _rename('task_part_of_reference_type', 'TASK', 'Task')
    # task_owner_reference_type
    _rename('task_owner_reference_type', 'RELATED_PERSON', 'RelatedPerson')
    _rename('task_owner_reference_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('task_owner_reference_type', 'PRACTITIONER', 'Practitioner')
    _rename('task_owner_reference_type', 'PATIENT', 'Patient')
    _rename('task_owner_reference_type', 'ORGANIZATION', 'Organization')
    _rename('task_owner_reference_type', 'HEALTHCARE_SERVICE', 'HealthcareService')
    _rename('task_owner_reference_type', 'DEVICE', 'Device')
    _rename('task_owner_reference_type', 'CARE_TEAM', 'CareTeam')
    # task_location_reference_type
    _rename('task_location_reference_type', 'LOCATION', 'Location')
    # task_insurance_reference_type
    _rename('task_insurance_reference_type', 'COVERAGE', 'Coverage')
    _rename('task_insurance_reference_type', 'CLAIM_RESPONSE', 'ClaimResponse')
    # subject_reference_type
    _rename('subject_reference_type', 'PATIENT', 'Patient')
    _rename('subject_reference_type', 'GROUP', 'Group')
    # sr_subject_type
    _rename('sr_subject_type', 'PATIENT', 'Patient')
    _rename('sr_subject_type', 'LOCATION', 'Location')
    _rename('sr_subject_type', 'GROUP', 'Group')
    _rename('sr_subject_type', 'DEVICE', 'Device')
    # sr_specimen_ref_type
    _rename('sr_specimen_ref_type', 'SPECIMEN', 'Specimen')
    # sr_requester_type
    _rename('sr_requester_type', 'RELATED_PERSON', 'RelatedPerson')
    _rename('sr_requester_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('sr_requester_type', 'PRACTITIONER', 'Practitioner')
    _rename('sr_requester_type', 'PATIENT', 'Patient')
    _rename('sr_requester_type', 'ORGANIZATION', 'Organization')
    _rename('sr_requester_type', 'DEVICE', 'Device')
    # sr_replaces_ref_type
    _rename('sr_replaces_ref_type', 'SERVICE_REQUEST', 'ServiceRequest')
    # sr_relevant_history_ref_type
    _rename('sr_relevant_history_ref_type', 'PROVENANCE', 'Provenance')
    # sr_reason_ref_type
    _rename('sr_reason_ref_type', 'OBSERVATION', 'Observation')
    _rename('sr_reason_ref_type', 'DOCUMENT_REFERENCE', 'DocumentReference')
    _rename('sr_reason_ref_type', 'DIAGNOSTIC_REPORT', 'DiagnosticReport')
    _rename('sr_reason_ref_type', 'CONDITION', 'Condition')
    # sr_performer_ref_type
    _rename('sr_performer_ref_type', 'RELATED_PERSON', 'RelatedPerson')
    _rename('sr_performer_ref_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('sr_performer_ref_type', 'PRACTITIONER', 'Practitioner')
    _rename('sr_performer_ref_type', 'PATIENT', 'Patient')
    _rename('sr_performer_ref_type', 'ORGANIZATION', 'Organization')
    _rename('sr_performer_ref_type', 'HEALTHCARE_SERVICE', 'HealthcareService')
    _rename('sr_performer_ref_type', 'DEVICE', 'Device')
    _rename('sr_performer_ref_type', 'CARE_TEAM', 'CareTeam')
    # sr_note_author_ref_type
    _rename('sr_note_author_ref_type', 'RELATED_PERSON', 'RelatedPerson')
    _rename('sr_note_author_ref_type', 'PRACTITIONER', 'Practitioner')
    _rename('sr_note_author_ref_type', 'PATIENT', 'Patient')
    _rename('sr_note_author_ref_type', 'ORGANIZATION', 'Organization')
    # sr_location_ref_type
    _rename('sr_location_ref_type', 'LOCATION', 'Location')
    # sr_insurance_ref_type
    _rename('sr_insurance_ref_type', 'COVERAGE', 'Coverage')
    _rename('sr_insurance_ref_type', 'CLAIM_RESPONSE', 'ClaimResponse')
    # sr_based_on_ref_type
    _rename('sr_based_on_ref_type', 'SERVICE_REQUEST', 'ServiceRequest')
    _rename('sr_based_on_ref_type', 'MEDICATION_REQUEST', 'MedicationRequest')
    _rename('sr_based_on_ref_type', 'CARE_PLAN', 'CarePlan')
    # specimen_subject_reference_type
    _rename('specimen_subject_reference_type', 'SUBSTANCE', 'Substance')
    _rename('specimen_subject_reference_type', 'PATIENT', 'Patient')
    _rename('specimen_subject_reference_type', 'LOCATION', 'Location')
    _rename('specimen_subject_reference_type', 'GROUP', 'Group')
    _rename('specimen_subject_reference_type', 'DEVICE', 'Device')
    # specimen_request_reference_type
    _rename('specimen_request_reference_type', 'SERVICE_REQUEST', 'ServiceRequest')
    # specimen_processing_additive_reference_type
    _rename('specimen_processing_additive_reference_type', 'SUBSTANCE', 'Substance')
    # specimen_parent_reference_type
    _rename('specimen_parent_reference_type', 'SPECIMEN', 'Specimen')
    # specimen_container_additive_reference_type
    _rename('specimen_container_additive_reference_type', 'SUBSTANCE', 'Substance')
    # specimen_collector_reference_type
    _rename('specimen_collector_reference_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('specimen_collector_reference_type', 'PRACTITIONER', 'Practitioner')
    # source_reference_type
    _rename('source_reference_type', 'RELATED_PERSON', 'RelatedPerson')
    _rename('source_reference_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('source_reference_type', 'PRACTITIONER', 'Practitioner')
    _rename('source_reference_type', 'PATIENT', 'Patient')
    # slot_schedule_reference_type
    _rename('slot_schedule_reference_type', 'SCHEDULE', 'Schedule')
    # schedule_actor_reference_type
    _rename('schedule_actor_reference_type', 'RELATED_PERSON', 'RelatedPerson')
    _rename('schedule_actor_reference_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('schedule_actor_reference_type', 'PRACTITIONER', 'Practitioner')
    _rename('schedule_actor_reference_type', 'PATIENT', 'Patient')
    _rename('schedule_actor_reference_type', 'LOCATION', 'Location')
    _rename('schedule_actor_reference_type', 'HEALTHCARE_SERVICE', 'HealthcareService')
    _rename('schedule_actor_reference_type', 'DEVICE', 'Device')
    # related_person_patient_reference_type
    _rename('related_person_patient_reference_type', 'PATIENT', 'Patient')
    # qr_part_of_reference_type
    _rename('qr_part_of_reference_type', 'PROCEDURE', 'Procedure')
    _rename('qr_part_of_reference_type', 'OBSERVATION', 'Observation')
    # qr_based_on_reference_type
    _rename('qr_based_on_reference_type', 'SERVICE_REQUEST', 'ServiceRequest')
    _rename('qr_based_on_reference_type', 'CARE_PLAN', 'CarePlan')
    # provenance_location_reference_type
    _rename('provenance_location_reference_type', 'LOCATION', 'Location')
    # provenance_agent_who_reference_type
    _rename('provenance_agent_who_reference_type', 'RELATED_PERSON', 'RelatedPerson')
    _rename('provenance_agent_who_reference_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('provenance_agent_who_reference_type', 'PRACTITIONER', 'Practitioner')
    _rename('provenance_agent_who_reference_type', 'PATIENT', 'Patient')
    _rename('provenance_agent_who_reference_type', 'ORGANIZATION', 'Organization')
    _rename('provenance_agent_who_reference_type', 'DEVICE', 'Device')
    # procedure_used_ref_type
    _rename('procedure_used_ref_type', 'SUBSTANCE', 'Substance')
    _rename('procedure_used_ref_type', 'MEDICATION', 'Medication')
    _rename('procedure_used_ref_type', 'DEVICE', 'Device')
    # procedure_subject_type
    _rename('procedure_subject_type', 'PATIENT', 'Patient')
    _rename('procedure_subject_type', 'GROUP', 'Group')
    # procedure_report_ref_type
    _rename('procedure_report_ref_type', 'DOCUMENT_REFERENCE', 'DocumentReference')
    _rename('procedure_report_ref_type', 'DIAGNOSTIC_REPORT', 'DiagnosticReport')
    _rename('procedure_report_ref_type', 'COMPOSITION', 'Composition')
    # procedure_recorder_type
    _rename('procedure_recorder_type', 'RELATED_PERSON', 'RelatedPerson')
    _rename('procedure_recorder_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('procedure_recorder_type', 'PRACTITIONER', 'Practitioner')
    _rename('procedure_recorder_type', 'PATIENT', 'Patient')
    # procedure_reason_ref_type
    _rename('procedure_reason_ref_type', 'PROCEDURE', 'Procedure')
    _rename('procedure_reason_ref_type', 'OBSERVATION', 'Observation')
    _rename('procedure_reason_ref_type', 'DOCUMENT_REFERENCE', 'DocumentReference')
    _rename('procedure_reason_ref_type', 'DIAGNOSTIC_REPORT', 'DiagnosticReport')
    _rename('procedure_reason_ref_type', 'CONDITION', 'Condition')
    # procedure_performer_actor_type
    _rename('procedure_performer_actor_type', 'RELATED_PERSON', 'RelatedPerson')
    _rename('procedure_performer_actor_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('procedure_performer_actor_type', 'PRACTITIONER', 'Practitioner')
    _rename('procedure_performer_actor_type', 'PATIENT', 'Patient')
    _rename('procedure_performer_actor_type', 'ORGANIZATION', 'Organization')
    _rename('procedure_performer_actor_type', 'DEVICE', 'Device')
    # procedure_part_of_ref_type
    _rename('procedure_part_of_ref_type', 'PROCEDURE', 'Procedure')
    _rename('procedure_part_of_ref_type', 'OBSERVATION', 'Observation')
    _rename('procedure_part_of_ref_type', 'MEDICATION_ADMINISTRATION', 'MedicationAdministration')
    # procedure_on_behalf_of_type
    _rename('procedure_on_behalf_of_type', 'ORGANIZATION', 'Organization')
    # procedure_note_author_ref_type
    _rename('procedure_note_author_ref_type', 'RELATED_PERSON', 'RelatedPerson')
    _rename('procedure_note_author_ref_type', 'PRACTITIONER', 'Practitioner')
    _rename('procedure_note_author_ref_type', 'PATIENT', 'Patient')
    _rename('procedure_note_author_ref_type', 'ORGANIZATION', 'Organization')
    # procedure_location_ref_type
    _rename('procedure_location_ref_type', 'LOCATION', 'Location')
    # procedure_focal_device_ref_type
    _rename('procedure_focal_device_ref_type', 'DEVICE', 'Device')
    # procedure_complication_detail_ref_type
    _rename('procedure_complication_detail_ref_type', 'CONDITION', 'Condition')
    # procedure_based_on_ref_type
    _rename('procedure_based_on_ref_type', 'SERVICE_REQUEST', 'ServiceRequest')
    _rename('procedure_based_on_ref_type', 'CARE_PLAN', 'CarePlan')
    # procedure_asserter_type
    _rename('procedure_asserter_type', 'RELATED_PERSON', 'RelatedPerson')
    _rename('procedure_asserter_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('procedure_asserter_type', 'PRACTITIONER', 'Practitioner')
    _rename('procedure_asserter_type', 'PATIENT', 'Patient')
    # pr_location_ref_type
    _rename('pr_location_ref_type', 'LOCATION', 'Location')
    # pr_healthcare_service_ref_type
    _rename('pr_healthcare_service_ref_type', 'HEALTHCARE_SERVICE', 'HealthcareService')
    # pr_endpoint_ref_type
    _rename('pr_endpoint_ref_type', 'ENDPOINT', 'Endpoint')
    # patient_link_other_type
    _rename('patient_link_other_type', 'RELATED_PERSON', 'RelatedPerson')
    _rename('patient_link_other_type', 'PATIENT', 'Patient')
    # patient_gp_type
    _rename('patient_gp_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('patient_gp_type', 'PRACTITIONER', 'Practitioner')
    _rename('patient_gp_type', 'ORGANIZATION', 'Organization')
    # organization_reference_type
    _rename('organization_reference_type', 'ORGANIZATION', 'Organization')
    # organization_endpoint_ref_type
    _rename('organization_endpoint_ref_type', 'ENDPOINT', 'Endpoint')
    # obs_subject_ref_type
    _rename('obs_subject_ref_type', 'PATIENT', 'Patient')
    _rename('obs_subject_ref_type', 'LOCATION', 'Location')
    _rename('obs_subject_ref_type', 'GROUP', 'Group')
    _rename('obs_subject_ref_type', 'DEVICE', 'Device')
    # obs_specimen_ref_type
    _rename('obs_specimen_ref_type', 'SPECIMEN', 'Specimen')
    # obs_performer_ref_type
    _rename('obs_performer_ref_type', 'RELATED_PERSON', 'RelatedPerson')
    _rename('obs_performer_ref_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('obs_performer_ref_type', 'PRACTITIONER', 'Practitioner')
    _rename('obs_performer_ref_type', 'PATIENT', 'Patient')
    _rename('obs_performer_ref_type', 'ORGANIZATION', 'Organization')
    _rename('obs_performer_ref_type', 'CARE_TEAM', 'CareTeam')
    # obs_part_of_ref_type
    _rename('obs_part_of_ref_type', 'PROCEDURE', 'Procedure')
    _rename('obs_part_of_ref_type', 'MEDICATION_STATEMENT', 'MedicationStatement')
    _rename('obs_part_of_ref_type', 'MEDICATION_DISPENSE', 'MedicationDispense')
    _rename('obs_part_of_ref_type', 'MEDICATION_ADMINISTRATION', 'MedicationAdministration')
    _rename('obs_part_of_ref_type', 'IMMUNIZATION', 'Immunization')
    _rename('obs_part_of_ref_type', 'IMAGING_STUDY', 'ImagingStudy')
    # obs_has_member_ref_type
    _rename('obs_has_member_ref_type', 'QUESTIONNAIRE_RESPONSE', 'QuestionnaireResponse')
    _rename('obs_has_member_ref_type', 'OBSERVATION', 'Observation')
    _rename('obs_has_member_ref_type', 'MOLECULAR_SEQUENCE', 'MolecularSequence')
    # obs_encounter_ref_type
    _rename('obs_encounter_ref_type', 'ENCOUNTER', 'Encounter')
    # obs_device_ref_type
    _rename('obs_device_ref_type', 'DEVICE_METRIC', 'DeviceMetric')
    _rename('obs_device_ref_type', 'DEVICE', 'Device')
    # obs_derived_from_ref_type
    _rename('obs_derived_from_ref_type', 'QUESTIONNAIRE_RESPONSE', 'QuestionnaireResponse')
    _rename('obs_derived_from_ref_type', 'OBSERVATION', 'Observation')
    _rename('obs_derived_from_ref_type', 'MOLECULAR_SEQUENCE', 'MolecularSequence')
    _rename('obs_derived_from_ref_type', 'MEDIA', 'Media')
    _rename('obs_derived_from_ref_type', 'IMAGING_STUDY', 'ImagingStudy')
    _rename('obs_derived_from_ref_type', 'DOCUMENT_REFERENCE', 'DocumentReference')
    # obs_based_on_ref_type
    _rename('obs_based_on_ref_type', 'SERVICE_REQUEST', 'ServiceRequest')
    _rename('obs_based_on_ref_type', 'NUTRITION_ORDER', 'NutritionOrder')
    _rename('obs_based_on_ref_type', 'MEDICATION_REQUEST', 'MedicationRequest')
    _rename('obs_based_on_ref_type', 'IMMUNIZATION_RECOMMENDATION', 'ImmunizationRecommendation')
    _rename('obs_based_on_ref_type', 'DEVICE_REQUEST', 'DeviceRequest')
    _rename('obs_based_on_ref_type', 'CARE_PLAN', 'CarePlan')
    # mr_subject_type
    _rename('mr_subject_type', 'PATIENT', 'Patient')
    _rename('mr_subject_type', 'GROUP', 'Group')
    # mr_requester_type
    _rename('mr_requester_type', 'RELATED_PERSON', 'RelatedPerson')
    _rename('mr_requester_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('mr_requester_type', 'PRACTITIONER', 'Practitioner')
    _rename('mr_requester_type', 'PATIENT', 'Patient')
    _rename('mr_requester_type', 'ORGANIZATION', 'Organization')
    _rename('mr_requester_type', 'DEVICE', 'Device')
    # mr_reported_ref_type
    _rename('mr_reported_ref_type', 'RELATED_PERSON', 'RelatedPerson')
    _rename('mr_reported_ref_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('mr_reported_ref_type', 'PRACTITIONER', 'Practitioner')
    _rename('mr_reported_ref_type', 'PATIENT', 'Patient')
    _rename('mr_reported_ref_type', 'ORGANIZATION', 'Organization')
    # mr_recorder_type
    _rename('mr_recorder_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('mr_recorder_type', 'PRACTITIONER', 'Practitioner')
    # mr_reason_ref_type
    _rename('mr_reason_ref_type', 'OBSERVATION', 'Observation')
    _rename('mr_reason_ref_type', 'CONDITION', 'Condition')
    # mr_prior_prescription_type
    _rename('mr_prior_prescription_type', 'MEDICATION_REQUEST', 'MedicationRequest')
    # mr_performer_type
    _rename('mr_performer_type', 'RELATED_PERSON', 'RelatedPerson')
    _rename('mr_performer_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('mr_performer_type', 'PRACTITIONER', 'Practitioner')
    _rename('mr_performer_type', 'PATIENT', 'Patient')
    _rename('mr_performer_type', 'ORGANIZATION', 'Organization')
    _rename('mr_performer_type', 'DEVICE', 'Device')
    _rename('mr_performer_type', 'CARE_TEAM', 'CareTeam')
    # mr_note_author_ref_type
    _rename('mr_note_author_ref_type', 'RELATED_PERSON', 'RelatedPerson')
    _rename('mr_note_author_ref_type', 'PRACTITIONER', 'Practitioner')
    _rename('mr_note_author_ref_type', 'PATIENT', 'Patient')
    _rename('mr_note_author_ref_type', 'ORGANIZATION', 'Organization')
    # mr_medication_ref_type
    _rename('mr_medication_ref_type', 'MEDICATION', 'Medication')
    # mr_insurance_ref_type
    _rename('mr_insurance_ref_type', 'COVERAGE', 'Coverage')
    _rename('mr_insurance_ref_type', 'CLAIM_RESPONSE', 'ClaimResponse')
    # mr_event_history_ref_type
    _rename('mr_event_history_ref_type', 'PROVENANCE', 'Provenance')
    # mr_dispense_performer_type
    _rename('mr_dispense_performer_type', 'ORGANIZATION', 'Organization')
    # mr_detected_issue_ref_type
    _rename('mr_detected_issue_ref_type', 'DETECTED_ISSUE', 'DetectedIssue')
    # mr_based_on_ref_type
    _rename('mr_based_on_ref_type', 'SERVICE_REQUEST', 'ServiceRequest')
    _rename('mr_based_on_ref_type', 'MEDICATION_REQUEST', 'MedicationRequest')
    _rename('mr_based_on_ref_type', 'IMMUNIZATION_RECOMMENDATION', 'ImmunizationRecommendation')
    _rename('mr_based_on_ref_type', 'CARE_PLAN', 'CarePlan')
    # medication_ingredient_item_reference_type
    _rename('medication_ingredient_item_reference_type', 'SUBSTANCE', 'Substance')
    _rename('medication_ingredient_item_reference_type', 'MEDICATION', 'Medication')
    # location_part_of_reference_type
    _rename('location_part_of_reference_type', 'LOCATION', 'Location')
    # location_endpoint_reference_type
    _rename('location_endpoint_reference_type', 'ENDPOINT', 'Endpoint')
    # invoice_subject_reference_type
    _rename('invoice_subject_reference_type', 'PATIENT', 'Patient')
    _rename('invoice_subject_reference_type', 'GROUP', 'Group')
    # invoice_recipient_reference_type
    _rename('invoice_recipient_reference_type', 'RELATED_PERSON', 'RelatedPerson')
    _rename('invoice_recipient_reference_type', 'PATIENT', 'Patient')
    _rename('invoice_recipient_reference_type', 'ORGANIZATION', 'Organization')
    # invoice_participant_actor_reference_type
    _rename('invoice_participant_actor_reference_type', 'RELATED_PERSON', 'RelatedPerson')
    _rename('invoice_participant_actor_reference_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('invoice_participant_actor_reference_type', 'PRACTITIONER', 'Practitioner')
    _rename('invoice_participant_actor_reference_type', 'PATIENT', 'Patient')
    _rename('invoice_participant_actor_reference_type', 'ORGANIZATION', 'Organization')
    _rename('invoice_participant_actor_reference_type', 'DEVICE', 'Device')
    # invoice_line_item_chargeitem_ref_type
    _rename('invoice_line_item_chargeitem_ref_type', 'CHARGE_ITEM', 'ChargeItem')
    # invoice_account_reference_type
    _rename('invoice_account_reference_type', 'ACCOUNT', 'Account')
    # immunization_reason_reference_type
    _rename('immunization_reason_reference_type', 'OBSERVATION', 'Observation')
    _rename('immunization_reason_reference_type', 'DIAGNOSTIC_REPORT', 'DiagnosticReport')
    _rename('immunization_reason_reference_type', 'CONDITION', 'Condition')
    # immunization_reaction_detail_reference_type
    _rename('immunization_reaction_detail_reference_type', 'OBSERVATION', 'Observation')
    # immunization_performer_actor_reference_type
    _rename('immunization_performer_actor_reference_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('immunization_performer_actor_reference_type', 'PRACTITIONER', 'Practitioner')
    _rename('immunization_performer_actor_reference_type', 'ORGANIZATION', 'Organization')
    # immunization_patient_reference_type
    _rename('immunization_patient_reference_type', 'PATIENT', 'Patient')
    # immunization_location_reference_type
    _rename('immunization_location_reference_type', 'LOCATION', 'Location')
    # hs_location_ref_type
    _rename('hs_location_ref_type', 'LOCATION', 'Location')
    # hs_endpoint_ref_type
    _rename('hs_endpoint_ref_type', 'ENDPOINT', 'Endpoint')
    # hs_coverage_area_ref_type
    _rename('hs_coverage_area_ref_type', 'LOCATION', 'Location')
    # episode_of_care_team_reference_type
    _rename('episode_of_care_team_reference_type', 'CARE_TEAM', 'CareTeam')
    # episode_of_care_referral_request_reference_type
    _rename('episode_of_care_referral_request_reference_type', 'SERVICE_REQUEST', 'ServiceRequest')
    # episode_of_care_patient_reference_type
    _rename('episode_of_care_patient_reference_type', 'PATIENT', 'Patient')
    # episode_of_care_diagnosis_reference_type
    _rename('episode_of_care_diagnosis_reference_type', 'CONDITION', 'Condition')
    # episode_of_care_care_manager_reference_type
    _rename('episode_of_care_care_manager_reference_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('episode_of_care_care_manager_reference_type', 'PRACTITIONER', 'Practitioner')
    # episode_of_care_account_reference_type
    _rename('episode_of_care_account_reference_type', 'ACCOUNT', 'Account')
    # encounter_service_type_reference_type
    _rename('encounter_service_type_reference_type', 'HEALTHCARE_SERVICE', 'HealthcareService')
    # encounter_reference_type
    _rename('encounter_reference_type', 'ENCOUNTER', 'Encounter')
    # encounter_reason_value_reference_type
    _rename('encounter_reason_value_reference_type', 'PROCEDURE', 'Procedure')
    _rename('encounter_reason_value_reference_type', 'OBSERVATION', 'Observation')
    _rename('encounter_reason_value_reference_type', 'DIAGNOSTIC_REPORT', 'DiagnosticReport')
    _rename('encounter_reason_value_reference_type', 'CONDITION', 'Condition')
    # encounter_participant_reference_type
    _rename('encounter_participant_reference_type', 'RELATED_PERSON', 'RelatedPerson')
    _rename('encounter_participant_reference_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('encounter_participant_reference_type', 'PRACTITIONER', 'Practitioner')
    _rename('encounter_participant_reference_type', 'PATIENT', 'Patient')
    _rename('encounter_participant_reference_type', 'HEALTHCARE_SERVICE', 'HealthcareService')
    _rename('encounter_participant_reference_type', 'GROUP', 'Group')
    _rename('encounter_participant_reference_type', 'DEVICE', 'Device')
    # encounter_location_reference_type
    _rename('encounter_location_reference_type', 'LOCATION', 'Location')
    # encounter_episode_of_care_reference_type
    _rename('encounter_episode_of_care_reference_type', 'EPISODE_OF_CARE', 'EpisodeOfCare')
    # encounter_diagnosis_condition_type
    _rename('encounter_diagnosis_condition_type', 'CONDITION', 'Condition')
    # encounter_care_team_reference_type
    _rename('encounter_care_team_reference_type', 'CARE_TEAM', 'CareTeam')
    # encounter_based_on_reference_type
    _rename('encounter_based_on_reference_type', 'VISION_PRESCRIPTION', 'VisionPrescription')
    _rename('encounter_based_on_reference_type', 'SERVICE_REQUEST', 'ServiceRequest')
    _rename('encounter_based_on_reference_type', 'REQUEST_ORCHESTRATION', 'RequestOrchestration')
    _rename('encounter_based_on_reference_type', 'NUTRITION_ORDER', 'NutritionOrder')
    _rename('encounter_based_on_reference_type', 'MEDICATION_REQUEST', 'MedicationRequest')
    _rename('encounter_based_on_reference_type', 'DEVICE_REQUEST', 'DeviceRequest')
    _rename('encounter_based_on_reference_type', 'CARE_PLAN', 'CarePlan')
    # encounter_appointment_ref_reference_type
    _rename('encounter_appointment_ref_reference_type', 'APPOINTMENT', 'Appointment')
    # encounter_account_reference_type
    _rename('encounter_account_reference_type', 'ACCOUNT', 'Account')
    # dr_subject_type
    _rename('dr_subject_type', 'PATIENT', 'Patient')
    _rename('dr_subject_type', 'LOCATION', 'Location')
    _rename('dr_subject_type', 'GROUP', 'Group')
    _rename('dr_subject_type', 'DEVICE', 'Device')
    # dr_specimen_ref_type
    _rename('dr_specimen_ref_type', 'SPECIMEN', 'Specimen')
    # dr_result_ref_type
    _rename('dr_result_ref_type', 'OBSERVATION', 'Observation')
    # dr_req_subject_type
    _rename('dr_req_subject_type', 'PATIENT', 'Patient')
    _rename('dr_req_subject_type', 'LOCATION', 'Location')
    _rename('dr_req_subject_type', 'GROUP', 'Group')
    _rename('dr_req_subject_type', 'DEVICE', 'Device')
    # dr_req_requester_type
    _rename('dr_req_requester_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('dr_req_requester_type', 'PRACTITIONER', 'Practitioner')
    _rename('dr_req_requester_type', 'ORGANIZATION', 'Organization')
    _rename('dr_req_requester_type', 'DEVICE', 'Device')
    # dr_req_performer_ref_type
    _rename('dr_req_performer_ref_type', 'RELATED_PERSON', 'RelatedPerson')
    _rename('dr_req_performer_ref_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('dr_req_performer_ref_type', 'PRACTITIONER', 'Practitioner')
    _rename('dr_req_performer_ref_type', 'PATIENT', 'Patient')
    _rename('dr_req_performer_ref_type', 'ORGANIZATION', 'Organization')
    _rename('dr_req_performer_ref_type', 'HEALTHCARE_SERVICE', 'HealthcareService')
    _rename('dr_req_performer_ref_type', 'DEVICE', 'Device')
    _rename('dr_req_performer_ref_type', 'CARE_TEAM', 'CareTeam')
    # dr_relevant_history_ref_type
    _rename('dr_relevant_history_ref_type', 'PROVENANCE', 'Provenance')
    # dr_reason_ref_type
    _rename('dr_reason_ref_type', 'OBSERVATION', 'Observation')
    _rename('dr_reason_ref_type', 'DOCUMENT_REFERENCE', 'DocumentReference')
    _rename('dr_reason_ref_type', 'DIAGNOSTIC_REPORT', 'DiagnosticReport')
    _rename('dr_reason_ref_type', 'CONDITION', 'Condition')
    # dr_performer_type
    _rename('dr_performer_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('dr_performer_type', 'PRACTITIONER', 'Practitioner')
    _rename('dr_performer_type', 'ORGANIZATION', 'Organization')
    _rename('dr_performer_type', 'CARE_TEAM', 'CareTeam')
    # dr_note_author_ref_type
    _rename('dr_note_author_ref_type', 'RELATED_PERSON', 'RelatedPerson')
    _rename('dr_note_author_ref_type', 'PRACTITIONER', 'Practitioner')
    _rename('dr_note_author_ref_type', 'PATIENT', 'Patient')
    _rename('dr_note_author_ref_type', 'ORGANIZATION', 'Organization')
    # dr_media_link_ref_type
    _rename('dr_media_link_ref_type', 'MEDIA', 'Media')
    # dr_interpreter_type
    _rename('dr_interpreter_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('dr_interpreter_type', 'PRACTITIONER', 'Practitioner')
    _rename('dr_interpreter_type', 'ORGANIZATION', 'Organization')
    _rename('dr_interpreter_type', 'CARE_TEAM', 'CareTeam')
    # dr_insurance_ref_type
    _rename('dr_insurance_ref_type', 'COVERAGE', 'Coverage')
    _rename('dr_insurance_ref_type', 'CLAIM_RESPONSE', 'ClaimResponse')
    # dr_imaging_study_ref_type
    _rename('dr_imaging_study_ref_type', 'IMAGING_STUDY', 'ImagingStudy')
    # dr_code_ref_type
    _rename('dr_code_ref_type', 'DEVICE', 'Device')
    # dr_based_on_ref_type
    _rename('dr_based_on_ref_type', 'SERVICE_REQUEST', 'ServiceRequest')
    _rename('dr_based_on_ref_type', 'NUTRITION_ORDER', 'NutritionOrder')
    _rename('dr_based_on_ref_type', 'MEDICATION_REQUEST', 'MedicationRequest')
    _rename('dr_based_on_ref_type', 'IMMUNIZATION_RECOMMENDATION', 'ImmunizationRecommendation')
    _rename('dr_based_on_ref_type', 'CARE_PLAN', 'CarePlan')
    # document_reference_subject_reference_type
    _rename('document_reference_subject_reference_type', 'PRACTITIONER', 'Practitioner')
    _rename('document_reference_subject_reference_type', 'PATIENT', 'Patient')
    _rename('document_reference_subject_reference_type', 'GROUP', 'Group')
    _rename('document_reference_subject_reference_type', 'DEVICE', 'Device')
    # document_reference_relates_to_target_type
    _rename('document_reference_relates_to_target_type', 'DOCUMENT_REFERENCE', 'DocumentReference')
    # document_reference_context_source_patient_info_type
    _rename('document_reference_context_source_patient_info_type', 'PATIENT', 'Patient')
    # document_reference_context_encounter_type
    _rename('document_reference_context_encounter_type', 'EPISODE_OF_CARE', 'EpisodeOfCare')
    _rename('document_reference_context_encounter_type', 'ENCOUNTER', 'Encounter')
    # document_reference_author_reference_type
    _rename('document_reference_author_reference_type', 'RELATED_PERSON', 'RelatedPerson')
    _rename('document_reference_author_reference_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('document_reference_author_reference_type', 'PRACTITIONER', 'Practitioner')
    _rename('document_reference_author_reference_type', 'PATIENT', 'Patient')
    _rename('document_reference_author_reference_type', 'ORGANIZATION', 'Organization')
    _rename('document_reference_author_reference_type', 'DEVICE', 'Device')
    # document_reference_authenticator_reference_type
    _rename('document_reference_authenticator_reference_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('document_reference_authenticator_reference_type', 'PRACTITIONER', 'Practitioner')
    _rename('document_reference_authenticator_reference_type', 'ORGANIZATION', 'Organization')
    # coverage_subscriber_reference_type
    _rename('coverage_subscriber_reference_type', 'RELATED_PERSON', 'RelatedPerson')
    _rename('coverage_subscriber_reference_type', 'PATIENT', 'Patient')
    # coverage_policy_holder_reference_type
    _rename('coverage_policy_holder_reference_type', 'RELATED_PERSON', 'RelatedPerson')
    _rename('coverage_policy_holder_reference_type', 'PATIENT', 'Patient')
    _rename('coverage_policy_holder_reference_type', 'ORGANIZATION', 'Organization')
    # coverage_payor_reference_type
    _rename('coverage_payor_reference_type', 'RELATED_PERSON', 'RelatedPerson')
    _rename('coverage_payor_reference_type', 'PATIENT', 'Patient')
    _rename('coverage_payor_reference_type', 'ORGANIZATION', 'Organization')
    # coverage_contract_reference_type
    _rename('coverage_contract_reference_type', 'CONTRACT', 'Contract')
    # coverage_beneficiary_reference_type
    _rename('coverage_beneficiary_reference_type', 'PATIENT', 'Patient')
    # condition_subject_type
    _rename('condition_subject_type', 'PATIENT', 'Patient')
    _rename('condition_subject_type', 'GROUP', 'Group')
    # condition_stage_assessment_type
    _rename('condition_stage_assessment_type', 'OBSERVATION', 'Observation')
    _rename('condition_stage_assessment_type', 'DIAGNOSTIC_REPORT', 'DiagnosticReport')
    _rename('condition_stage_assessment_type', 'CLINICAL_IMPRESSION', 'ClinicalImpression')
    # condition_recorder_type
    _rename('condition_recorder_type', 'RELATED_PERSON', 'RelatedPerson')
    _rename('condition_recorder_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('condition_recorder_type', 'PRACTITIONER', 'Practitioner')
    _rename('condition_recorder_type', 'PATIENT', 'Patient')
    # condition_note_author_ref_type
    _rename('condition_note_author_ref_type', 'RELATED_PERSON', 'RelatedPerson')
    _rename('condition_note_author_ref_type', 'PRACTITIONER', 'Practitioner')
    _rename('condition_note_author_ref_type', 'PATIENT', 'Patient')
    _rename('condition_note_author_ref_type', 'ORGANIZATION', 'Organization')
    # condition_asserter_type
    _rename('condition_asserter_type', 'RELATED_PERSON', 'RelatedPerson')
    _rename('condition_asserter_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('condition_asserter_type', 'PRACTITIONER', 'Practitioner')
    _rename('condition_asserter_type', 'PATIENT', 'Patient')
    # claim_response_requestor_ref_type
    _rename('claim_response_requestor_ref_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('claim_response_requestor_ref_type', 'PRACTITIONER', 'Practitioner')
    _rename('claim_response_requestor_ref_type', 'ORGANIZATION', 'Organization')
    # claim_response_request_ref_type
    _rename('claim_response_request_ref_type', 'CLAIM', 'Claim')
    # claim_response_patient_ref_type
    _rename('claim_response_patient_ref_type', 'PATIENT', 'Patient')
    # claim_response_insurance_cr_ref_type
    _rename('claim_response_insurance_cr_ref_type', 'CLAIM_RESPONSE', 'ClaimResponse')
    # claim_response_insurance_coverage_ref_type
    _rename('claim_response_insurance_coverage_ref_type', 'COVERAGE', 'Coverage')
    # claim_response_comm_req_ref_type
    _rename('claim_response_comm_req_ref_type', 'COMMUNICATION_REQUEST', 'CommunicationRequest')
    # claim_response_add_item_provider_ref_type
    _rename('claim_response_add_item_provider_ref_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('claim_response_add_item_provider_ref_type', 'PRACTITIONER', 'Practitioner')
    _rename('claim_response_add_item_provider_ref_type', 'ORGANIZATION', 'Organization')
    # claim_response_add_item_location_ref_type
    _rename('claim_response_add_item_location_ref_type', 'LOCATION', 'Location')
    # claim_related_claim_ref_type
    _rename('claim_related_claim_ref_type', 'CLAIM', 'Claim')
    # claim_referral_ref_type
    _rename('claim_referral_ref_type', 'SERVICE_REQUEST', 'ServiceRequest')
    # claim_provider_ref_type
    _rename('claim_provider_ref_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('claim_provider_ref_type', 'PRACTITIONER', 'Practitioner')
    _rename('claim_provider_ref_type', 'ORGANIZATION', 'Organization')
    # claim_procedure_ref_type
    _rename('claim_procedure_ref_type', 'PROCEDURE', 'Procedure')
    # claim_prescription_ref_type
    _rename('claim_prescription_ref_type', 'VISION_PRESCRIPTION', 'VisionPrescription')
    _rename('claim_prescription_ref_type', 'MEDICATION_REQUEST', 'MedicationRequest')
    _rename('claim_prescription_ref_type', 'DEVICE_REQUEST', 'DeviceRequest')
    # claim_payee_party_ref_type
    _rename('claim_payee_party_ref_type', 'RELATED_PERSON', 'RelatedPerson')
    _rename('claim_payee_party_ref_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('claim_payee_party_ref_type', 'PRACTITIONER', 'Practitioner')
    _rename('claim_payee_party_ref_type', 'PATIENT', 'Patient')
    _rename('claim_payee_party_ref_type', 'ORGANIZATION', 'Organization')
    # claim_patient_ref_type
    _rename('claim_patient_ref_type', 'PATIENT', 'Patient')
    # claim_location_ref_type
    _rename('claim_location_ref_type', 'LOCATION', 'Location')
    # claim_item_encounter_ref_type
    _rename('claim_item_encounter_ref_type', 'ENCOUNTER', 'Encounter')
    # claim_insurance_coverage_ref_type
    _rename('claim_insurance_coverage_ref_type', 'COVERAGE', 'Coverage')
    # claim_insurance_claim_response_ref_type
    _rename('claim_insurance_claim_response_ref_type', 'CLAIM_RESPONSE', 'ClaimResponse')
    # claim_enterer_ref_type
    _rename('claim_enterer_ref_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('claim_enterer_ref_type', 'PRACTITIONER', 'Practitioner')
    # claim_diagnosis_condition_ref_type
    _rename('claim_diagnosis_condition_ref_type', 'CONDITION', 'Condition')
    # claim_device_ref_type
    _rename('claim_device_ref_type', 'DEVICE', 'Device')
    # care_plan_subject_reference_type
    _rename('care_plan_subject_reference_type', 'PATIENT', 'Patient')
    _rename('care_plan_subject_reference_type', 'GROUP', 'Group')
    # care_plan_replaces_reference_type
    _rename('care_plan_replaces_reference_type', 'CARE_PLAN', 'CarePlan')
    # care_plan_part_of_reference_type
    _rename('care_plan_part_of_reference_type', 'CARE_PLAN', 'CarePlan')
    # care_plan_goal_reference_type
    _rename('care_plan_goal_reference_type', 'GOAL', 'Goal')
    # care_plan_detail_reason_reference_type
    _rename('care_plan_detail_reason_reference_type', 'OBSERVATION', 'Observation')
    _rename('care_plan_detail_reason_reference_type', 'DOCUMENT_REFERENCE', 'DocumentReference')
    _rename('care_plan_detail_reason_reference_type', 'DIAGNOSTIC_REPORT', 'DiagnosticReport')
    _rename('care_plan_detail_reason_reference_type', 'CONDITION', 'Condition')
    # care_plan_detail_product_reference_type
    _rename('care_plan_detail_product_reference_type', 'SUBSTANCE', 'Substance')
    _rename('care_plan_detail_product_reference_type', 'MEDICATION', 'Medication')
    # care_plan_detail_performer_reference_type
    _rename('care_plan_detail_performer_reference_type', 'RELATED_PERSON', 'RelatedPerson')
    _rename('care_plan_detail_performer_reference_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('care_plan_detail_performer_reference_type', 'PRACTITIONER', 'Practitioner')
    _rename('care_plan_detail_performer_reference_type', 'PATIENT', 'Patient')
    _rename('care_plan_detail_performer_reference_type', 'ORGANIZATION', 'Organization')
    _rename('care_plan_detail_performer_reference_type', 'HEALTHCARE_SERVICE', 'HealthcareService')
    _rename('care_plan_detail_performer_reference_type', 'DEVICE', 'Device')
    _rename('care_plan_detail_performer_reference_type', 'CARE_TEAM', 'CareTeam')
    # care_plan_detail_location_reference_type
    _rename('care_plan_detail_location_reference_type', 'LOCATION', 'Location')
    # care_plan_detail_goal_reference_type
    _rename('care_plan_detail_goal_reference_type', 'GOAL', 'Goal')
    # care_plan_contributor_reference_type
    _rename('care_plan_contributor_reference_type', 'RELATED_PERSON', 'RelatedPerson')
    _rename('care_plan_contributor_reference_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('care_plan_contributor_reference_type', 'PRACTITIONER', 'Practitioner')
    _rename('care_plan_contributor_reference_type', 'PATIENT', 'Patient')
    _rename('care_plan_contributor_reference_type', 'ORGANIZATION', 'Organization')
    _rename('care_plan_contributor_reference_type', 'DEVICE', 'Device')
    _rename('care_plan_contributor_reference_type', 'CARE_TEAM', 'CareTeam')
    # care_plan_care_team_reference_type
    _rename('care_plan_care_team_reference_type', 'CARE_TEAM', 'CareTeam')
    # care_plan_based_on_reference_type
    _rename('care_plan_based_on_reference_type', 'CARE_PLAN', 'CarePlan')
    # care_plan_author_reference_type
    _rename('care_plan_author_reference_type', 'RELATED_PERSON', 'RelatedPerson')
    _rename('care_plan_author_reference_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('care_plan_author_reference_type', 'PRACTITIONER', 'Practitioner')
    _rename('care_plan_author_reference_type', 'PATIENT', 'Patient')
    _rename('care_plan_author_reference_type', 'ORGANIZATION', 'Organization')
    _rename('care_plan_author_reference_type', 'DEVICE', 'Device')
    _rename('care_plan_author_reference_type', 'CARE_TEAM', 'CareTeam')
    # care_plan_addresses_reference_type
    _rename('care_plan_addresses_reference_type', 'CONDITION', 'Condition')
    # care_plan_activity_reference_type
    _rename('care_plan_activity_reference_type', 'VISION_PRESCRIPTION', 'VisionPrescription')
    _rename('care_plan_activity_reference_type', 'TASK', 'Task')
    _rename('care_plan_activity_reference_type', 'SERVICE_REQUEST', 'ServiceRequest')
    _rename('care_plan_activity_reference_type', 'REQUEST_GROUP', 'RequestGroup')
    _rename('care_plan_activity_reference_type', 'NUTRITION_ORDER', 'NutritionOrder')
    _rename('care_plan_activity_reference_type', 'MEDICATION_REQUEST', 'MedicationRequest')
    _rename('care_plan_activity_reference_type', 'DEVICE_REQUEST', 'DeviceRequest')
    _rename('care_plan_activity_reference_type', 'COMMUNICATION_REQUEST', 'CommunicationRequest')
    _rename('care_plan_activity_reference_type', 'APPOINTMENT', 'Appointment')
    # author_reference_type
    _rename('author_reference_type', 'RELATED_PERSON', 'RelatedPerson')
    _rename('author_reference_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('author_reference_type', 'PRACTITIONER', 'Practitioner')
    _rename('author_reference_type', 'PATIENT', 'Patient')
    _rename('author_reference_type', 'ORGANIZATION', 'Organization')
    _rename('author_reference_type', 'DEVICE', 'Device')
    # audit_event_who_reference_type
    _rename('audit_event_who_reference_type', 'RELATED_PERSON', 'RelatedPerson')
    _rename('audit_event_who_reference_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('audit_event_who_reference_type', 'PRACTITIONER', 'Practitioner')
    _rename('audit_event_who_reference_type', 'PATIENT', 'Patient')
    _rename('audit_event_who_reference_type', 'ORGANIZATION', 'Organization')
    _rename('audit_event_who_reference_type', 'DEVICE', 'Device')
    # audit_event_location_reference_type
    _rename('audit_event_location_reference_type', 'LOCATION', 'Location')
    # appointment_slot_reference_type
    _rename('appointment_slot_reference_type', 'SLOT', 'Slot')
    # appointment_service_type_reference_type
    _rename('appointment_service_type_reference_type', 'HEALTHCARE_SERVICE', 'HealthcareService')
    # appointment_replaces_reference_type
    _rename('appointment_replaces_reference_type', 'APPOINTMENT', 'Appointment')
    # appointment_reason_reference_type
    _rename('appointment_reason_reference_type', 'PROCEDURE', 'Procedure')
    _rename('appointment_reason_reference_type', 'OBSERVATION', 'Observation')
    _rename('appointment_reason_reference_type', 'IMMUNIZATION_RECOMMENDATION', 'ImmunizationRecommendation')
    _rename('appointment_reason_reference_type', 'DIAGNOSTIC_REPORT', 'DiagnosticReport')
    _rename('appointment_reason_reference_type', 'CONDITION', 'Condition')
    # appointment_pi_reference_type
    _rename('appointment_pi_reference_type', 'DOCUMENT_REFERENCE', 'DocumentReference')
    _rename('appointment_pi_reference_type', 'COMMUNICATION', 'Communication')
    _rename('appointment_pi_reference_type', 'BINARY', 'Binary')
    # appointment_participant_actor_type
    _rename('appointment_participant_actor_type', 'RELATED_PERSON', 'RelatedPerson')
    _rename('appointment_participant_actor_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('appointment_participant_actor_type', 'PRACTITIONER', 'Practitioner')
    _rename('appointment_participant_actor_type', 'PATIENT', 'Patient')
    _rename('appointment_participant_actor_type', 'LOCATION', 'Location')
    _rename('appointment_participant_actor_type', 'HEALTHCARE_SERVICE', 'HealthcareService')
    _rename('appointment_participant_actor_type', 'GROUP', 'Group')
    _rename('appointment_participant_actor_type', 'DEVICE', 'Device')
    _rename('appointment_participant_actor_type', 'CARE_TEAM', 'CareTeam')
    # appointment_note_author_reference_type
    _rename('appointment_note_author_reference_type', 'RELATED_PERSON', 'RelatedPerson')
    _rename('appointment_note_author_reference_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('appointment_note_author_reference_type', 'PRACTITIONER', 'Practitioner')
    _rename('appointment_note_author_reference_type', 'PATIENT', 'Patient')
    _rename('appointment_note_author_reference_type', 'ORGANIZATION', 'Organization')
    # appointment_based_on_reference_type
    _rename('appointment_based_on_reference_type', 'VISION_PRESCRIPTION', 'VisionPrescription')
    _rename('appointment_based_on_reference_type', 'SERVICE_REQUEST', 'ServiceRequest')
    _rename('appointment_based_on_reference_type', 'REQUEST_ORCHESTRATION', 'RequestOrchestration')
    _rename('appointment_based_on_reference_type', 'NUTRITION_ORDER', 'NutritionOrder')
    _rename('appointment_based_on_reference_type', 'MEDICATION_REQUEST', 'MedicationRequest')
    _rename('appointment_based_on_reference_type', 'DEVICE_REQUEST', 'DeviceRequest')
    _rename('appointment_based_on_reference_type', 'CARE_PLAN', 'CarePlan')
    # appointment_account_reference_type
    _rename('appointment_account_reference_type', 'ACCOUNT', 'Account')
    # allergy_intolerance_patient_reference_type
    _rename('allergy_intolerance_patient_reference_type', 'PATIENT', 'Patient')
    # allergy_intolerance_participant_reference_type
    _rename('allergy_intolerance_participant_reference_type', 'RELATED_PERSON', 'RelatedPerson')
    _rename('allergy_intolerance_participant_reference_type', 'PRACTITIONER_ROLE', 'PractitionerRole')
    _rename('allergy_intolerance_participant_reference_type', 'PRACTITIONER', 'Practitioner')
    _rename('allergy_intolerance_participant_reference_type', 'PATIENT', 'Patient')
