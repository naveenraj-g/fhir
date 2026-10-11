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
from app.models.plan_definition import columns as col
from app.models.plan_definition.enums import (
    ActionCardinalityBehavior,
    ActionConditionKind,
    ActionGroupingBehavior,
    ActionParticipantType,
    ActionPrecheckBehavior,
    ActionPriority,
    ActionRelationshipType,
    ActionRequiredBehavior,
    ActionSelectionBehavior,
    DataRequirementRole,
    PlanDefinitionContactKind,
    PlanDefinitionGroupReferenceType,
    PlanDefinitionScheduleReferenceType,
    PlanDefinitionStatus,
    PlanDefinitionUseContextReferenceType,
    RelatedArtifactScope,
    RelatedArtifactType,
    SortDirection,
    TriggerType,
)

plan_definition_id_seq = Sequence("plan_definition_pub_seq", start=400000, increment=1, metadata=Base.metadata)

_ALL = "all, delete-orphan"


class PlanDefinitionModel(Base):
    """FHIR R4 PlanDefinition — a pre-defined group of actions to be taken in particular circumstances."""

    __tablename__ = "plan_definition"

    # Internal PK — never exposed
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # Public ID — used in all API responses and FHIR output
    plan_definition_id = Column(
        Integer,
        plan_definition_id_seq,
        server_default=plan_definition_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    user_id = Column(String, nullable=True, index=True)
    org_id = Column(String, nullable=True, index=True)

    # ── Metadata ──────────────────────────────────────────────────────────────
    url = Column(String, nullable=True, index=True)
    version = Column(String, nullable=True, index=True)
    name = Column(String, nullable=True, index=True)
    title = Column(String, nullable=True)
    subtitle = Column(String, nullable=True)
    status = Column(Enum(PlanDefinitionStatus, name="plan_definition_status"), nullable=False, index=True)
    experimental = Column(Boolean, nullable=True)
    date = Column(DateTime(timezone=True), nullable=True, index=True)
    publisher = Column(String, nullable=True)
    description = Column(Text, nullable=True)  # markdown
    purpose = Column(Text, nullable=True)  # markdown
    usage = Column(Text, nullable=True)
    copyright = Column(Text, nullable=True)  # markdown
    approval_date = Column(Date, nullable=True)
    last_review_date = Column(Date, nullable=True)

    # type (0..1 CodeableConcept — order-set | clinical-protocol | eca-rule | workflow-definition)
    locals().update(col.cc("type", index_code=True))

    # subject[x] (0..1 — CodeableConcept | Reference(Group))
    locals().update(col.cc("subject_cc"))
    locals().update(col.reference("subject_reference", PlanDefinitionGroupReferenceType, "plan_definition_group_ref_type"))

    # effectivePeriod (0..1 Period)
    locals().update(col.period("effective_period"))

    # ── Audit ─────────────────────────────────────────────────────────────────
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)

    # ── Child collections (everything is also reachable flat from the plan) ───
    identifiers = relationship("PlanDefinitionIdentifier", back_populates="plan_definition", cascade=_ALL)
    contacts = relationship("PlanDefinitionContact", back_populates="plan_definition", cascade=_ALL)
    use_contexts = relationship("PlanDefinitionUseContext", back_populates="plan_definition", cascade=_ALL)
    jurisdictions = relationship("PlanDefinitionJurisdiction", back_populates="plan_definition", cascade=_ALL)
    topics = relationship("PlanDefinitionTopic", back_populates="plan_definition", cascade=_ALL)
    libraries = relationship("PlanDefinitionLibrary", back_populates="plan_definition", cascade=_ALL)
    related_artifacts = relationship("PlanDefinitionRelatedArtifact", back_populates="plan_definition", cascade=_ALL)
    goals = relationship("PlanDefinitionGoal", back_populates="plan_definition", cascade=_ALL, order_by="PlanDefinitionGoal.id")
    # Every action at every depth, stored flat (tree rebuilt from parent_action_id by the mapper).
    actions = relationship(
        "PlanDefinitionAction", back_populates="plan_definition", cascade=_ALL,
        foreign_keys="PlanDefinitionAction.plan_definition_id", order_by="PlanDefinitionAction.position",
    )
    action_codes = relationship("PlanDefinitionActionCode", back_populates="plan_definition", cascade=_ALL)
    action_goal_ids = relationship("PlanDefinitionActionGoalId", back_populates="plan_definition", cascade=_ALL)
    triggers = relationship("PlanDefinitionActionTrigger", back_populates="plan_definition", cascade=_ALL)
    conditions = relationship("PlanDefinitionActionCondition", back_populates="plan_definition", cascade=_ALL)
    data_requirements = relationship("PlanDefinitionDataRequirement", back_populates="plan_definition", cascade=_ALL)
    related_actions = relationship("PlanDefinitionActionRelatedAction", back_populates="plan_definition", cascade=_ALL)
    participants = relationship("PlanDefinitionActionParticipant", back_populates="plan_definition", cascade=_ALL)
    dynamic_values = relationship("PlanDefinitionActionDynamicValue", back_populates="plan_definition", cascade=_ALL)


