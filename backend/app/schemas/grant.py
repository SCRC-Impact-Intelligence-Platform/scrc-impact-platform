from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class GrantCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    funder: str = Field(min_length=1, max_length=255)
    amount: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    award_date: date
    researcher_id: int | None = None


class GrantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    funder: str
    amount: Decimal | None
    award_date: date
    researcher_id: int | None
