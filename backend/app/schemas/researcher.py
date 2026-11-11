from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ResearcherCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    orcid: str | None = Field(
        default=None, pattern=r"^\d{4}-\d{4}-\d{4}-[\dX]{4}$"
    )


class ResearcherUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )
    email: EmailStr | None = None
    orcid: str | None = Field(
        default=None, pattern=r"^\d{4}-\d{4}-\d{4}-[\dX]{4}$"
    )
    is_active: bool | None = None


class ResearcherResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    orcid: str | None
    email: EmailStr
    is_active: bool


class ResearcherImportResponse(BaseModel):
    created: int
    skipped: int
