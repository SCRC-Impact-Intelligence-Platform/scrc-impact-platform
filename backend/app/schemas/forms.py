from pydantic import BaseModel, Field


class PublicationSelection(BaseModel):
    publication_id: int
    resource_ids: list[int] = Field(min_length=1)


class FormCreate(BaseModel):
    items: list[PublicationSelection] = Field(min_length=1)


from datetime import datetime
from pydantic import ConfigDict
from app.enums import FormBatchState


class FormQuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    publication_id: int
    resource_ids: list[int]
    yes_question_id: str
    resources_question_id: str


class FormBatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    google_form_id: str | None
    responder_url: str | None
    state: FormBatchState
    created_at: datetime


class FormBatchDetail(FormBatchResponse):
    questions: list[FormQuestionResponse]