def _plan_fk():
    """plan_definition_id FK — a child table pointing at its own parent resource (the only kind of FK we use)."""
    return Column(Integer, ForeignKey("plan_definition.id"), nullable=False, index=True)


# ── Resource-level child tables ────────────────────────────────────────────────


class PlanDefinitionIdentifier(Base):
    """identifier[] — business identifiers."""

    __tablename__ = "plan_definition_identifier"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_definition_id = _plan_fk()
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

    plan_definition = relationship("PlanDefinitionModel", back_populates="identifiers")


class PlanDefinitionContact(Base):
    """contact[] / author[] / editor[] / reviewer[] / endorser[] — ContactDetail, told apart by `kind`."""

    __tablename__ = "plan_definition_contact"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_definition_id = _plan_fk()
    org_id = Column(String, nullable=True)

    kind = Column(Enum(PlanDefinitionContactKind, name="plan_definition_contact_kind"), nullable=False, index=True)
    name = Column(String, nullable=True)

    plan_definition = relationship("PlanDefinitionModel", back_populates="contacts")
    telecoms = relationship("PlanDefinitionContactTelecom", back_populates="contact", cascade=_ALL)


class PlanDefinitionContactTelecom(Base):
    """ContactDetail.telecom[] — ContactPoint."""

    __tablename__ = "plan_definition_contact_telecom"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contact_id = Column(Integer, ForeignKey("plan_definition_contact.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    system = Column(String, nullable=True)
    value = Column(String, nullable=True)
    use = Column(String, nullable=True)
    rank = Column(Integer, nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    contact = relationship("PlanDefinitionContact", back_populates="telecoms")


class PlanDefinitionUseContext(Base):
    """useContext[] — UsageContext: code (Coding) + value[x] (CodeableConcept | Quantity | Range | Reference)."""

    __tablename__ = "plan_definition_use_context"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_definition_id = _plan_fk()
    org_id = Column(String, nullable=True)

    locals().update(col.coding("code"))
    locals().update(col.cc("value_cc"))
    locals().update(col.simple_quantity("value_quantity"))
    locals().update(col.range_("value_range"))
    locals().update(col.reference("value_reference", PlanDefinitionUseContextReferenceType, "plan_definition_use_context_ref_type"))

    plan_definition = relationship("PlanDefinitionModel", back_populates="use_contexts")


class PlanDefinitionJurisdiction(Base):
    """jurisdiction[] — CodeableConcept."""

    __tablename__ = "plan_definition_jurisdiction"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_definition_id = _plan_fk()
    org_id = Column(String, nullable=True)

    coding_system = Column(String, nullable=True)
    coding_code = Column(String, nullable=True, index=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)

    plan_definition = relationship("PlanDefinitionModel", back_populates="jurisdictions")


class PlanDefinitionTopic(Base):
    """topic[] — CodeableConcept."""

    __tablename__ = "plan_definition_topic"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_definition_id = _plan_fk()
    org_id = Column(String, nullable=True)

    coding_system = Column(String, nullable=True)
    coding_code = Column(String, nullable=True, index=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)

    plan_definition = relationship("PlanDefinitionModel", back_populates="topics")


class PlanDefinitionLibrary(Base):
    """library[] — canonical(Library)."""

    __tablename__ = "plan_definition_library"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_definition_id = _plan_fk()
    org_id = Column(String, nullable=True)

    canonical = Column(String, nullable=False, index=True)

    plan_definition = relationship("PlanDefinitionModel", back_populates="libraries")


class PlanDefinitionRelatedArtifact(Base):
    """
    RelatedArtifact — used by relatedArtifact[] (scope=plan), goal.documentation[] (scope=goal) and
    action.documentation[] (scope=action). goal_id / action_id are the row's own parent (child→parent FK).
    """

    __tablename__ = "plan_definition_related_artifact"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_definition_id = _plan_fk()
    goal_id = Column(Integer, ForeignKey("plan_definition_goal.id"), nullable=True, index=True)
    action_id = Column(Integer, ForeignKey("plan_definition_action.id"), nullable=True, index=True)
    org_id = Column(String, nullable=True)

    scope = Column(Enum(RelatedArtifactScope, name="plan_definition_related_artifact_scope"), nullable=False)
    type = Column(Enum(RelatedArtifactType, name="plan_definition_related_artifact_type"), nullable=False, index=True)
    label = Column(String, nullable=True)
    display = Column(String, nullable=True)
    citation = Column(Text, nullable=True)  # markdown
    url = Column(String, nullable=True)
    locals().update(col.attachment("document"))
    resource = Column(String, nullable=True, index=True)  # canonical(Any)

    plan_definition = relationship("PlanDefinitionModel", back_populates="related_artifacts")
    goal = relationship("PlanDefinitionGoal", back_populates="documentation", foreign_keys=[goal_id])
    action = relationship("PlanDefinitionAction", back_populates="documentation", foreign_keys=[action_id])


# ── goal ───────────────────────────────────────────────────────────────────────


class PlanDefinitionGoal(Base):
    """goal[] BackboneElement."""

    __tablename__ = "plan_definition_goal"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_definition_id = _plan_fk()
    org_id = Column(String, nullable=True)

    element_id = Column(String, nullable=True, index=True)  # Element.id — action.goalId points at it

    locals().update(col.cc("category"))
    locals().update(col.cc("description", index_code=True))  # 1..1
    locals().update(col.cc("priority"))
    locals().update(col.cc("start"))

    plan_definition = relationship("PlanDefinitionModel", back_populates="goals")
    addresses = relationship("PlanDefinitionGoalAddress", back_populates="goal", cascade=_ALL)
    targets = relationship("PlanDefinitionGoalTarget", back_populates="goal", cascade=_ALL)
    documentation = relationship(
        "PlanDefinitionRelatedArtifact", back_populates="goal", cascade=_ALL, foreign_keys="PlanDefinitionRelatedArtifact.goal_id"
    )


class PlanDefinitionGoalAddress(Base):
    """goal.addresses[] — CodeableConcept."""

    __tablename__ = "plan_definition_goal_address"

    id = Column(Integer, primary_key=True, autoincrement=True)
    goal_id = Column(Integer, ForeignKey("plan_definition_goal.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    coding_system = Column(String, nullable=True)
    coding_code = Column(String, nullable=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)

    goal = relationship("PlanDefinitionGoal", back_populates="addresses")


class PlanDefinitionGoalTarget(Base):
    """goal.target[] — measure + detail[x] (Quantity | Range | CodeableConcept) + due (Duration)."""

    __tablename__ = "plan_definition_goal_target"

    id = Column(Integer, primary_key=True, autoincrement=True)
    goal_id = Column(Integer, ForeignKey("plan_definition_goal.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    locals().update(col.cc("measure", index_code=True))
    locals().update(col.quantity("detail_quantity"))
    locals().update(col.range_("detail_range"))
    locals().update(col.cc("detail_cc"))
    locals().update(col.quantity("due"))

    goal = relationship("PlanDefinitionGoal", back_populates="targets")


# ── action (recursive, stored flat) ─────────────────────────────────────────────


class PlanDefinitionAction(Base):
    """
    action[] BackboneElement, at every depth. Nested actions are rows pointing at their parent through
    parent_action_id; every row also carries plan_definition_id so the whole tree loads in one query.
    """

    __tablename__ = "plan_definition_action"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    plan_definition_id = _plan_fk()
    parent_action_id = Column(Integer, ForeignKey("plan_definition_action.id"), nullable=True, index=True)
    org_id = Column(String, nullable=True)

    position = Column(Integer, nullable=False, default=0)  # global depth-first order
    element_id = Column(String, nullable=True, index=True)  # Element.id — relatedAction.actionId points at it

    prefix = Column(String, nullable=True)
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    text_equivalent = Column(Text, nullable=True)
    priority = Column(Enum(ActionPriority, name="plan_definition_action_priority"), nullable=True)

    # subject[x] (0..1 — CodeableConcept | Reference(Group))
    locals().update(col.cc("subject_cc"))
    locals().update(col.reference("subject_reference", PlanDefinitionGroupReferenceType, "plan_definition_group_ref_type"))

    # timing[x] (0..1 — dateTime | Age | Period | Duration | Range | Timing)
    timing_datetime = Column(DateTime(timezone=True), nullable=True)
    locals().update(col.quantity("timing_age"))
    locals().update(col.period("timing_period"))
    locals().update(col.quantity("timing_duration"))
    locals().update(col.range_("timing_range"))
    locals().update(col.timing("timing_timing"))

    # type (0..1 CodeableConcept — create | update | remove | fire-event)
    locals().update(col.cc("type", index_code=True))

    grouping_behavior = Column(Enum(ActionGroupingBehavior, name="plan_definition_grouping_behavior"), nullable=True)
    selection_behavior = Column(Enum(ActionSelectionBehavior, name="plan_definition_selection_behavior"), nullable=True)
    required_behavior = Column(Enum(ActionRequiredBehavior, name="plan_definition_required_behavior"), nullable=True)
    precheck_behavior = Column(Enum(ActionPrecheckBehavior, name="plan_definition_precheck_behavior"), nullable=True)
    cardinality_behavior = Column(Enum(ActionCardinalityBehavior, name="plan_definition_cardinality_behavior"), nullable=True)

    # definition[x] (0..1 — canonical(ActivityDefinition | PlanDefinition | Questionnaire) | uri)
    definition_canonical = Column(String, nullable=True, index=True)
    definition_uri = Column(String, nullable=True, index=True)
    transform = Column(String, nullable=True)  # canonical(StructureMap)

    plan_definition = relationship("PlanDefinitionModel", back_populates="actions", foreign_keys=[plan_definition_id])
    parent = relationship("PlanDefinitionAction", back_populates="sub_actions", remote_side="PlanDefinitionAction.id", foreign_keys=[parent_action_id])
    sub_actions = relationship("PlanDefinitionAction", back_populates="parent", cascade=_ALL, foreign_keys=[parent_action_id])

    codes = relationship("PlanDefinitionActionCode", back_populates="action", cascade=_ALL)
    goal_ids = relationship("PlanDefinitionActionGoalId", back_populates="action", cascade=_ALL)
    documentation = relationship(
        "PlanDefinitionRelatedArtifact", back_populates="action", cascade=_ALL, foreign_keys="PlanDefinitionRelatedArtifact.action_id"
    )
    triggers = relationship("PlanDefinitionActionTrigger", back_populates="action", cascade=_ALL)
    conditions = relationship("PlanDefinitionActionCondition", back_populates="action", cascade=_ALL)
    data_requirements = relationship(
        "PlanDefinitionDataRequirement", back_populates="action", cascade=_ALL, foreign_keys="PlanDefinitionDataRequirement.action_id"
    )
    related_actions = relationship("PlanDefinitionActionRelatedAction", back_populates="action", cascade=_ALL)
    participants = relationship("PlanDefinitionActionParticipant", back_populates="action", cascade=_ALL)
    dynamic_values = relationship("PlanDefinitionActionDynamicValue", back_populates="action", cascade=_ALL)


def _action_fk():
    return Column(Integer, ForeignKey("plan_definition_action.id"), nullable=False, index=True)


class PlanDefinitionActionCode(Base):
    """action.code[] (kind=code) and action.reason[] (kind=reason) — CodeableConcept."""

    __tablename__ = "plan_definition_action_code"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_definition_id = _plan_fk()
    action_id = _action_fk()
    org_id = Column(String, nullable=True)

    kind = Column(String, nullable=False, index=True)  # "code" | "reason"
    coding_system = Column(String, nullable=True)
    coding_code = Column(String, nullable=True, index=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)

    plan_definition = relationship("PlanDefinitionModel", back_populates="action_codes")
    action = relationship("PlanDefinitionAction", back_populates="codes")


class PlanDefinitionActionGoalId(Base):
    """action.goalId[] — id of a goal this action addresses."""

    __tablename__ = "plan_definition_action_goal_id"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_definition_id = _plan_fk()
    action_id = _action_fk()
    org_id = Column(String, nullable=True)

    goal_element_id = Column(String, nullable=False)

    plan_definition = relationship("PlanDefinitionModel", back_populates="action_goal_ids")
    action = relationship("PlanDefinitionAction", back_populates="goal_ids")


class PlanDefinitionActionTrigger(Base):
    """action.trigger[] — TriggerDefinition (type, name, timing[x], condition; data[] lives in data_requirement)."""

    __tablename__ = "plan_definition_action_trigger"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_definition_id = _plan_fk()
    action_id = _action_fk()
    org_id = Column(String, nullable=True)

    type = Column(Enum(TriggerType, name="plan_definition_trigger_type"), nullable=False)
    name = Column(String, nullable=True)

    # timing[x] (0..1 — Timing | Reference(Schedule) | date | dateTime)
    locals().update(col.timing("timing_timing"))
    locals().update(col.reference("timing_reference", PlanDefinitionScheduleReferenceType, "plan_definition_schedule_ref_type"))
    timing_date = Column(Date, nullable=True)
    timing_datetime = Column(DateTime(timezone=True), nullable=True)

    # condition (0..1 Expression)
    locals().update(col.expression("condition"))

    plan_definition = relationship("PlanDefinitionModel", back_populates="triggers")
    action = relationship("PlanDefinitionAction", back_populates="triggers")
    data = relationship(
        "PlanDefinitionDataRequirement", back_populates="trigger", cascade=_ALL, foreign_keys="PlanDefinitionDataRequirement.trigger_id"
    )


class PlanDefinitionActionCondition(Base):
    """action.condition[] — kind + Expression."""

    __tablename__ = "plan_definition_action_condition"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_definition_id = _plan_fk()
    action_id = _action_fk()
    org_id = Column(String, nullable=True)

    kind = Column(Enum(ActionConditionKind, name="plan_definition_condition_kind"), nullable=False)
    locals().update(col.expression("expression"))

    plan_definition = relationship("PlanDefinitionModel", back_populates="conditions")
    action = relationship("PlanDefinitionAction", back_populates="conditions")


class PlanDefinitionDataRequirement(Base):
    """
    DataRequirement — action.input[] (role=input), action.output[] (role=output) and
    trigger.data[] (role=trigger). profile[] and mustSupport[] are comma-separated Text (never filtered).
    """

    __tablename__ = "plan_definition_data_requirement"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_definition_id = _plan_fk()
    action_id = Column(Integer, ForeignKey("plan_definition_action.id"), nullable=True, index=True)
    trigger_id = Column(Integer, ForeignKey("plan_definition_action_trigger.id"), nullable=True, index=True)
    org_id = Column(String, nullable=True)

    role = Column(Enum(DataRequirementRole, name="plan_definition_dr_role"), nullable=False)
    type = Column(String, nullable=False)  # FHIRAllTypes code
    profile = Column(Text, nullable=True)
    must_support = Column(Text, nullable=True)
    limit = Column(Integer, nullable=True)
    locals().update(col.cc("subject_cc"))
    locals().update(col.reference("subject_reference", PlanDefinitionGroupReferenceType, "plan_definition_group_ref_type"))

    plan_definition = relationship("PlanDefinitionModel", back_populates="data_requirements")
    action = relationship("PlanDefinitionAction", back_populates="data_requirements", foreign_keys=[action_id])
    trigger = relationship("PlanDefinitionActionTrigger", back_populates="data", foreign_keys=[trigger_id])
    code_filters = relationship("PlanDefinitionDataRequirementCodeFilter", back_populates="data_requirement", cascade=_ALL)
    date_filters = relationship("PlanDefinitionDataRequirementDateFilter", back_populates="data_requirement", cascade=_ALL)
    sorts = relationship("PlanDefinitionDataRequirementSort", back_populates="data_requirement", cascade=_ALL)


class PlanDefinitionDataRequirementCodeFilter(Base):
    """DataRequirement.codeFilter[] (path xor searchParam)."""

    __tablename__ = "plan_definition_dr_code_filter"

    id = Column(Integer, primary_key=True, autoincrement=True)
    data_requirement_id = Column(Integer, ForeignKey("plan_definition_data_requirement.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    path = Column(String, nullable=True)
    search_param = Column(String, nullable=True)
    value_set = Column(String, nullable=True)  # canonical(ValueSet)

    data_requirement = relationship("PlanDefinitionDataRequirement", back_populates="code_filters")
    codes = relationship("PlanDefinitionDataRequirementCodeFilterCode", back_populates="code_filter", cascade=_ALL)


class PlanDefinitionDataRequirementCodeFilterCode(Base):
    """DataRequirement.codeFilter.code[] — Coding."""

    __tablename__ = "plan_definition_dr_code_filter_code"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code_filter_id = Column(Integer, ForeignKey("plan_definition_dr_code_filter.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    system = Column(String, nullable=True)
    code = Column(String, nullable=True)
    display = Column(String, nullable=True)

    code_filter = relationship("PlanDefinitionDataRequirementCodeFilter", back_populates="codes")


class PlanDefinitionDataRequirementDateFilter(Base):
    """DataRequirement.dateFilter[] — path xor searchParam + value[x] (dateTime | Period | Duration)."""

    __tablename__ = "plan_definition_dr_date_filter"

    id = Column(Integer, primary_key=True, autoincrement=True)
    data_requirement_id = Column(Integer, ForeignKey("plan_definition_data_requirement.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    path = Column(String, nullable=True)
    search_param = Column(String, nullable=True)
    value_datetime = Column(DateTime(timezone=True), nullable=True)
    locals().update(col.period("value_period"))
    locals().update(col.quantity("value_duration"))

    data_requirement = relationship("PlanDefinitionDataRequirement", back_populates="date_filters")


class PlanDefinitionDataRequirementSort(Base):
    """DataRequirement.sort[] — path + direction."""

    __tablename__ = "plan_definition_dr_sort"

    id = Column(Integer, primary_key=True, autoincrement=True)
    data_requirement_id = Column(Integer, ForeignKey("plan_definition_data_requirement.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    path = Column(String, nullable=False)
    direction = Column(Enum(SortDirection, name="plan_definition_sort_direction"), nullable=False)

    data_requirement = relationship("PlanDefinitionDataRequirement", back_populates="sorts")


class PlanDefinitionActionRelatedAction(Base):
    """action.relatedAction[] — actionId, relationship, offset[x] (Duration | Range)."""

    __tablename__ = "plan_definition_action_related_action"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_definition_id = _plan_fk()
    action_id = _action_fk()
    org_id = Column(String, nullable=True)

    related_action_id = Column(String, nullable=False)  # Element.id of the related action
    relationship_type = Column(Enum(ActionRelationshipType, name="plan_definition_relationship_type"), nullable=False)
    locals().update(col.quantity("offset_duration"))
    locals().update(col.range_("offset_range"))

    plan_definition = relationship("PlanDefinitionModel", back_populates="related_actions")
    action = relationship("PlanDefinitionAction", back_populates="related_actions")


class PlanDefinitionActionParticipant(Base):
    """action.participant[] — type + role."""

    __tablename__ = "plan_definition_action_participant"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_definition_id = _plan_fk()
    action_id = _action_fk()
    org_id = Column(String, nullable=True)

    type = Column(Enum(ActionParticipantType, name="plan_definition_participant_type"), nullable=False)
    locals().update(col.cc("role"))

    plan_definition = relationship("PlanDefinitionModel", back_populates="participants")
    action = relationship("PlanDefinitionAction", back_populates="participants")


class PlanDefinitionActionDynamicValue(Base):
    """action.dynamicValue[] — path + Expression."""

    __tablename__ = "plan_definition_action_dynamic_value"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_definition_id = _plan_fk()
    action_id = _action_fk()
    org_id = Column(String, nullable=True)

    path = Column(String, nullable=True)
    locals().update(col.expression("expression"))

    plan_definition = relationship("PlanDefinitionModel", back_populates="dynamic_values")
    action = relationship("PlanDefinitionAction", back_populates="dynamic_values")
