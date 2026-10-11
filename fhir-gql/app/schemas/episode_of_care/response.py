"""
Response schemas for EpisodeOfCare resources (fhir-gql gateway).

Plain* classes mirror the fhir-server snake_case output (`application/json`);
Fhir* classes document the `application/fhir+json` shape for Swagger only.
"""

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Plain sub-schemas
# ---------------------------------------------------------------------------


class PlainEpisodeOfCareIdentifier(BaseModel):
    """PlainEpisodeOfCareIdentifier — see the fhir-server schema of the same name."""

    model_config = ConfigDict(extra="allow")
    id: int
    use: Optional[str] = None
    type_system: Optional[str] = None
    type_code: Optional[str] = None
    type_display: Optional[str] = None
    type_text: Optional[str] = None
    system: Optional[str] = None
    value: Optional[str] = None
    period_start: Optional[Any] = None
    period_end: Optional[Any] = None
    assigner: Optional[str] = None


class PlainEpisodeOfCareStatusHistory(BaseModel):
    """PlainEpisodeOfCareStatusHistory — see the fhir-server schema of the same name."""

    model_config = ConfigDict(extra="allow")
    id: int
    status: str
    period_start: Optional[Any] = None
    period_end: Optional[Any] = None


class PlainEpisodeOfCareType(BaseModel):
    """PlainEpisodeOfCareType — see the fhir-server schema of the same name."""

    model_config = ConfigDict(extra="allow")
    id: int
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class PlainEpisodeOfCareDiagnosis(BaseModel):
    """PlainEpisodeOfCareDiagnosis — see the fhir-server schema of the same name."""

    model_config = ConfigDict(extra="allow")
    id: int
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    reference_display: Optional[str] = None
    role_system: Optional[str] = None
    role_code: Optional[str] = None
    role_display: Optional[str] = None
    role_text: Optional[str] = None
    rank: Optional[int] = None


class PlainEpisodeOfCareReferralRequest(BaseModel):
    """PlainEpisodeOfCareReferralRequest — see the fhir-server schema of the same name."""

    model_config = ConfigDict(extra="allow")
    id: int
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    reference_display: Optional[str] = None


class PlainEpisodeOfCareTeam(BaseModel):
    """PlainEpisodeOfCareTeam — see the fhir-server schema of the same name."""

    model_config = ConfigDict(extra="allow")
    id: int
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    reference_display: Optional[str] = None


class PlainEpisodeOfCareAccount(BaseModel):
    """PlainEpisodeOfCareAccount — see the fhir-server schema of the same name."""

    model_config = ConfigDict(extra="allow")
    id: int
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    reference_display: Optional[str] = None


# ---------------------------------------------------------------------------
# Plain main response
# ---------------------------------------------------------------------------


class EpisodeOfCareRecord(BaseModel):
    """EpisodeOfCareRecord — see the fhir-server schema of the same name."""

    model_config = ConfigDict(extra="allow")
    id: int
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    status: str
    patient_type: Optional[str] = None
    patient_id: Optional[int] = None
    patient_display: Optional[str] = None
    managing_organization_type: Optional[str] = None
    managing_organization_id: Optional[int] = None
    managing_organization_display: Optional[str] = None
    period_start: Optional[Any] = None
    period_end: Optional[Any] = None
    care_manager_type: Optional[str] = None
    care_manager_id: Optional[int] = None
    care_manager_display: Optional[str] = None
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    identifiers: list[PlainEpisodeOfCareIdentifier] = []
    status_history: list[PlainEpisodeOfCareStatusHistory] = []
    types: list[PlainEpisodeOfCareType] = []
    diagnoses: list[PlainEpisodeOfCareDiagnosis] = []
    referral_requests: list[PlainEpisodeOfCareReferralRequest] = []
    team: list[PlainEpisodeOfCareTeam] = []
    accounts: list[PlainEpisodeOfCareAccount] = []


class PaginatedEpisodeOfCareResponse(BaseModel):
    """PaginatedEpisodeOfCareResponse — see the fhir-server schema of the same name."""

    model_config = ConfigDict(extra="allow")
    total: int
    limit: int
    offset: int
    data: list[EpisodeOfCareRecord]


# ---------------------------------------------------------------------------
# FHIR response schemas
# ---------------------------------------------------------------------------


class FhirEpisodeOfCareResponse(BaseModel):
    """FhirEpisodeOfCareResponse — see the fhir-server schema of the same name."""

    model_config = ConfigDict(extra="allow")
    resourceType: str = "EpisodeOfCare"
    id: str


class FhirBundleEntry(BaseModel):
    """FhirBundleEntry — see the fhir-server schema of the same name."""

    model_config = ConfigDict(extra="allow")
    resource: FhirEpisodeOfCareResponse


class FhirBundleResponse(BaseModel):
    """FhirBundleResponse — see the fhir-server schema of the same name."""

    model_config = ConfigDict(extra="allow")
    resourceType: str = "Bundle"
    type: str = "searchset"
    total: int
    entry: list[FhirBundleEntry] = []
