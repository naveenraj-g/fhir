"""
Schemas of the `$apply` operations (PlanDefinition and ActivityDefinition).

Applying a definition to a subject generates ServiceRequests (the only ActivityDefinition kind supported today).
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.core.schema_utils import inline_schema
from app.schemas.service_request.fhir_schemas import FhirBundleResponse
from app.schemas.service_request.response import ServiceRequestResponse


class ActivityDefinitionApplySchema(BaseModel):
    """Body of `POST /activity-definitions/{id}/$apply`."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "org_id": "org-uuid-456",
                "subject": "Patient/10001",
                "encounter": "Encounter/20001",
                "practitioner": "Practitioner/30001",
                "persist": False,
            }
        },
    )

    org_id: str = Field(..., min_length=1, description="Tenant organization id — the definition must belong to it.")
    user_id: Optional[str] = Field(None, description="Owner stored on the created records when `persist` is true.")
    subject: str = Field(..., description="Who the request is for — `Patient/10001` (also Group, Location, Device).")
    subject_display: Optional[str] = None
    encounter: Optional[str] = Field(None, description="Optional `Encounter/20001` the requests belong to.")
    encounter_display: Optional[str] = None
    practitioner: Optional[str] = Field(
        None, description="Requester of the generated orders — `Practitioner/30001` (or PractitionerRole, Organization, ...)."
    )
    practitioner_display: Optional[str] = None
    persist: bool = Field(
        False,
        description="false (default) = preview only, nothing is saved. true = the ServiceRequests are saved in one "
        "transaction (all or none).",
    )
    status: Optional[Literal["draft", "active"]] = Field(
        None, description="Status of the generated ServiceRequests. Defaults to `draft` for a preview and `active` when persisting."
    )
    allow_duplicates: bool = Field(
        False,
        description="false (default) = a definition that already produced a (non-revoked) ServiceRequest for the same "
        "subject/encounter is skipped. true = always generate.",
    )


class PlanDefinitionApplySchema(ActivityDefinitionApplySchema):
    """Body of `POST /plan-definitions/{id}/$apply`."""

    selected_actions: Optional[List[str]] = Field(
        None,
        description="Action ids (`action[].id` of the PlanDefinition) to apply. Omit to apply every action; "
        "an id that is not part of the plan is rejected with 422.",
    )


class SkippedAction(BaseModel):
    action_id: Optional[str] = Field(None, description="`action[].id` of the PlanDefinition action.")
    action_title: Optional[str] = None
    definition: Optional[str] = Field(None, description="The action's definitionCanonical, or the ActivityDefinition reference.")
    reason: str = Field(..., description="Why nothing was generated for it.")


class ApplyResponse(BaseModel):
    definition: str = Field(..., description="The applied definition, e.g. `PlanDefinition/400001`.")
    subject: str
    encounter: Optional[str] = None
    persisted: bool = Field(..., description="false = preview only (`id` of each ServiceRequest is null); true = saved.")
    total: int = Field(..., description="Number of ServiceRequests generated.")
    service_requests: List[ServiceRequestResponse]
    skipped: List[SkippedAction]


APPLY_200 = {
    200: {
        "description": "Generated ServiceRequests (plain JSON) or a `collection` Bundle of them (FHIR). In the Bundle, "
        "actions that produced nothing are listed as `information` issues of a trailing OperationOutcome entry.",
        "content": {
            "application/json": {"schema": inline_schema(ApplyResponse.model_json_schema())},
            "application/fhir+json": {"schema": inline_schema(FhirBundleResponse.model_json_schema())},
        },
    }
}
