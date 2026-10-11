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
from app.models.activity_definition.enums import (
    ActionParticipantType,
    ActionPriority,
    ActivityDefinitionIntent,
    ActivityDefinitionKind,
    ActivityDefinitionLocationReferenceType,
    ActivityDefinitionObservationReferenceType,
    ActivityDefinitionProductReferenceType,
    ActivityDefinitionSpecimenReferenceType,
    PlanDefinitionContactKind,
    PlanDefinitionGroupReferenceType,
    PlanDefinitionStatus,
    PlanDefinitionUseContextReferenceType,
    RelatedArtifactType,
)
from app.models.plan_definition import columns as col

activity_definition_id_seq = Sequence("activity_definition_pub_seq", start=410000, increment=1, metadata=Base.metadata)

_ALL = "all, delete-orphan"


class ActivityDefinitionModel(Base):
    """FHIR R4 ActivityDefinition — the definition of an action to be performed (a request template)."""

    __tablename__ = "activity_definition"

    # Internal PK — never exposed
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # Public ID — used in all API responses and FHIR output
    activity_definition_id = Column(
        Integer,
        activity_definition_id_seq,
        server_default=activity_definition_id_seq.next_value(),
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
    status = Column(Enum(PlanDefinitionStatus, name="activity_definition_status"), nullable=False, index=True)
    experimental = Column(Boolean, nullable=True)
    date = Column(DateTime(timezone=True), nullable=True, index=True)
    publisher = Column(String, nullable=True)
    description = Column(Text, nullable=True)  # markdown
    purpose = Column(Text, nullable=True)  # markdown
    usage = Column(Text, nullable=True)
    copyright = Column(Text, nullable=True)  # markdown
    approval_date = Column(Date, nullable=True)
    last_review_date = Column(Date, nullable=True)

    # subject[x] (0..1 — CodeableConcept | Reference(Group))
    locals().update(col.cc("subject_cc"))
    locals().update(col.reference("subject_reference", PlanDefinitionGroupReferenceType, "activity_definition_group_ref_type"))

    # effectivePeriod (0..1 Period)
    locals().update(col.period("effective_period"))

    # ── Definition of the activity ────────────────────────────────────────────
    kind = Column(Enum(ActivityDefinitionKind, name="activity_definition_kind"), nullable=True, index=True)
    profile = Column(String, nullable=True)  # canonical(StructureDefinition)
    locals().update(col.cc("code", index_code=True))
    intent = Column(Enum(ActivityDefinitionIntent, name="activity_definition_intent"), nullable=True, index=True)
    priority = Column(Enum(ActionPriority, name="activity_definition_priority"), nullable=True)
    do_not_perform = Column(Boolean, nullable=True)

    # timing[x] (0..1 — Timing | dateTime | Age | Period | Range | Duration)
    timing_datetime = Column(DateTime(timezone=True), nullable=True)
    locals().update(col.quantity("timing_age"))
    locals().update(col.period("timing_period"))
    locals().update(col.range_("timing_range"))
    locals().update(col.quantity("timing_duration"))
    locals().update(col.timing("timing_timing"))

    # location (0..1 Reference(Location))
    locals().update(col.reference("location", ActivityDefinitionLocationReferenceType, "activity_definition_location_ref_type"))

    # product[x] (0..1 — Reference(Medication | Substance) | CodeableConcept)
    locals().update(col.reference("product_reference", ActivityDefinitionProductReferenceType, "activity_definition_product_ref_type"))
    locals().update(col.cc("product_cc"))

    # quantity (0..1 SimpleQuantity)
    locals().update(col.simple_quantity("quantity"))

    transform = Column(String, nullable=True)  # canonical(StructureMap)

    # ── Audit ─────────────────────────────────────────────────────────────────
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)

    # ── Child collections ─────────────────────────────────────────────────────
    identifiers = relationship("ActivityDefinitionIdentifier", back_populates="activity_definition", cascade=_ALL)
    contacts = relationship("ActivityDefinitionContact", back_populates="activity_definition", cascade=_ALL)
    use_contexts = relationship("ActivityDefinitionUseContext", back_populates="activity_definition", cascade=_ALL)
    jurisdictions = relationship("ActivityDefinitionJurisdiction", back_populates="activity_definition", cascade=_ALL)
    topics = relationship("ActivityDefinitionTopic", back_populates="activity_definition", cascade=_ALL)
    related_artifacts = relationship("ActivityDefinitionRelatedArtifact", back_populates="activity_definition", cascade=_ALL)
    libraries = relationship("ActivityDefinitionLibrary", back_populates="activity_definition", cascade=_ALL)
    participants = relationship("ActivityDefinitionParticipant", back_populates="activity_definition", cascade=_ALL)
    dosages = relationship(
        "ActivityDefinitionDosage", back_populates="activity_definition", cascade=_ALL, order_by="ActivityDefinitionDosage.id"
    )
    body_sites = relationship("ActivityDefinitionBodySite", back_populates="activity_definition", cascade=_ALL)
    specimen_requirements = relationship("ActivityDefinitionSpecimenRequirement", back_populates="activity_definition", cascade=_ALL)
    observation_requirements = relationship("ActivityDefinitionObservationRequirement", back_populates="activity_definition", cascade=_ALL)
    observation_result_requirements = relationship(
        "ActivityDefinitionObservationResultRequirement", back_populates="activity_definition", cascade=_ALL
    )
    dynamic_values = relationship("ActivityDefinitionDynamicValue", back_populates="activity_definition", cascade=_ALL)


