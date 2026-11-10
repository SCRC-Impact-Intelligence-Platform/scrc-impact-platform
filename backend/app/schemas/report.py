from pydantic import BaseModel

from app.schemas.publication import PublicationResponse


class QuarterlyReportResponse(BaseModel):
    year: int
    quarter: int
    publications: list[PublicationResponse]
    # CONFIRMED publications from the year whose date has no month; not in any quarter.
    undated_publications: list[PublicationResponse]
    # CONFIRMED publications with no readable year; not in any report period.
    no_date_publications: list[PublicationResponse]
