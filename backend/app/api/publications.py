
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.publication import Publication
from app.models.researcher import Researcher
from app.schemas.publication import (
    PublicationResponse,
    PublicationStatus,
)
from app.services.pubmed import discover_publications
from app.services.publications import save_publications


router = APIRouter(
    prefix="/publications",
    tags=["Publications"],
)


@router.get("", response_model=list[PublicationResponse])
def list_publications(
    status: PublicationStatus | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    stmt = select(Publication)

    if status is not None:
        stmt = stmt.where(Publication.status == status)

    stmt = (
        stmt.order_by(Publication.id.desc())
        .offset(offset)
        .limit(limit)
    )

    return db.scalars(stmt).all()


@router.post("/discover")
def discover_for_researchers(db: Session = Depends(get_db)):
    researchers = db.scalars(
        select(Researcher)
        .order_by(Researcher.id)
    ).all()

    results = []
    total_found = 0
    total_new = 0
    failures = []

    for researcher in researchers:
        try:
            publications = discover_publications(researcher.orcid)
            new_count = save_publications(
                db=db,
                source_orcid=researcher.orcid,
                publications=publications,
            )
            total_found += len(publications)
            total_new += new_count
            results.append({
                "researcher": researcher.name,
                "found": len(publications),
                "new": new_count,
            })
        except Exception as exc:
            db.rollback()
            failures.append({
                "researcher": researcher.name,
                "error": str(exc),
            })

    return {
        "researchers_searched": len(researchers),
        "publications_found": total_found,
        "new_publications": total_new,
        "results": results,
        "failures": failures,
    }


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
