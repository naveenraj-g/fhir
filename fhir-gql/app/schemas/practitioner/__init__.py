"""
Public API for the Practitioner schemas package.

Import from here rather than from sub-modules to insulate callers from
internal reorganisation.
"""

from app.schemas.practitioner.fhir_schemas import FhirBundleResponse, FhirPractitionerResponse
from app.schemas.practitioner.input import ListPractitionersSchema, PractitionerCreateSchema, PractitionerPatchSchema
from app.schemas.practitioner.response import PaginatedPractitionerResponse, PractitionerResponse

__all__ = [
    # Input schemas — used for request body validation
    "PractitionerCreateSchema",
    "PractitionerPatchSchema",
    "ListPractitionersSchema",
    # Plain JSON response schemas — Swagger documentation (application/json)
    "PractitionerResponse",
    "PaginatedPractitionerResponse",
    # FHIR R4 response schemas — Swagger documentation (application/fhir+json)
    "FhirPractitionerResponse",
    "FhirBundleResponse",
]
