
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.enums import PublicationConfidence
from app.models.publication import Publication
from app.schemas.publication import (
    PublicationResponse,
    PublicationStatus,
)


router = APIRouter(
    prefix="/publications",
    tags=["Publications"],
)


@router.get("", response_model=list[PublicationResponse])
def list_publications(
    status: PublicationStatus | None = None,
    confidence: PublicationConfidence | None = None,
    researcher_id: int | None = Query(default=None, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    stmt = select(Publication)

    if status is not None:
        stmt = stmt.where(Publication.status == status)

    if researcher_id is not None:
        stmt = stmt.where(Publication.first_discovered_researcher_id == researcher_id)

    if confidence == PublicationConfidence.HIGH:
        stmt = stmt.where(Publication.first_discovered_by_orcid.is_not(None))
    elif confidence == PublicationConfidence.LOW:
        stmt = stmt.where(Publication.first_discovered_by_orcid.is_(None))

    stmt = (
        stmt.order_by(Publication.id.desc())
        .offset(offset)
        .limit(limit)
    )

    return db.scalars(stmt).all()


@router.get(
    "/{publication_id}",
    response_model=PublicationResponse,
)
def get_publication(
    publication_id: int,
    db: Session = Depends(get_db),
):
    publication = db.get(Publication, publication_id)

    if publication is None:
        raise HTTPException(
            status_code=404,
            detail="Publication not found",
        )

    return publication
