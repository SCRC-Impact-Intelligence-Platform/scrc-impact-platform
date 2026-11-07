"""Response schemas for publication-resource attribution APIs."""

from pydantic import BaseModel

from app.enums import ResourceCriticality, ResourceType


class ResourceAttributionResponse(BaseModel):
    resource_id: int
    resource_name: str
    criticality: ResourceCriticality


class ResourceImpactSummary(BaseModel):
    resource_id: int
    resource_name: str
    resource_type: ResourceType
    is_active: bool
    publication_count: int
    critical_count: int
    significant_count: int
    minor_count: int


class ResourcePublicationAttribution(BaseModel):
    publication_id: int
    pmid: str
    title: str
    publication_date: str | None
    criticality: ResourceCriticality
