from enum import Enum


class PlanDefinitionStatus(str, Enum):
    """FHIR R4 PublicationStatus (PlanDefinition.status, required binding)."""

    draft = "draft"
    active = "active"
    retired = "retired"
    unknown = "unknown"


class PlanDefinitionGroupReferenceType(str, Enum):
    """Allowed reference type for subject[x] Reference(Group) (PlanDefinition.subject / action.subject / DataRequirement.subject)."""

    Group = "Group"


class PlanDefinitionScheduleReferenceType(str, Enum):
    """Allowed reference type for TriggerDefinition.timing[x] Reference(Schedule)."""

    Schedule = "Schedule"


class PlanDefinitionUseContextReferenceType(str, Enum):
    """Allowed reference types for UsageContext.valueReference (R4)."""

    PlanDefinition = "PlanDefinition"
    ResearchStudy = "ResearchStudy"
    InsurancePlan = "InsurancePlan"
    HealthcareService = "HealthcareService"
    Group = "Group"
    Location = "Location"
    Organization = "Organization"


class PlanDefinitionContactKind(str, Enum):
    """Which ContactDetail[] list a contact row belongs to."""

    contact = "contact"
    author = "author"
    editor = "editor"
    reviewer = "reviewer"
    endorser = "endorser"


class RelatedArtifactType(str, Enum):
    """FHIR R4 RelatedArtifactType value set."""

    documentation = "documentation"
    justification = "justification"
    citation = "citation"
    predecessor = "predecessor"
    successor = "successor"
    derived_from = "derived-from"
    depends_on = "depends-on"
    composed_of = "composed-of"


class RelatedArtifactScope(str, Enum):
    """Which element a RelatedArtifact row hangs off."""

    plan = "plan"
    goal = "goal"
    action = "action"


class ActionPriority(str, Enum):
    """FHIR R4 RequestPriority (action.priority)."""

    routine = "routine"
    urgent = "urgent"
    asap = "asap"
    stat = "stat"


class ActionConditionKind(str, Enum):
    """FHIR R4 ActionConditionKind (action.condition.kind)."""

    applicability = "applicability"
    start = "start"
    stop = "stop"


class ActionRelationshipType(str, Enum):
    """FHIR R4 ActionRelationshipType (action.relatedAction.relationship)."""

    before_start = "before-start"
    before = "before"
    before_end = "before-end"
    concurrent_with_start = "concurrent-with-start"
    concurrent = "concurrent"
    concurrent_with_end = "concurrent-with-end"
    after_start = "after-start"
    after = "after"
    after_end = "after-end"


class ActionParticipantType(str, Enum):
    """FHIR R4 ActionParticipantType (action.participant.type)."""

    patient = "patient"
    practitioner = "practitioner"
    related_person = "related-person"
    device = "device"


class ActionGroupingBehavior(str, Enum):
    """FHIR R4 ActionGroupingBehavior."""

    visual_group = "visual-group"
    logical_group = "logical-group"
    sentence_group = "sentence-group"


class ActionSelectionBehavior(str, Enum):
    """FHIR R4 ActionSelectionBehavior."""

    any = "any"
    all = "all"
    all_or_none = "all-or-none"
    exactly_one = "exactly-one"
    at_most_one = "at-most-one"
    one_or_more = "one-or-more"


class ActionRequiredBehavior(str, Enum):
    """FHIR R4 ActionRequiredBehavior."""

    must = "must"
    could = "could"
    must_unless_documented = "must-unless-documented"


class ActionPrecheckBehavior(str, Enum):
    """FHIR R4 ActionPrecheckBehavior."""

    yes = "yes"
    no = "no"


class ActionCardinalityBehavior(str, Enum):
    """FHIR R4 ActionCardinalityBehavior."""

    single = "single"
    multiple = "multiple"


class TriggerType(str, Enum):
    """FHIR R4 TriggerType (TriggerDefinition.type)."""

    named_event = "named-event"
    periodic = "periodic"
    data_changed = "data-changed"
    data_added = "data-added"
    data_modified = "data-modified"
    data_removed = "data-removed"
    data_accessed = "data-accessed"
    data_access_ended = "data-access-ended"


class DataRequirementRole(str, Enum):
    """Where a DataRequirement row lives: action.input, action.output or trigger.data."""

    input = "input"
    output = "output"
    trigger = "trigger"


class SortDirection(str, Enum):
    """FHIR R4 SortDirection (DataRequirement.sort.direction)."""

    ascending = "ascending"
    descending = "descending"
