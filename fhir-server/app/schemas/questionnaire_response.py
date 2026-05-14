from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.questionnaire_response.enums import QuestionnaireResponseStatus


# ── Answer value sub-types ─────────────────────────────────────────────────


class AnswerCodingInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    system: Optional[str] = None
    code: Optional[str] = None
    display: Optional[str] = None


class AnswerQuantityInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    value: Optional[float] = None
    unit: Optional[str] = None
    system: Optional[str] = None
    code: Optional[str] = None


# ── Answer input ───────────────────────────────────────────────────────────


class AnswerInput(BaseModel):
    """
    A single answer within a QuestionnaireResponse item.
    Set exactly one value field to match the question type.
    """

    model_config = ConfigDict(extra="forbid")

    value_boolean: Optional[bool] = None
    value_decimal: Optional[float] = None
    value_integer: Optional[int] = None
    value_date: Optional[str] = Field(None, description="Date answer (YYYY-MM-DD).", examples=["2024-06-01"])
    value_datetime: Optional[datetime] = None
    value_time: Optional[str] = Field(None, description="Time answer (HH:MM:SS).", examples=["09:00:00"])
    value_string: Optional[str] = None
    value_uri: Optional[str] = None
    value_coding: Optional[AnswerCodingInput] = None
    value_quantity: Optional[AnswerQuantityInput] = None
    value_reference: Optional[str] = Field(
        None,
        description="Reference answer using the public resource ID, e.g. 'Patient/10001'.",
    )
    item: Optional[List["ItemInput"]] = None


# ── Item input (recursive) ─────────────────────────────────────────────────


class ItemInput(BaseModel):
    """
    A group or question item within the QuestionnaireResponse.
    Items can be nested to represent grouped questions.
    """

    model_config = ConfigDict(extra="forbid")

    link_id: str = Field(..., description="Pointer to the specific item from the Questionnaire.", examples=["1.1"])
    definition: Optional[str] = None
    text: Optional[str] = Field(None, description="Question text or group name.", examples=["What is your date of birth?"])
    answer: Optional[List[AnswerInput]] = None
    item: Optional[List["ItemInput"]] = None


AnswerInput.model_rebuild()
ItemInput.model_rebuild()


# ── Create / patch ─────────────────────────────────────────────────────────


class QuestionnaireResponseCreateSchema(BaseModel):
    """
    Payload for creating a QuestionnaireResponse.

    A QuestionnaireResponse is a completed or in-progress set of answers to
    questions from a Questionnaire. References use public IDs
    (e.g. Patient/10001, Encounter/20001, Practitioner/30001).
    Supply user_id and org_id to bind the record to a specific user and
    organisation; omit them to create an unowned record.
    The caller's sub JWT claim is recorded as created_by.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "user_id": "user-uuid-123",
                "org_id": "org-uuid-456",
                "questionnaire": "http://example.org/fhir/Questionnaire/phq-9",
                "status": "completed",
                "subject": "Patient/10001",
                "encounter": "Encounter/20001",
                "authored": "2024-06-01T09:00:00Z",
                "author": "Practitioner/30001",
                "source": "Patient/10001",
                "item": [
                    {
                        "link_id": "1",
                        "text": "Over the last 2 weeks, how often have you felt down, depressed, or hopeless?",
                        "answer": [
                            {
                                "value_coding": {
                                    "system": "http://loinc.org",
                                    "code": "LA6568-5",
                                    "display": "Not at all",
                                }
                            }
                        ],
                    },
                    {
                        "link_id": "2",
                        "text": "Mental health group",
                        "item": [
                            {
                                "link_id": "2.1",
                                "text": "Do you have difficulty concentrating?",
                                "answer": [{"value_boolean": False}],
                            }
                        ],
                    },
                ],
            }
        },
    )

    user_id: Optional[str] = None
    org_id: Optional[str] = None
    questionnaire: str = Field(
        ...,
        description="Canonical URL or id of the Questionnaire this response answers.",
        examples=["http://example.org/fhir/Questionnaire/phq-9"],
    )
    status: QuestionnaireResponseStatus
    subject: Optional[str] = Field(
        None,
        description="Subject reference using the public patient_id, e.g. 'Patient/10001'.",
    )
    subject_display: Optional[str] = None
    encounter: Optional[str] = Field(
        None,
        description="Encounter reference, e.g. 'Encounter/20001'.",
    )
    authored: Optional[datetime] = Field(None, description="Date/time the answers were gathered.")
    author: Optional[str] = Field(
        None,
        description="Who recorded the answers, e.g. 'Practitioner/30001' or 'Patient/10001'.",
    )
    author_display: Optional[str] = None
    source: Optional[str] = Field(
        None,
        description="Who answered the questions (if different from author), e.g. 'Patient/10001'.",
    )
    source_display: Optional[str] = None
    item: Optional[List[ItemInput]] = None


class QuestionnaireResponsePatchSchema(BaseModel):
    """
    Partial update for a QuestionnaireResponse.

    Only lifecycle fields are patchable after creation. To replace items,
    re-create the resource.
    """

    model_config = ConfigDict(extra="forbid")

    status: Optional[QuestionnaireResponseStatus] = None
    authored: Optional[datetime] = None
