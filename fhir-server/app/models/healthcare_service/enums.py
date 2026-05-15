from enum import Enum


class HealthcareServiceLocationReferenceType(str, Enum):
    """Allowed reference types for HealthcareService.location[]."""

    LOCATION = "Location"


class HealthcareServiceCoverageAreaReferenceType(str, Enum):
    """Allowed reference types for HealthcareService.coverageArea[]."""

    LOCATION = "Location"


class HealthcareServiceEndpointReferenceType(str, Enum):
    """Allowed reference types for HealthcareService.endpoint[]."""

    ENDPOINT = "Endpoint"
