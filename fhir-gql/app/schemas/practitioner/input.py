"""
Input schemas for the Practitioner resource endpoints.

Three schemas cover the write surfaces:
  - PractitionerCreateSchema  — POST /practitioners body
  - PractitionerPatchSchema   — PATCH /practitioners/{id} body
  - ListPractitionersSchema   — GET /practitioners query parameters

Design notes:
  - The fhir-server manages Practitioner child arrays (name, identifier, telecom,
    address, photo, qualification, communication) via separate sub-routes. The
    create schema here only accepts the top-level scalar fields — no child arrays.
  - user_id / org_id are Optional to match the fhir-server's PractitionerCreateSchema.
  - created_by / updated_by are NOT in any schema — FhirClient injects them from actor.sub.
  - gender uses AdministrativeGender so invalid values are caught at the API boundary.
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import AdministrativeGender


class PractitionerCreateSchema(BaseModel):
    """
    Input schema for creating a Practitioner resource (POST /practitioners).

    All fields are optional because the fhir-server allows creating a bare
    Practitioner record and adding child sub-resources (name, identifier, etc.)
    via separate sub-route calls.

    Tenant scoping (user_id, org_id) is Optional to match the fhir-server schema.
    created_by is NOT included — FhirClient injects it automatically from actor.sub.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "user_id": "user-uuid-123",
                "org_id": "org-uuid-456",
                "active": True,
                "gender": "female",
                "birth_date": "1978-03-15",
            }
        },
    )

    # Tenant scoping — Optional to match the fhir-server schema
    user_id: Optional[str] = Field(default=None, description="User identifier for tenant scoping")
    org_id: Optional[str] = Field(default=None, description="Organisation identifier for tenant scoping")

    # Whether this practitioner record is currently in active use
    active: Optional[bool] = Field(default=True, description="Whether this practitioner record is active")

    # FHIR R4 administrative gender (not clinical sex or gender identity)
    gender: Optional[AdministrativeGender] = Field(
        default=None,
        description="Administrative gender: male | female | other | unknown",
    )

    # Date of birth — ISO 8601 date (not datetime)
    birth_date: Optional[date] = Field(default=None, description="Date of birth (ISO 8601 date, e.g. 1978-03-15)")

    # Deceased indicators — at most one should be populated (boolean XOR datetime)
    deceased_boolean: Optional[bool] = Field(
        default=None,
        description="True if the practitioner is deceased and the exact date/time is unknown",
    )
    deceased_datetime: Optional[datetime] = Field(
        default=None,
        description="Date/time of death — used when the exact datetime is known (ISO 8601)",
    )


class PractitionerPatchSchema(BaseModel):
    """
    Input schema for partially updating a Practitioner (PATCH /practitioners/{id}).

    All fields are optional — the service layer enforces that at least one is provided.
    Child arrays (name, identifier, telecom, address, photo, qualification, communication)
    are managed via separate sub-routes and cannot be patched here.
    updated_by is NOT included — FhirClient injects it automatically from actor.sub.
    """

    model_config = ConfigDict(extra="forbid")

    # Patchable scalar fields only
    active: Optional[bool] = Field(default=None, description="Update the active status")
    gender: Optional[AdministrativeGender] = Field(
        default=None,
        description="Update administrative gender: male | female | other | unknown",
    )
    birth_date: Optional[date] = Field(default=None, description="Update date of birth (ISO 8601 date)")
    deceased_boolean: Optional[bool] = Field(default=None, description="Update deceased boolean flag")
    deceased_datetime: Optional[datetime] = Field(default=None, description="Update date/time of death")


class ListPractitionersSchema(BaseModel):
    """
    Query parameters for listing Practitioners (GET /practitioners).

    Filters by name, active status, or tenant scoping. All filters optional.
    Name searches are delegated to the fhir-server which queries the practitioner_name
    child table.
    """

    # Name filters — searches across the practitioner_name child table (partial, case-insensitive)
    family_name: Optional[str] = Field(
        default=None,
        description="Filter by family (last) name — partial match, case-insensitive",
    )
    given_name: Optional[str] = Field(
        default=None,
        description="Filter by given (first) name — partial match, case-insensitive",
    )

    # Active status filter
    active: Optional[bool] = Field(default=None, description="Filter by active status")

    # Tenant scoping filters
    user_id: Optional[str] = Field(default=None, description="Filter by user_id for tenant scoping")
    org_id: Optional[str] = Field(default=None, description="Filter by org_id for tenant scoping")

    # Pagination
    limit: int = Field(default=20, ge=1, le=200, description="Maximum number of records to return per page")
    offset: int = Field(default=0, ge=0, description="Number of records to skip before returning results")
