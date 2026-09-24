from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class LocationIdentifierInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    use: str | None = None
    type_system: str | None = None
    type_code: str | None = None
    type_display: str | None = None
    type_text: str | None = None
    system: str | None = None
    value: str | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
    assigner: str | None = None


class LocationTypeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    coding_system: str | None = None
    coding_code: str | None = None
    coding_display: str | None = None
    text: str | None = None


class LocationTelecomInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    system: str | None = Field(
        None, description="phone | fax | email | pager | url | sms | other"
    )
    value: str | None = None
    use: str | None = Field(None, description="home | work | temp | old | mobile")
    rank: int | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None


class LocationHoursOfOperationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    days_of_week: list[str] | None = Field(
        None, description="Days available, e.g. ['mon', 'wed', 'fri']"
    )
    all_day: bool | None = None
    opening_time: str | None = Field(None, description="HH:mm:ss opening time")
    closing_time: str | None = Field(None, description="HH:mm:ss closing time")


class LocationEndpointInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: str = Field(
        ..., description="FHIR Endpoint reference, e.g. 'Endpoint/1'."
    )
    reference_display: str | None = None


class LocationCreateSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "user_id": "u-test",
                    "org_id": "org-test",
                    "status": "active",
                    "name": "Main Building",
                    "description": "Primary hospital building",
                    "mode": "instance",
                    "address_line": ["123 Main St", "Suite 100"],
                    "address_city": "Springfield",
                    "address_state": "IL",
                    "address_postal_code": "62701",
                    "address_country": "US",
                    "physical_type_system": "http://terminology.hl7.org/CodeSystem/location-physical-type",
                    "physical_type_code": "bu",
                    "physical_type_display": "Building",
                    "managing_organization": "Organization/190001",
                    "managing_organization_display": "General Hospital",
                    "position_longitude": -89.6501481,
                    "position_latitude": 39.7817213,
                    "hours_of_operation": [
                        {
                            "days_of_week": ["mon", "tue", "wed", "thu", "fri"],
                            "all_day": False,
                            "opening_time": "08:00:00",
                            "closing_time": "17:00:00",
                        }
                    ],
                }
            ]
        },
    )

    user_id: str | None = None
    org_id: str | None = None
    created_by: str | None = None

    status: str | None = Field(None, description="active | suspended | inactive")
    operational_status_system: str | None = None
    operational_status_code: str | None = None
    operational_status_display: str | None = None
    name: str | None = None
    description: str | None = None
    mode: str | None = Field(None, description="instance | kind")

    identifiers: list[LocationIdentifierInput] | None = None
    aliases: list[str] | None = Field(
        None, description="Alternate names for the location."
    )
    types: list[LocationTypeInput] | None = None
    telecoms: list[LocationTelecomInput] | None = None

    address_use: str | None = None
    address_type: str | None = None
    address_text: str | None = None
    address_line: list[str] | None = Field(None, description="Street address lines.")
    address_city: str | None = None
    address_district: str | None = None
    address_state: str | None = None
    address_postal_code: str | None = None
    address_country: str | None = None
    address_period_start: datetime | None = None
    address_period_end: datetime | None = None

    physical_type_system: str | None = None
    physical_type_code: str | None = None
    physical_type_display: str | None = None
    physical_type_text: str | None = None

    managing_organization: str | None = Field(
        None, description="FHIR reference, e.g. 'Organization/190001'."
    )
    managing_organization_display: str | None = None
    part_of: str | None = Field(
        None, description="Parent location reference, e.g. 'Location/230001'."
    )
    part_of_display: str | None = None

    availability_exceptions: str | None = None

    position_longitude: Decimal | None = None
    position_latitude: Decimal | None = None
    position_altitude: Decimal | None = None

    hours_of_operation: list[LocationHoursOfOperationInput] | None = None
    endpoints: list[LocationEndpointInput] | None = None


class LocationPatchSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str | None = None
    operational_status_system: str | None = None
    operational_status_code: str | None = None
    operational_status_display: str | None = None
    name: str | None = None
    description: str | None = None
    mode: str | None = None

    address_use: str | None = None
    address_type: str | None = None
    address_text: str | None = None
    address_line: list[str] | None = None
    address_city: str | None = None
    address_district: str | None = None
    address_state: str | None = None
    address_postal_code: str | None = None
    address_country: str | None = None
    address_period_start: datetime | None = None
    address_period_end: datetime | None = None

    physical_type_system: str | None = None
    physical_type_code: str | None = None
    physical_type_display: str | None = None
    physical_type_text: str | None = None

    managing_organization: str | None = None
    managing_organization_display: str | None = None
    part_of: str | None = None
    part_of_display: str | None = None

    availability_exceptions: str | None = None

    position_longitude: Decimal | None = None
    position_latitude: Decimal | None = None
    position_altitude: Decimal | None = None
    updated_by: str | None = None
