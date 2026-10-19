from pydantic import BaseModel, ConfigDict, Field


class ResearcherCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    orcid: str = Field(
        pattern=r"^\d{4}-\d{4}-\d{4}-[\dX]{4}$"
    )


class ResearcherUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )
    is_active: bool | None = None


class ResearcherResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    orcid: str
    is_active: bool