from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Sequence,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import FHIRBase as Base
from app.models.questionnaire.enums import (
    QuestionnaireEnableBehavior,
    QuestionnaireItemOperator,
    QuestionnaireItemType,
    QuestionnaireStatus,
    QuestionnaireUseContextReferenceType,
)

questionnaire_id_seq = Sequence("questionnaire_pub_seq", start=370000, increment=1, metadata=Base.metadata)


class QuestionnaireModel(Base):
    """FHIR R4 Questionnaire — a structured set of questions (form definition)."""

    __tablename__ = "questionnaire"

    # Internal PK — never exposed
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # Public ID — used in all API responses and FHIR output
    questionnaire_id = Column(
        Integer,
        questionnaire_id_seq,
        server_default=questionnaire_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    user_id = Column(String, nullable=True, index=True)
    org_id = Column(String, nullable=True, index=True)

    # ── Metadata (all 0..1 primitives) ────────────────────────────────────────

    url = Column(String, nullable=True, index=True)  # canonical identifier (uri)
    version = Column(String, nullable=True, index=True)
    name = Column(String, nullable=True, index=True)  # machine-friendly name
    title = Column(String, nullable=True)
    status = Column(Enum(QuestionnaireStatus, name="questionnaire_status"), nullable=False, index=True)
    experimental = Column(Boolean, nullable=True)
    date = Column(DateTime(timezone=True), nullable=True, index=True)
    publisher = Column(String, nullable=True)
    description = Column(Text, nullable=True)  # markdown
    purpose = Column(Text, nullable=True)  # markdown
    copyright = Column(Text, nullable=True)  # markdown
    approval_date = Column(Date, nullable=True)
    last_review_date = Column(Date, nullable=True)

    # derivedFrom (0..* canonical(Questionnaire)) — comma-separated, never filtered individually
    derived_from = Column(Text, nullable=True)

    # effectivePeriod (0..1 Period)
    effective_period_start = Column(DateTime(timezone=True), nullable=True)
    effective_period_end = Column(DateTime(timezone=True), nullable=True)

    # ── Audit ─────────────────────────────────────────────────────────────────

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────

    identifiers = relationship("QuestionnaireIdentifier", back_populates="questionnaire", cascade="all, delete-orphan")
    subject_types = relationship("QuestionnaireSubjectType", back_populates="questionnaire", cascade="all, delete-orphan")
    contacts = relationship("QuestionnaireContact", back_populates="questionnaire", cascade="all, delete-orphan")
    use_contexts = relationship("QuestionnaireUseContext", back_populates="questionnaire", cascade="all, delete-orphan")
    jurisdictions = relationship("QuestionnaireJurisdiction", back_populates="questionnaire", cascade="all, delete-orphan")
    codes = relationship("QuestionnaireCode", back_populates="questionnaire", cascade="all, delete-orphan")
    # Every item at every depth, stored flat (tree rebuilt from parent_item_id by the mapper).
    items = relationship(
        "QuestionnaireItem",
        back_populates="questionnaire",
        cascade="all, delete-orphan",
        foreign_keys="QuestionnaireItem.questionnaire_id",
        order_by="QuestionnaireItem.position",
    )


# ── Questionnaire-level child tables ───────────────────────────────────────────


class QuestionnaireIdentifier(Base):
    """identifier[] — business identifiers."""

    __tablename__ = "questionnaire_identifier"

    id = Column(Integer, primary_key=True, autoincrement=True)
    questionnaire_id = Column(Integer, ForeignKey("questionnaire.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    use = Column(String, nullable=True)
    type_system = Column(String, nullable=True)
    type_code = Column(String, nullable=True)
    type_display = Column(String, nullable=True)
    type_text = Column(String, nullable=True)
    system = Column(String, nullable=True)
    value = Column(String, nullable=False)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)
    assigner = Column(String, nullable=True)

    questionnaire = relationship("QuestionnaireModel", back_populates="identifiers")


class QuestionnaireSubjectType(Base):
    """subjectType[] — resource types that can be the subject of a QuestionnaireResponse."""

    __tablename__ = "questionnaire_subject_type"

    id = Column(Integer, primary_key=True, autoincrement=True)
    questionnaire_id = Column(Integer, ForeignKey("questionnaire.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    code = Column(String, nullable=False, index=True)  # ResourceType code e.g. "Patient"

    questionnaire = relationship("QuestionnaireModel", back_populates="subject_types")


class QuestionnaireContact(Base):
    """contact[] — ContactDetail (name + telecom[])."""

    __tablename__ = "questionnaire_contact"

    id = Column(Integer, primary_key=True, autoincrement=True)
    questionnaire_id = Column(Integer, ForeignKey("questionnaire.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    name = Column(String, nullable=True)

    questionnaire = relationship("QuestionnaireModel", back_populates="contacts")
    telecoms = relationship("QuestionnaireContactTelecom", back_populates="contact", cascade="all, delete-orphan")


class QuestionnaireContactTelecom(Base):
    """contact.telecom[] — ContactPoint."""

    __tablename__ = "questionnaire_contact_telecom"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contact_id = Column(Integer, ForeignKey("questionnaire_contact.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    system = Column(String, nullable=True)
    value = Column(String, nullable=True)
    use = Column(String, nullable=True)
    rank = Column(Integer, nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    contact = relationship("QuestionnaireContact", back_populates="telecoms")


class QuestionnaireUseContext(Base):
    """useContext[] — UsageContext: code (Coding) + value[x] (CodeableConcept | Quantity | Range | Reference)."""

    __tablename__ = "questionnaire_use_context"

    id = Column(Integer, primary_key=True, autoincrement=True)
    questionnaire_id = Column(Integer, ForeignKey("questionnaire.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    # code (1..1 Coding)
    code_system = Column(String, nullable=True)
    code_code = Column(String, nullable=True, index=True)
    code_display = Column(String, nullable=True)

    # value[x] — one column group per variant, mapper uses whichever is non-null
    value_cc_system = Column(String, nullable=True)
    value_cc_code = Column(String, nullable=True, index=True)
    value_cc_display = Column(String, nullable=True)
    value_cc_text = Column(String, nullable=True)

    value_quantity_value = Column(Float, nullable=True)
    value_quantity_unit = Column(String, nullable=True)
    value_quantity_system = Column(String, nullable=True)
    value_quantity_code = Column(String, nullable=True)

    value_range_low_value = Column(Float, nullable=True)
    value_range_low_unit = Column(String, nullable=True)
    value_range_high_value = Column(Float, nullable=True)
    value_range_high_unit = Column(String, nullable=True)

    value_reference_type = Column(
        Enum(QuestionnaireUseContextReferenceType, name="questionnaire_use_context_ref_type"), nullable=True
    )
    value_reference_id = Column(Integer, nullable=True)
    value_reference_display = Column(String, nullable=True)

    questionnaire = relationship("QuestionnaireModel", back_populates="use_contexts")


class QuestionnaireJurisdiction(Base):
    """jurisdiction[] — CodeableConcept."""

    __tablename__ = "questionnaire_jurisdiction"

    id = Column(Integer, primary_key=True, autoincrement=True)
    questionnaire_id = Column(Integer, ForeignKey("questionnaire.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    coding_system = Column(String, nullable=True)
    coding_code = Column(String, nullable=True, index=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)

    questionnaire = relationship("QuestionnaireModel", back_populates="jurisdictions")


class QuestionnaireCode(Base):
    """code[] — Coding that describes the questionnaire as a whole."""

    __tablename__ = "questionnaire_code"

    id = Column(Integer, primary_key=True, autoincrement=True)
    questionnaire_id = Column(Integer, ForeignKey("questionnaire.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    system = Column(String, nullable=True)
    code = Column(String, nullable=True, index=True)
    display = Column(String, nullable=True)

    questionnaire = relationship("QuestionnaireModel", back_populates="codes")


# ── item (recursive BackboneElement) ────────────────────────────────────────────


class QuestionnaireItem(Base):
    """
    item[] — a question, group or display element. Nested items (0..* at every
    level) are rows pointing at their parent through parent_item_id; every row
    also carries questionnaire_id so the whole tree loads in one query.
    """

    __tablename__ = "questionnaire_item"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    questionnaire_id = Column(Integer, ForeignKey("questionnaire.id"), nullable=False, index=True)
    parent_item_id = Column(Integer, ForeignKey("questionnaire_item.id"), nullable=True, index=True)
    org_id = Column(String, nullable=True)

    # Global creation order (depth-first) — preserves sibling order on read.
    position = Column(Integer, nullable=False, default=0)

    link_id = Column(String, nullable=False)  # 1..1, unique within the Questionnaire
    definition = Column(String, nullable=True, index=True)  # uri to an ElementDefinition
    prefix = Column(String, nullable=True)
    text = Column(Text, nullable=True)
    type = Column(Enum(QuestionnaireItemType, name="questionnaire_item_type"), nullable=False)
    enable_behavior = Column(Enum(QuestionnaireEnableBehavior, name="questionnaire_enable_behavior"), nullable=True)
    required = Column(Boolean, nullable=True)
    repeats = Column(Boolean, nullable=True)
    read_only = Column(Boolean, nullable=True)
    max_length = Column(Integer, nullable=True)
    answer_value_set = Column(String, nullable=True)  # canonical(ValueSet)

    questionnaire = relationship("QuestionnaireModel", back_populates="items", foreign_keys=[questionnaire_id])
    parent = relationship(
        "QuestionnaireItem", back_populates="sub_items", remote_side="QuestionnaireItem.id", foreign_keys=[parent_item_id]
    )
    sub_items = relationship(
        "QuestionnaireItem",
        back_populates="parent",
        cascade="all, delete-orphan",
        foreign_keys=[parent_item_id],
    )
    codes = relationship("QuestionnaireItemCode", back_populates="item", cascade="all, delete-orphan")
    enable_whens = relationship("QuestionnaireItemEnableWhen", back_populates="item", cascade="all, delete-orphan")
    answer_options = relationship("QuestionnaireItemAnswerOption", back_populates="item", cascade="all, delete-orphan")
    initials = relationship("QuestionnaireItemInitial", back_populates="item", cascade="all, delete-orphan")


class QuestionnaireItemCode(Base):
    """item.code[] — Coding that corresponds to this item."""

    __tablename__ = "questionnaire_item_code"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(Integer, ForeignKey("questionnaire_item.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    system = Column(String, nullable=True)
    code = Column(String, nullable=True, index=True)
    display = Column(String, nullable=True)

    item = relationship("QuestionnaireItem", back_populates="codes")


class QuestionnaireItemEnableWhen(Base):
    """item.enableWhen[] — condition controlling whether the item is shown (answer[x] 1..1)."""

    __tablename__ = "questionnaire_item_enable_when"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(Integer, ForeignKey("questionnaire_item.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    question = Column(String, nullable=False)  # linkId of the governing question
    operator = Column(Enum(QuestionnaireItemOperator, name="questionnaire_item_operator"), nullable=False)

    # answer[x] — Boolean | Decimal | Integer | Date | DateTime | Time | String | Coding | Quantity | Reference(Any)
    answer_boolean = Column(Boolean, nullable=True)
    answer_decimal = Column(Float, nullable=True)
    answer_integer = Column(Integer, nullable=True)
    answer_date = Column(Date, nullable=True)
    answer_datetime = Column(DateTime(timezone=True), nullable=True)
    answer_time = Column(String, nullable=True)
    answer_string = Column(Text, nullable=True)
    answer_coding_system = Column(String, nullable=True)
    answer_coding_code = Column(String, nullable=True)
    answer_coding_display = Column(String, nullable=True)
    answer_quantity_value = Column(Float, nullable=True)
    answer_quantity_unit = Column(String, nullable=True)
    answer_quantity_system = Column(String, nullable=True)
    answer_quantity_code = Column(String, nullable=True)
    # Reference(Any) — open type, so the resource type is a free string
    answer_reference_type = Column(String, nullable=True)
    answer_reference_id = Column(Integer, nullable=True)
    answer_reference_display = Column(String, nullable=True)

    item = relationship("QuestionnaireItem", back_populates="enable_whens")


class QuestionnaireItemAnswerOption(Base):
    """item.answerOption[] — permitted answer (value[x] 1..1) for choice-type items."""

    __tablename__ = "questionnaire_item_answer_option"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(Integer, ForeignKey("questionnaire_item.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    initial_selected = Column(Boolean, nullable=True)

    # value[x] — Integer | Date | Time | String | Coding | Reference(Any)
    value_integer = Column(Integer, nullable=True)
    value_date = Column(Date, nullable=True)
    value_time = Column(String, nullable=True)
    value_string = Column(Text, nullable=True)
    value_coding_system = Column(String, nullable=True)
    value_coding_code = Column(String, nullable=True)
    value_coding_display = Column(String, nullable=True)
    value_reference_type = Column(String, nullable=True)
    value_reference_id = Column(Integer, nullable=True)
    value_reference_display = Column(String, nullable=True)

    item = relationship("QuestionnaireItem", back_populates="answer_options")


class QuestionnaireItemInitial(Base):
    """item.initial[] — initial value (value[x] 1..1) pre-populated in the form."""

    __tablename__ = "questionnaire_item_initial"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(Integer, ForeignKey("questionnaire_item.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    # value[x] — Boolean | Decimal | Integer | Date | DateTime | Time | String | Uri | Attachment | Coding | Quantity | Reference(Any)
    value_boolean = Column(Boolean, nullable=True)
    value_decimal = Column(Float, nullable=True)
    value_integer = Column(Integer, nullable=True)
    value_date = Column(Date, nullable=True)
    value_datetime = Column(DateTime(timezone=True), nullable=True)
    value_time = Column(String, nullable=True)
    value_string = Column(Text, nullable=True)
    value_uri = Column(String, nullable=True)
    value_attachment_content_type = Column(String, nullable=True)
    value_attachment_language = Column(String, nullable=True)
    value_attachment_data = Column(Text, nullable=True)  # base64Binary
    value_attachment_url = Column(String, nullable=True)
    value_attachment_size = Column(Integer, nullable=True)
    value_attachment_hash = Column(String, nullable=True)
    value_attachment_title = Column(String, nullable=True)
    value_attachment_creation = Column(DateTime(timezone=True), nullable=True)
    value_coding_system = Column(String, nullable=True)
    value_coding_code = Column(String, nullable=True)
    value_coding_display = Column(String, nullable=True)
    value_quantity_value = Column(Float, nullable=True)
    value_quantity_unit = Column(String, nullable=True)
    value_quantity_system = Column(String, nullable=True)
    value_quantity_code = Column(String, nullable=True)
    value_reference_type = Column(String, nullable=True)
    value_reference_id = Column(Integer, nullable=True)
    value_reference_display = Column(String, nullable=True)

    item = relationship("QuestionnaireItem", back_populates="initials")
