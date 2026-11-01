from app.enums import ResourceType

from pydantic import BaseModel, ConfigDict, Field


class ResourceCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=255,
    )
    type: ResourceType


class ResourceUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )
    type: ResourceType | None = None
    is_active: bool | None = None


class ResourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: ResourceType
    is_active: bool
