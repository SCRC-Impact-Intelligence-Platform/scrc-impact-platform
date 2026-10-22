from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


PublicationStatus = Literal[
    "PENDING",
    "SENT",
    "CONFIRMED",
    "REJECTED",
    "DISMISSED",
]


class PublicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pmid: str
    title: str
    authors: list[str]
    journal: str | None
    publication_date: str | None
    doi: str | None
    abstract: str | None
    first_discovered_by_orcid: str
    discovered_at: datetime

    status: PublicationStatus