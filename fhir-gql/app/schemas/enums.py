"""
FHIR-aligned enumeration types used across resource schemas.

Each enum maps directly to a code set defined in the FHIR R4 specification
(https://hl7.org/fhir/R4/). Using str-based enums (str, Enum) means the values
serialise to their string codes in JSON bodies automatically, which is what the
FHIR Server expects. Pydantic validates incoming strings against these enums during
request deserialisation so invalid codes are rejected with a 422 before reaching
the service layer.

Reference: https://hl7.org/fhir/R4/valueset-identifier-use.html and related pages.
"""

from enum import Enum


class IdentifierUse(str, Enum):
    """
    FHIR Identifier.use — describes the purpose of an identifier attached to a resource.

    Values defined by https://hl7.org/fhir/R4/valueset-identifier-use.html:
      usual     — the identifier recommended for display and use in real-world contact.
      official  — the 'official' identifier assigned by an authoritative body.
      temp      — a temporary identifier assigned during registration or interim use.
      secondary — an identifier that was assigned in secondary use (e.g. a visit number).
      old       — the identifier is no longer in use.
    """

    usual = "usual"
    official = "official"
    temp = "temp"
    secondary = "secondary"
    old = "old"


class ContactPointSystem(str, Enum):
    """
    FHIR ContactPoint.system — the technology or protocol behind a contact point.

    Values defined by https://hl7.org/fhir/R4/valueset-contact-point-system.html:
      phone  — a voice telephone number.
      fax    — a fax machine number.
      email  — an email address.
      pager  — a pager number.
      url    — a URL — typically a website or SMART-on-FHIR endpoint.
      sms    — a contact that can be reached by SMS text message.
      other  — a contact value using a technology not covered by the above codes.
    """

    phone = "phone"
    fax = "fax"
    email = "email"
    pager = "pager"
    url = "url"
    sms = "sms"
    other = "other"


class ContactPointUse(str, Enum):
    """
    FHIR ContactPoint.use — the purpose of a contact point value.

    Values defined by https://hl7.org/fhir/R4/valueset-contact-point-use.html:
      home   — a communication address at a home (not work).
      work   — an office contact address.
      temp   — a temporary contact address.
      old    — this contact address is no longer in use.
      mobile — a telecommunication device that moves with its owner.
    """

    home = "home"
    work = "work"
    temp = "temp"
    old = "old"
    mobile = "mobile"


class AddressUse(str, Enum):
    """
    FHIR Address.use — the purpose of the address.

    Values defined by https://hl7.org/fhir/R4/valueset-address-use.html:
      home    — a home address.
      work    — an office or institutional address.
      temp    — a temporary address (e.g. hotel during travel).
      old     — a previous address that is no longer in use.
      billing — an address to be used to send bills, invoices, receipts, etc.
    """

    home = "home"
    work = "work"
    temp = "temp"
    old = "old"
    billing = "billing"


class AddressType(str, Enum):
    """
    FHIR Address.type — distinguishes between a mailing address and a physical location.

    Values defined by https://hl7.org/fhir/R4/valueset-address-type.html:
      postal   — mailing address (PO Box or similar) — no physical visit expected.
      physical — a physical address that can be visited (building, floor, room).
      both     — the address serves as both a postal and a physical address.
    """

    postal = "postal"
    physical = "physical"
    both = "both"


class HumanNameUse(str, Enum):
    """
    FHIR HumanName.use — the purpose of a human name value.

    Values defined by https://hl7.org/fhir/R4/valueset-name-use.html:
      usual     — the name normally used to address the person (preferred display).
      official  — the formal name as it appears on legal documents.
      temp      — a temporary name (e.g. used during emergency care without ID).
      nickname  — an informal name used by friends or family.
      anonymous — a name used for privacy to hide the real identity (e.g. research).
      old       — a name that was previously in use (e.g. maiden name before marriage).
      maiden    — name used before changing due to marriage — a special case of `old`.
    """

    usual = "usual"
    official = "official"
    temp = "temp"
    nickname = "nickname"
    anonymous = "anonymous"
    old = "old"
    maiden = "maiden"


