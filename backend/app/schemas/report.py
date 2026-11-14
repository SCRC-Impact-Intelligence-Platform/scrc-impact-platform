from pydantic import BaseModel

from app.enums import ResourceCriticality, ResourceType
from app.schemas.publication import PublicationResponse


class ReportResourceAttribution(BaseModel):
    resource_id: int
    resource_name: str
    resource_type: ResourceType
    criticality: ResourceCriticality


class AttributedPublication(BaseModel):
    publication: PublicationResponse
    resources: list[ReportResourceAttribution]


class AttributionSummary(BaseModel):
    # Publications in the quarter (``publications``) attributed to at least one resource.
    attributed_in_period: int
    # ...of which at least one attributed resource is a grant (FUNDING).
    grant_attributed_in_period: int
    # All CONFIRMED attributed publications, whatever their date.
    attributed_total: int
    grant_attributed_total: int


class QuarterlyReportResponse(BaseModel):
    year: int
    quarter: int
    # The resource filter, when one was applied.
    resource_id: int | None
    resource_name: str | None
    publications: list[PublicationResponse]
    # CONFIRMED publications from the year whose date has no month; not in any quarter.
    undated_publications: list[PublicationResponse]
    # CONFIRMED publications with no readable year; not in any report period.
    no_date_publications: list[PublicationResponse]
    # The quarter's publications that have resource attributions, in the same order.
    attributed_publications: list[AttributedPublication]
    attribution_summary: AttributionSummary
