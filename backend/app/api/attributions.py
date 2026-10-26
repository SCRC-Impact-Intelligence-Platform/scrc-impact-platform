from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.publication import Publication
from app.models.resource import Resource
from app.models.publication_resource import publication_resources
from app.schemas.publication import PublicationResponse
from app.schemas.resource import ResourceResponse

router = APIRouter(tags=["Attributions"])


@router.get("/publications/{publication_id}/resources", response_model=list[ResourceResponse])
def publication_resources_list(publication_id: int, db: Session = Depends(get_db)):
    if db.get(Publication, publication_id) is None:
        raise HTTPException(404, "Publication not found")
    stmt = (select(Resource).join(publication_resources, Resource.id == publication_resources.c.resource_id)
            .where(publication_resources.c.publication_id == publication_id).order_by(Resource.id))
    return db.scalars(stmt).all()


@router.get("/resources/{resource_id}/publications", response_model=list[PublicationResponse])
def resource_publications_list(resource_id: int, db: Session = Depends(get_db)):
    if db.get(Resource, resource_id) is None:
        raise HTTPException(404, "Resource not found")
    stmt = (select(Publication).join(publication_resources, Publication.id == publication_resources.c.publication_id)
            .where(publication_resources.c.resource_id == resource_id).order_by(Publication.id))
    return db.scalars(stmt).all()
