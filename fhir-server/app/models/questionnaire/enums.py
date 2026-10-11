from enum import Enum


class QuestionnaireStatus(str, Enum):
    """FHIR R4 PublicationStatus value set (Questionnaire.status, required binding)."""

    draft = "draft"
    active = "active"
    retired = "retired"
    unknown = "unknown"


class QuestionnaireItemType(str, Enum):
    """FHIR R4 QuestionnaireItemType value set (Questionnaire.item.type, required binding)."""

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
    """FHIR R4 EnableWhenBehavior value set (Questionnaire.item.enableBehavior)."""

    all = "all"
    any = "any"


class QuestionnaireItemOperator(str, Enum):
    """
    FHIR R4 QuestionnaireItemOperator value set (Questionnaire.item.enableWhen.operator).

    Member names are identifier-safe stand-ins for the symbolic FHIR codes
    (hyphen/symbol codes cannot be Python identifiers); the *values* are the FHIR codes.
    """

    exists = "exists"
    eq = "="
    ne = "!="
    gt = ">"
    lt = "<"
    ge = ">="
    le = "<="


class QuestionnaireUseContextReferenceType(str, Enum):
    """Allowed reference types for UsageContext.valueReference (R4)."""

    PlanDefinition = "PlanDefinition"
    ResearchStudy = "ResearchStudy"
    InsurancePlan = "InsurancePlan"
    HealthcareService = "HealthcareService"
    Group = "Group"
    Location = "Location"
    Organization = "Organization"
