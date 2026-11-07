from fastapi import APIRouter, Depends, HTTPException
from app.enums import ResourceCriticality
from sqlalchemy import select, func, case
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.publication import Publication
from app.models.resource import Resource
from app.models.publication_resource import PublicationResource
from app.schemas.attribution import (
    ResourceAttributionResponse,
    ResourceImpactSummary,
    ResourcePublicationAttribution,
)
from app.schemas.publication import PublicationResponse
from app.schemas.resource import ResourceResponse

router = APIRouter(tags=["Attributions"])


@router.get("/publications/{publication_id}/resources", response_model=list[ResourceResponse])
def publication_resources_list(publication_id: int, db: Session = Depends(get_db)):
    if db.get(Publication, publication_id) is None:
        raise HTTPException(404, "Publication not found")
    stmt = (select(Resource).join(PublicationResource, Resource.id == PublicationResource.resource_id)
            .where(PublicationResource.publication_id == publication_id).order_by(Resource.id))
    return db.scalars(stmt).all()


@router.get("/resources/{resource_id}/publications", response_model=list[PublicationResponse])
def resource_publications_list(resource_id: int, db: Session = Depends(get_db)):
    if db.get(Resource, resource_id) is None:
        raise HTTPException(404, "Resource not found")
    stmt = (select(Publication).join(PublicationResource, Publication.id == PublicationResource.publication_id)
            .where(PublicationResource.resource_id == resource_id).order_by(Publication.id))
    return db.scalars(stmt).all()


@router.get("/publications/{publication_id}/attributions", response_model=list[ResourceAttributionResponse])
def publication_attributions(publication_id: int, db: Session = Depends(get_db)):
    if db.get(Publication, publication_id) is None:
        raise HTTPException(404, "Publication not found")
    rows = db.execute(
        select(Resource.id, Resource.name, PublicationResource.criticality)
        .join(PublicationResource, Resource.id == PublicationResource.resource_id)
        .where(PublicationResource.publication_id == publication_id)
        .order_by(Resource.id)
    ).all()
    return [ResourceAttributionResponse(resource_id=rid, resource_name=name, criticality=crit) for rid, name, crit in rows]


@router.get("/attributions/summary", response_model=list[ResourceImpactSummary])
def resource_impact_summary(db: Session = Depends(get_db)):
    """Count confirmed publication-resource pairs by resource and criticality.

    Include resources with zero attributions. The join table has a composite
    PK, so each publication contributes at most one count per resource.
    """
    stats = (
        select(
            PublicationResource.resource_id.label("resource_id"),
            func.count(PublicationResource.publication_id).label("publication_count"),
            func.sum(case((PublicationResource.criticality == ResourceCriticality.CRITICAL.value, 1), else_=0)).label("critical_count"),
            func.sum(case((PublicationResource.criticality == ResourceCriticality.SIGNIFICANT.value, 1), else_=0)).label("significant_count"),
            func.sum(case((PublicationResource.criticality == ResourceCriticality.MINOR.value, 1), else_=0)).label("minor_count"),
        )
        .group_by(PublicationResource.resource_id)
        .subquery()
    )
    rows = db.execute(
        select(
            Resource.id,
            Resource.name,
            Resource.type,
            Resource.is_active,
            func.coalesce(stats.c.publication_count, 0),
            func.coalesce(stats.c.critical_count, 0),
            func.coalesce(stats.c.significant_count, 0),
            func.coalesce(stats.c.minor_count, 0),
        )
        .outerjoin(stats, Resource.id == stats.c.resource_id)
        .order_by(Resource.name, Resource.id)
    ).all()
    return [
        ResourceImpactSummary(
            resource_id=rid,
            resource_name=name,
            resource_type=resource_type,
            is_active=is_active,
            publication_count=total,
            critical_count=critical,
            significant_count=significant,
            minor_count=minor,
        )
        for rid, name, resource_type, is_active, total, critical, significant, minor in rows
    ]


@router.get("/resources/{resource_id}/attributions", response_model=list[ResourcePublicationAttribution])
def resource_attribution_details(resource_id: int, db: Session = Depends(get_db)):
    """Show the publications and criticality confirmed for one resource."""
    if db.get(Resource, resource_id) is None:
        raise HTTPException(404, "Resource not found")
    rows = db.execute(
        select(
            Publication.id,
            Publication.pmid,
            Publication.title,
            Publication.publication_date,
            PublicationResource.criticality,
        )
        .join(PublicationResource, Publication.id == PublicationResource.publication_id)
        .where(PublicationResource.resource_id == resource_id)
        .order_by(Publication.id)
    ).all()
    return [
        ResourcePublicationAttribution(
            publication_id=pid,
            pmid=pmid,
            title=title,
            publication_date=publication_date,
            criticality=criticality,
        )
        for pid, pmid, title, publication_date, criticality in rows
    ]
