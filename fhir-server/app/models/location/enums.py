from enum import Enum


class LocationStatus(str, Enum):
    """FHIR R4 Location.status value set — general availability."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"


class LocationMode(str, Enum):
    """FHIR R4 Location.mode value set — instance or kind."""

    INSTANCE = "instance"
    KIND = "kind"


class LocationPartOfReferenceType(str, Enum):
    """Allowed reference types for Location.partOf."""

    LOCATION = "Location"


class LocationEndpointReferenceType(str, Enum):
    """Allowed reference types for Location.endpoint[]."""

    ENDPOINT = "Endpoint"