class AdministrativeGender(str, Enum):
    """
    FHIR administrative gender — the gender of a person used for administrative purposes.

    Note: FHIR separates administrative gender (used for record-keeping) from clinical
    sex or gender identity. This enum covers the four values used across Practitioner,
    Patient, RelatedPerson, and Person resources.

    Values defined by https://hl7.org/fhir/R4/valueset-administrative-gender.html:
      male    — male gender.
      female  — female gender.
      other   — a gender not covered by male or female (e.g. non-binary, intersex).
      unknown — gender is unknown or not provided.
    """

    male = "male"
    female = "female"
    other = "other"
    unknown = "unknown"


class ProcedureStatus(str, Enum):
    """
    FHIR event-status value set for Procedure.status (R4, required binding).

    Values defined by https://hl7.org/fhir/R4/valueset-event-status.html.
    Note the hyphenated codes ("in-progress", "not-done", "on-hold",
    "entered-in-error") — member names use underscores because hyphens are not
    valid Python identifiers, while the serialised values keep the FHIR spelling.

      preparation      — the core event has not started yet; preparatory work is underway.
      in-progress      — the event is currently occurring.
      not-done         — the event was terminated prior to any activity beyond preparation.
      on-hold          — the event has been temporarily stopped but is expected to resume.
      stopped          — the event was terminated prior to the planned or expected completion.
      completed        — the event has been completed.
      entered-in-error — this electronic record should never have existed.
      unknown          — the authoring system does not know which of the status values applies.
    """

    preparation = "preparation"
    in_progress = "in-progress"
    not_done = "not-done"
    on_hold = "on-hold"
    stopped = "stopped"
    completed = "completed"
    entered_in_error = "entered-in-error"
    unknown = "unknown"


class QuestionnaireStatus(str, Enum):
    """
    FHIR PublicationStatus value set for Questionnaire.status (R4, required binding).

    Values defined by https://hl7.org/fhir/R4/valueset-publication-status.html.

      draft   — under development, not yet for production use.
      active  — approved and ready for use.
      retired — no longer recommended for new use.
      unknown — the authoring system does not know which status applies.
    """

    draft = "draft"
    active = "active"
    retired = "retired"
    unknown = "unknown"


class QuestionnaireItemType(str, Enum):
    """
    FHIR QuestionnaireItemType value set for Questionnaire.item.type (R4, required binding).

    Values defined by https://hl7.org/fhir/R4/valueset-item-type.html. The
    hyphenated code "open-choice" is exposed as the member `open_choice`
    (hyphens are not valid in Python identifiers); the serialised value keeps
    the FHIR spelling.
    """

    group = "group"
    display = "display"
    boolean = "boolean"
    decimal = "decimal"
    integer = "integer"
    date = "date"
    dateTime = "dateTime"
    time = "time"
    string = "string"
    text = "text"
    url = "url"
    choice = "choice"
    open_choice = "open-choice"
    attachment = "attachment"
    reference = "reference"
    quantity = "quantity"


class QuestionnaireEnableBehavior(str, Enum):
    """
    FHIR EnableWhenBehavior value set (Questionnaire.item.enableBehavior).

    Values defined by https://hl7.org/fhir/R4/valueset-questionnaire-enable-behavior.html.

      all — enable the item only if all enableWhen conditions are true.
      any — enable the item if any enableWhen condition is true.
    """

    all = "all"
    any = "any"


class QuestionnaireItemOperator(str, Enum):
    """
    FHIR QuestionnaireItemOperator value set (Questionnaire.item.enableWhen.operator).

    Values defined by https://hl7.org/fhir/R4/valueset-questionnaire-enable-operator.html.
    Member names are identifier-safe stand-ins for the symbolic FHIR codes; the
    serialised values are the FHIR codes themselves.
    """

    exists = "exists"
    eq = "="
    ne = "!="
    gt = ">"
    lt = "<"
    ge = ">="
    le = "<="


