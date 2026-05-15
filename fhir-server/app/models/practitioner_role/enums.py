from enum import Enum


class DayOfWeek(str, Enum):
    mon = "mon"
    tue = "tue"
    wed = "wed"
    thu = "thu"
    fri = "fri"
    sat = "sat"
    sun = "sun"


class PractitionerRoleLocationReferenceType(str, Enum):
    """Allowed reference types for PractitionerRole.location[]."""

    LOCATION = "Location"


class PractitionerRoleHealthcareServiceReferenceType(str, Enum):
    """Allowed reference types for PractitionerRole.healthcareService[]."""

    HEALTHCARE_SERVICE = "HealthcareService"


class PractitionerRoleEndpointReferenceType(str, Enum):
    """Allowed reference types for PractitionerRole.endpoint[]."""

    ENDPOINT = "Endpoint"
