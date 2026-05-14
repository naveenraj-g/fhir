from sqlalchemy import (
    Column,
    String,
    DateTime,
    Integer,
    ForeignKey,
    Text,
    Boolean,
    Float,
    Sequence,
    Enum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import FHIRBase as Base
from app.models.questionnaire_response.enums import QuestionnaireResponseStatus
from app.models.enums import SubjectReferenceType
from app.models.questionnaire_response.enums import (
    QuestionnaireResponseAuthorReferenceType,
    QuestionnaireResponseSourceReferenceType,
)

questionnaire_response_id_seq = Sequence(
    "questionnaire_response_id_seq", start=60000, increment=1
)


class QuestionnaireResponseModel(Base):
    __tablename__ = "questionnaire_response"

    # Internal PK — never exposed
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # Public ID — used in all API responses and FHIR output
    questionnaire_response_id = Column(
        Integer,
        questionnaire_response_id_seq,
        server_default=questionnaire_response_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    user_id = Column(String, nullable=True, index=True)
    org_id = Column(String, nullable=True, index=True)

    # Required
    questionnaire = Column(String, nullable=False)  # canonical URL
    status = Column(
        Enum(QuestionnaireResponseStatus), nullable=False
    )  # in-progress | completed | amended | entered-in-error | stopped

    # Subject reference — stored as type enum + integer ID
    subject_type = Column(
        Enum(SubjectReferenceType, name="subject_reference_type"),
        nullable=True,
    )
    subject_id = Column(Integer, nullable=True)
    subject_display = Column(String, nullable=True)

    # Encounter reference — the encounter this questionnaire response belongs to
    encounter_id = Column(
        Integer, ForeignKey("encounter.id"), nullable=True, index=True
    )

    # Authored / Author / Source
    authored = Column(DateTime(timezone=True), nullable=True)

    author_reference_type = Column(
        Enum(QuestionnaireResponseAuthorReferenceType, name="author_reference_type"),
        nullable=True,
    )
    author_reference_id = Column(Integer, nullable=True)
    author_reference_display = Column(String, nullable=True)

    source_reference_type = Column(
        Enum(QuestionnaireResponseSourceReferenceType, name="source_reference_type"),
        nullable=True,
    )
    source_reference_id = Column(Integer, nullable=True)
    source_reference_display = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    items = relationship(
        "QuestionnaireResponseItemModel",
        back_populates="response",
        cascade="all, delete-orphan",
        foreign_keys="QuestionnaireResponseItemModel.response_id",
    )
    encounter = relationship("EncounterModel", back_populates="questionnaire_responses")


class QuestionnaireResponseItemModel(Base):
    __tablename__ = "questionnaire_response_item"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    response_id = Column(
        Integer, ForeignKey("questionnaire_response.id"), nullable=False, index=True
    )
    parent_item_id = Column(
        Integer, ForeignKey("questionnaire_response_item.id"), nullable=True, index=True
    )
    org_id = Column(String, nullable=True)

    link_id = Column(String, nullable=False)
    text = Column(String, nullable=True)
    definition = Column(String, nullable=True)

    response = relationship(
        "QuestionnaireResponseModel",
        back_populates="items",
        foreign_keys=[response_id],
    )
    answers = relationship(
        "QuestionnaireResponseAnswerModel",
        back_populates="item",
        cascade="all, delete-orphan",
    )
    sub_items = relationship(
        "QuestionnaireResponseItemModel",
        cascade="all, delete-orphan",
        foreign_keys=[parent_item_id],
    )


class QuestionnaireResponseAnswerModel(Base):
    __tablename__ = "questionnaire_response_answer"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    item_id = Column(
        Integer,
        ForeignKey("questionnaire_response_item.id"),
        nullable=False,
        index=True,
    )
    org_id = Column(String, nullable=True)

    # Discriminator for which value[x] is stored
    value_type = Column(String, nullable=False)

    # Scalar values
    value_string = Column(
        Text, nullable=True
    )  # valueString, valueUri, valueTime, valueDate
    value_boolean = Column(Boolean, nullable=True)  # valueBoolean
    value_integer = Column(Integer, nullable=True)  # valueInteger
    value_decimal = Column(Float, nullable=True)  # valueDecimal
    value_datetime = Column(DateTime(timezone=True), nullable=True)  # valueDateTime

    # valueCoding
    value_coding_system = Column(String, nullable=True)
    value_coding_code = Column(String, nullable=True)
    value_coding_display = Column(String, nullable=True)

    # valueReference
    value_reference = Column(String, nullable=True)
    value_reference_display = Column(String, nullable=True)

    # valueQuantity
    value_quantity_value = Column(Float, nullable=True)
    value_quantity_unit = Column(String, nullable=True)
    value_quantity_system = Column(String, nullable=True)
    value_quantity_code = Column(String, nullable=True)

    item = relationship("QuestionnaireResponseItemModel", back_populates="answers")