class QuestionnaireResponseStatus(str, Enum):
    """
    FHIR QuestionnaireResponseStatus value set (QuestionnaireResponse.status, required binding).

    Values defined by https://hl7.org/fhir/R4/valueset-questionnaire-answers-status.html.
    Hyphenated codes are exposed with underscore member names (hyphens are not valid
    in Python identifiers); the serialised values keep the FHIR spelling.

      in-progress      — still being filled in; answers may be incomplete.
      completed        — all answers have been gathered.
      amended          — a completed response was subsequently changed.
      entered-in-error — this record should never have existed.
      stopped          — filling in was abandoned before completion.
    """

    in_progress = "in-progress"
    completed = "completed"
    amended = "amended"
    entered_in_error = "entered-in-error"
    stopped = "stopped"


class RiskAssessmentStatus(str, Enum):
    """
    FHIR ObservationStatus value set for RiskAssessment.status (R4, required binding).

    Values defined by https://hl7.org/fhir/R4/valueset-observation-status.html.
    "entered-in-error" is exposed as `entered_in_error` (hyphens are not valid in
    Python identifiers); the serialised value keeps the FHIR spelling.

      registered       — the existence of the assessment is registered but no result is available yet.
      preliminary      — an initial or interim result; may be subject to change.
      final            — the result is complete and verified.
      amended          — the result has been modified after being final.
      corrected        — the result has been modified to correct an error.
      cancelled        — the assessment was never completed.
      entered-in-error — this record should never have existed.
      unknown          — the authoring system does not know which status applies.
    """

    registered = "registered"
    preliminary = "preliminary"
    final = "final"
    amended = "amended"
    corrected = "corrected"
    cancelled = "cancelled"
    entered_in_error = "entered-in-error"
    unknown = "unknown"


class FlagStatus(str, Enum):
    """
    FHIR FlagStatus value set for Flag.status (R4, required binding).

    Values defined by https://hl7.org/fhir/R4/valueset-flag-status.html.
    "entered-in-error" is exposed as `entered_in_error` (hyphens are not valid in
    Python identifiers); the serialised value keeps the FHIR spelling.

      active           — the flag is active and should be taken into account.
      inactive         — the flag no longer needs to be taken into account.
      entered-in-error — this record should never have existed.
    """

    active = "active"
    inactive = "inactive"
    entered_in_error = "entered-in-error"


class TaskStatus(str, Enum):
    """
    FHIR TaskStatus value set for Task.status (R4, required binding).

    Values defined by https://hl7.org/fhir/R4/valueset-task-status.html. Hyphenated codes are
    exposed with underscore member names (hyphens are not valid in Python identifiers); the
    serialised values keep the FHIR spelling.

      draft            — in the process of being created; not yet ready to act on.
      requested        — the task has been requested but not yet received.
      received         — the task has been received by the performer.
      accepted         — the performer has accepted the task.
      rejected         — the performer has declined the task.
      ready            — ready to be performed.
      cancelled        — the task was cancelled before completion.
      in-progress      — the task is being performed.
      on-hold          — the task has been temporarily stopped.
      failed           — the task could not be completed.
      completed        — the task has been performed to completion.
      entered-in-error — this record should never have existed.
    """

    draft = "draft"
    requested = "requested"
    received = "received"
    accepted = "accepted"
    rejected = "rejected"
    ready = "ready"
    cancelled = "cancelled"
    in_progress = "in-progress"
    on_hold = "on-hold"
    failed = "failed"
    completed = "completed"
    entered_in_error = "entered-in-error"


class TaskIntent(str, Enum):
    """
    FHIR TaskIntent value set for Task.intent (R4, required binding).

    Values defined by https://hl7.org/fhir/R4/valueset-task-intent.html (hyphenated codes use
    underscore member names).
    """

    unknown = "unknown"
    proposal = "proposal"
    plan = "plan"
    order = "order"
    original_order = "original-order"
    reflex_order = "reflex-order"
    filler_order = "filler-order"
    instance_order = "instance-order"
    option = "option"


class TaskPriority(str, Enum):
    """
    FHIR RequestPriority value set for Task.priority (R4, required binding).

    Values defined by https://hl7.org/fhir/R4/valueset-request-priority.html:
    routine < urgent < asap < stat.
    """

    routine = "routine"
    urgent = "urgent"
    asap = "asap"
    stat = "stat"


