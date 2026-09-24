"""
Vitals schema package — re-exports public input/response schemas.

Vitals has no FHIR R4 representation (it is a custom wearable/activity resource),
so unlike other schema packages there is no fhir_schemas.py module here.
"""

from app.schemas.vitals.input import (
    ListVitalsSchema,
    VitalsCreateSchema,
    VitalsPatchSchema,
)
from app.schemas.vitals.response import PaginatedVitalsResponse, VitalsResponse

__all__ = [
    "VitalsCreateSchema",
    "VitalsPatchSchema",
    "ListVitalsSchema",
    "VitalsResponse",
    "PaginatedVitalsResponse",
]
