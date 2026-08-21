"""OpenAPI response schemas, computed once at import.

The emitted spec is a contract, not decoration — anything consuming
`/openapi.json` (an MCP tool server, a generated client) sees exactly what is
declared here, so a missing field is a silently broken caller.

Only `application/json` is declared. fhir-server documents both that and
`application/fhir+json` because it content-negotiates; this service has one
representation, so a second content type would be a lie.

Response models are declared via `responses=` rather than `response_model=`
because the handlers return `JSONResponse` directly — `response_model` would
re-validate and silently drop keys the model does not know about.
"""

from app.core.schema_utils import inline_schema
from app.schemas.staging_medical_record import (
    PaginatedStagingMedicalRecordResponse,
    PlainStagingMedicalRecordResponse,
)

_ERR_NOT_FOUND = {404: {"description": "Staging record not found"}}
_ERR_VALIDATION = {
    422: {"description": "Validation error — request body failed schema validation"}
}

_SINGLE_200 = {
    200: {
        "description": "The staging record, with its extracted observations nested.",
        "content": {
            "application/json": {
                "schema": inline_schema(
                    PlainStagingMedicalRecordResponse.model_json_schema()
                )
            }
        },
    }
}

_SINGLE_201 = {201: {**_SINGLE_200[200], "description": "The created staging record."}}

_LIST_200 = {
    200: {
        "description": "Paginated list of staging records.",
        "content": {
            "application/json": {
                "schema": inline_schema(
                    PaginatedStagingMedicalRecordResponse.model_json_schema()
                )
            }
        },
    }
}

_DELETE_204 = {204: {"description": "Deleted. Observations cascade with it."}}