def _fk():
    """activity_definition_id FK — a child table pointing at its own parent resource (the only kind of FK we use)."""
    return Column(Integer, ForeignKey("activity_definition.id"), nullable=False, index=True)




# ── Resource-level child tables ────────────────────────────────────────────────


class ActivityDefinitionIdentifier(Base):
    """identifier[] — business identifiers."""

    __tablename__ = "activity_definition_identifier"

    id = Column(Integer, primary_key=True, autoincrement=True)
    activity_definition_id = _fk()
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

    activity_definition = relationship("ActivityDefinitionModel", back_populates="identifiers")


class ActivityDefinitionContact(Base):
    """contact[] / author[] / editor[] / reviewer[] / endorser[] — ContactDetail, told apart by `kind`."""

    __tablename__ = "activity_definition_contact"

    id = Column(Integer, primary_key=True, autoincrement=True)
    activity_definition_id = _fk()
    org_id = Column(String, nullable=True)

    kind = Column(Enum(PlanDefinitionContactKind, name="activity_definition_contact_kind"), nullable=False, index=True)
    name = Column(String, nullable=True)

    activity_definition = relationship("ActivityDefinitionModel", back_populates="contacts")
    telecoms = relationship("ActivityDefinitionContactTelecom", back_populates="contact", cascade=_ALL)


