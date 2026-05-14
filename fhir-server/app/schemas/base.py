from pydantic import BaseModel, ConfigDict


class FHIRBaseModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        use_enum_values=True,
    )


class HealthResponseSchema(BaseModel):
    status: str
    req_id: str