class EpisodeOfCareStatus(str, Enum):
    """
    FHIR EpisodeOfCareStatus value set for EpisodeOfCare.status (R4, required binding).

    Values defined by https://hl7.org/fhir/R4/valueset-episode-of-care-status.html.
    "entered-in-error" is exposed as `entered_in_error` (hyphens are not valid in Python
    identifiers); the serialised value keeps the FHIR spelling.

      planned          — the episode is planned but has not started.
      waitlist         — the patient is on a waiting list for the episode.
      active           — the episode is in progress.
      onhold           — the episode is temporarily suspended.
      finished         — the episode has ended.
      cancelled        — the episode was cancelled before it started or completed.
      entered-in-error — this record should never have existed.
    """

    planned = "planned"
    waitlist = "waitlist"
    active = "active"
    onhold = "onhold"
    finished = "finished"
    cancelled = "cancelled"
    entered_in_error = "entered-in-error"


# ── PlanDefinition value sets (FHIR R4) ─────────────────────────────────────


class PlanDefinitionStatus(str, Enum):
    """FHIR R4 PublicationStatus (PlanDefinition.status, required binding)."""

    draft = "draft"
    active = "active"
    retired = "retired"
    unknown = "unknown"


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


class SortDirection(str, Enum):
    """FHIR R4 SortDirection (DataRequirement.sort.direction)."""

    ascending = "ascending"
    descending = "descending"


# ── ActivityDefinition value sets (FHIR R4) ─────────────────────────────────


class ActivityDefinitionKind(str, Enum):
    """FHIR R4 RequestResourceType (ActivityDefinition.kind, required binding)."""

    Appointment = "Appointment"
    AppointmentResponse = "AppointmentResponse"
    CarePlan = "CarePlan"
    Claim = "Claim"
    CommunicationRequest = "CommunicationRequest"
    Contract = "Contract"
    DeviceRequest = "DeviceRequest"
    EnrollmentRequest = "EnrollmentRequest"
    ImmunizationRecommendation = "ImmunizationRecommendation"
    MedicationRequest = "MedicationRequest"
    NutritionOrder = "NutritionOrder"
    ServiceRequest = "ServiceRequest"
    SupplyRequest = "SupplyRequest"
    Task = "Task"
    VisionPrescription = "VisionPrescription"


class ActivityDefinitionIntent(str, Enum):
    """FHIR R4 RequestIntent (ActivityDefinition.intent, required binding)."""

    proposal = "proposal"
    plan = "plan"
    directive = "directive"
    order = "order"
    original_order = "original-order"
    reflex_order = "reflex-order"
    filler_order = "filler-order"
    instance_order = "instance-order"
    option = "option"


# ── CarePlan value sets (FHIR R4) ───────────────────────────────────────────


class CarePlanStatus(str, Enum):
    draft = "draft"
    active = "active"
    on_hold = "on-hold"
    revoked = "revoked"
    completed = "completed"
    entered_in_error = "entered-in-error"
    unknown = "unknown"


class CarePlanIntent(str, Enum):
    proposal = "proposal"
    plan = "plan"
    order = "order"
    option = "option"


class CarePlanDetailActivityStatus(str, Enum):
    not_started = "not-started"
    scheduled = "scheduled"
    in_progress = "in-progress"
    on_hold = "on-hold"
    completed = "completed"
    cancelled = "cancelled"
    stopped = "stopped"
    unknown = "unknown"
    entered_in_error = "entered-in-error"


class CarePlanActivityKind(str, Enum):
    """FHIR R4 CarePlanActivityKind (activity.detail.kind, required binding)."""

    Appointment = "Appointment"
    CommunicationRequest = "CommunicationRequest"
    DeviceRequest = "DeviceRequest"
    MedicationRequest = "MedicationRequest"
    NutritionOrder = "NutritionOrder"
    Task = "Task"
    ServiceRequest = "ServiceRequest"
    VisionPrescription = "VisionPrescription"


# ── CareTeam value sets (FHIR R4) ───────────────────────────────────────────


class CareTeamStatus(str, Enum):
    """FHIR R4 CareTeamStatus value set (CareTeam.status, required binding)."""

    proposed = "proposed"
    active = "active"
    suspended = "suspended"
    inactive = "inactive"
    entered_in_error = "entered-in-error"
