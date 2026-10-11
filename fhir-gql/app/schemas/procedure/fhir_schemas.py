"""
FHIR R4 response schemas for Procedure resources — Swagger docs only.

These are never used for runtime validation (routers return JSONResponse
directly); they exist so the OpenAPI spec documents the
`application/fhir+json` representation.

Reference: https://www.hl7.org/fhir/R4/procedure.html
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class FhirProcedureResponse(BaseModel):
    """FHIR R4 Procedure shape for Swagger documentation."""

    model_config = ConfigDict(extra="allow")

    resourceType: str = "Procedure"
    id: Optional[str] = None
    identifier: Optional[List[Dict[str, Any]]] = None
    instantiatesCanonical: Optional[List[str]] = None
    instantiatesUri: Optional[List[str]] = None
    basedOn: Optional[List[Dict[str, Any]]] = None
    partOf: Optional[List[Dict[str, Any]]] = None
    status: Optional[str] = None
    statusReason: Optional[Dict[str, Any]] = None
    category: Optional[Dict[str, Any]] = None
    code: Optional[Dict[str, Any]] = None
    subject: Optional[Dict[str, Any]] = None
    encounter: Optional[Dict[str, Any]] = None
    # performed[x] — exactly one of these is present.
    performedDateTime: Optional[str] = None
    performedPeriod: Optional[Dict[str, Any]] = None
    performedString: Optional[str] = None
    performedAge: Optional[Dict[str, Any]] = None
    performedRange: Optional[Dict[str, Any]] = None
    recorder: Optional[Dict[str, Any]] = None
    asserter: Optional[Dict[str, Any]] = None
    performer: Optional[List[Dict[str, Any]]] = None
    location: Optional[Dict[str, Any]] = None
    reasonCode: Optional[List[Dict[str, Any]]] = None
    reasonReference: Optional[List[Dict[str, Any]]] = None
    bodySite: Optional[List[Dict[str, Any]]] = None
    outcome: Optional[Dict[str, Any]] = None
    report: Optional[List[Dict[str, Any]]] = None
    complication: Optional[List[Dict[str, Any]]] = None
    complicationDetail: Optional[List[Dict[str, Any]]] = None
    followUp: Optional[List[Dict[str, Any]]] = None
    note: Optional[List[Dict[str, Any]]] = None
    focalDevice: Optional[List[Dict[str, Any]]] = None
    usedReference: Optional[List[Dict[str, Any]]] = None
    usedCode: Optional[List[Dict[str, Any]]] = None


class FhirBundleEntry(BaseModel):
    """A single entry in a FHIR Bundle — wraps one Procedure resource."""

    model_config = ConfigDict(extra="allow")

    # Typed (not Any) so Swagger UI renders the full Procedure schema inside the entry.
    resource: FhirProcedureResponse


class FhirBundleResponse(BaseModel):
    """FHIR R4 Bundle (searchset) for the Procedure list endpoint."""

    model_config = ConfigDict(extra="allow")

    resourceType: str = "Bundle"
    type: str = "searchset"
    total: Optional[int] = None
    entry: Optional[List[FhirBundleEntry]] = None
