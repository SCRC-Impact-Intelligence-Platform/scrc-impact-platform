from pydantic import BaseModel, Field


class PublicationSelection(BaseModel):
    publication_id: int
    resource_ids: list[int] = Field(min_length=1)


class FormCreate(BaseModel):
    items: list[PublicationSelection] = Field(min_length=1)