class ActivityDefinitionContactTelecom(Base):
    """ContactDetail.telecom[] — ContactPoint."""

    __tablename__ = "activity_definition_contact_telecom"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contact_id = Column(Integer, ForeignKey("activity_definition_contact.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    system = Column(String, nullable=True)
    value = Column(String, nullable=True)
    use = Column(String, nullable=True)
    rank = Column(Integer, nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    contact = relationship("ActivityDefinitionContact", back_populates="telecoms")


class ActivityDefinitionUseContext(Base):
    """useContext[] — UsageContext: code (Coding) + value[x] (CodeableConcept | Quantity | Range | Reference)."""

    __tablename__ = "activity_definition_use_context"

    id = Column(Integer, primary_key=True, autoincrement=True)
    activity_definition_id = _fk()
    org_id = Column(String, nullable=True)

    locals().update(col.coding("code"))
    locals().update(col.cc("value_cc"))
    locals().update(col.simple_quantity("value_quantity"))
    locals().update(col.range_("value_range"))
    locals().update(
        col.reference("value_reference", PlanDefinitionUseContextReferenceType, "activity_definition_use_context_ref_type")
    )

    activity_definition = relationship("ActivityDefinitionModel", back_populates="use_contexts")


class ActivityDefinitionJurisdiction(Base):
    """jurisdiction[] — CodeableConcept."""

    __tablename__ = "activity_definition_jurisdiction"

    id = Column(Integer, primary_key=True, autoincrement=True)
    activity_definition_id = _fk()
    org_id = Column(String, nullable=True)

    coding_system = Column(String, nullable=True)
    coding_code = Column(String, nullable=True, index=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)

    activity_definition = relationship("ActivityDefinitionModel", back_populates="jurisdictions")


class ActivityDefinitionTopic(Base):
    """topic[] — CodeableConcept."""

    __tablename__ = "activity_definition_topic"

    id = Column(Integer, primary_key=True, autoincrement=True)
    activity_definition_id = _fk()
    org_id = Column(String, nullable=True)

    coding_system = Column(String, nullable=True)
    coding_code = Column(String, nullable=True, index=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)

    activity_definition = relationship("ActivityDefinitionModel", back_populates="topics")


class ActivityDefinitionBodySite(Base):
    """bodySite[] — CodeableConcept."""

    __tablename__ = "activity_definition_body_site"

    id = Column(Integer, primary_key=True, autoincrement=True)
    activity_definition_id = _fk()
    org_id = Column(String, nullable=True)

    coding_system = Column(String, nullable=True)
    coding_code = Column(String, nullable=True, index=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)

    activity_definition = relationship("ActivityDefinitionModel", back_populates="body_sites")


class ActivityDefinitionLibrary(Base):
    """library[] — canonical(Library)."""

    __tablename__ = "activity_definition_library"

    id = Column(Integer, primary_key=True, autoincrement=True)
    activity_definition_id = _fk()
    org_id = Column(String, nullable=True)

    canonical = Column(String, nullable=False, index=True)

    activity_definition = relationship("ActivityDefinitionModel", back_populates="libraries")


class ActivityDefinitionRelatedArtifact(Base):
    """relatedArtifact[] — RelatedArtifact."""

    __tablename__ = "activity_definition_related_artifact"

    id = Column(Integer, primary_key=True, autoincrement=True)
    activity_definition_id = _fk()
    org_id = Column(String, nullable=True)

    type = Column(Enum(RelatedArtifactType, name="activity_definition_related_artifact_type"), nullable=False, index=True)
    label = Column(String, nullable=True)
    display = Column(String, nullable=True)
    citation = Column(Text, nullable=True)  # markdown
    url = Column(String, nullable=True)
    locals().update(col.attachment("document"))
    resource = Column(String, nullable=True, index=True)  # canonical(Any)

    activity_definition = relationship("ActivityDefinitionModel", back_populates="related_artifacts")


class ActivityDefinitionParticipant(Base):
    """participant[] — type + role."""

    __tablename__ = "activity_definition_participant"

    id = Column(Integer, primary_key=True, autoincrement=True)
    activity_definition_id = _fk()
    org_id = Column(String, nullable=True)

    type = Column(Enum(ActionParticipantType, name="activity_definition_participant_type"), nullable=False)
    locals().update(col.cc("role"))

    activity_definition = relationship("ActivityDefinitionModel", back_populates="participants")


class ActivityDefinitionSpecimenRequirement(Base):
    """specimenRequirement[] — Reference(SpecimenDefinition)."""

    __tablename__ = "activity_definition_specimen_requirement"

    id = Column(Integer, primary_key=True, autoincrement=True)
    activity_definition_id = _fk()
    org_id = Column(String, nullable=True)

    reference_type = Column(
        Enum(ActivityDefinitionSpecimenReferenceType, name="activity_definition_specimen_ref_type"), nullable=True
    )
    reference_id = Column(Integer, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    activity_definition = relationship("ActivityDefinitionModel", back_populates="specimen_requirements")


class ActivityDefinitionObservationRequirement(Base):
    """observationRequirement[] — Reference(ObservationDefinition)."""

    __tablename__ = "activity_definition_observation_requirement"

    id = Column(Integer, primary_key=True, autoincrement=True)
    activity_definition_id = _fk()
    org_id = Column(String, nullable=True)

    reference_type = Column(
        Enum(ActivityDefinitionObservationReferenceType, name="activity_definition_observation_ref_type"), nullable=True
    )
    reference_id = Column(Integer, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    activity_definition = relationship("ActivityDefinitionModel", back_populates="observation_requirements")


class ActivityDefinitionObservationResultRequirement(Base):
    """observationResultRequirement[] — Reference(ObservationDefinition)."""

    __tablename__ = "activity_definition_observation_result_requirement"

    id = Column(Integer, primary_key=True, autoincrement=True)
    activity_definition_id = _fk()
    org_id = Column(String, nullable=True)

    reference_type = Column(
        Enum(ActivityDefinitionObservationReferenceType, name="activity_definition_observation_ref_type", create_type=False),
        nullable=True,
    )
    reference_id = Column(Integer, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    activity_definition = relationship("ActivityDefinitionModel", back_populates="observation_result_requirements")


class ActivityDefinitionDynamicValue(Base):
    """dynamicValue[] — path + Expression."""

    __tablename__ = "activity_definition_dynamic_value"

    id = Column(Integer, primary_key=True, autoincrement=True)
    activity_definition_id = _fk()
    org_id = Column(String, nullable=True)

    path = Column(String, nullable=True)
    locals().update(col.expression("expression"))

    activity_definition = relationship("ActivityDefinitionModel", back_populates="dynamic_values")


# ── dosage[] (Dosage datatype) ─────────────────────────────────────────────────


class ActivityDefinitionDosage(Base):
    """dosage[] — Dosage datatype (the full R4 element set)."""

    __tablename__ = "activity_definition_dosage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    activity_definition_id = _fk()
    org_id = Column(String, nullable=True)

    sequence = Column(Integer, nullable=True)
    text = Column(Text, nullable=True)
    patient_instruction = Column(Text, nullable=True)

    # timing (0..1 Timing)
    locals().update(col.timing("timing"))

    # asNeeded[x] (boolean | CodeableConcept)
    as_needed_boolean = Column(Boolean, nullable=True)
    locals().update(col.cc("as_needed"))

    locals().update(col.cc("site"))
    locals().update(col.cc("route"))
    locals().update(col.cc("method"))

    # maxDosePerPeriod (Ratio), maxDosePerAdministration / maxDosePerLifetime (SimpleQuantity)
    locals().update(col.ratio("max_dose_per_period"))
    locals().update(col.simple_quantity("max_dose_per_administration"))
    locals().update(col.simple_quantity("max_dose_per_lifetime"))

    activity_definition = relationship("ActivityDefinitionModel", back_populates="dosages")
    additional_instructions = relationship("ActivityDefinitionDosageAdditionalInstruction", back_populates="dosage", cascade=_ALL)
    dose_and_rates = relationship("ActivityDefinitionDosageDoseAndRate", back_populates="dosage", cascade=_ALL)


class ActivityDefinitionDosageAdditionalInstruction(Base):
    """dosage.additionalInstruction[] — CodeableConcept."""

    __tablename__ = "activity_definition_dosage_additional_instruction"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dosage_id = Column(Integer, ForeignKey("activity_definition_dosage.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    coding_system = Column(String, nullable=True)
    coding_code = Column(String, nullable=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)

    dosage = relationship("ActivityDefinitionDosage", back_populates="additional_instructions")


class ActivityDefinitionDosageDoseAndRate(Base):
    """dosage.doseAndRate[] — type + dose[x] (Range | SimpleQuantity) + rate[x] (Ratio | Range | SimpleQuantity)."""

    __tablename__ = "activity_definition_dosage_dose_and_rate"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dosage_id = Column(Integer, ForeignKey("activity_definition_dosage.id"), nullable=False, index=True)
    org_id = Column(String, nullable=True)

    locals().update(col.cc("type"))
    locals().update(col.range_("dose_range"))
    locals().update(col.simple_quantity("dose_quantity"))
    locals().update(col.ratio("rate_ratio"))
    locals().update(col.range_("rate_range"))
    locals().update(col.simple_quantity("rate_quantity"))

    dosage = relationship("ActivityDefinitionDosage", back_populates="dose_and_rates")
