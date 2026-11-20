from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.publication import Publication


def save_publications(
    db: Session,
    source_orcid: str | None,
    publications: list[dict],
    source_researcher_id: int | None = None,
) -> int:
    new_count = 0

    for data in publications:
        pmid = str(data["pmid"])

        existing = db.scalar(
            select(Publication)
            .where(Publication.pmid == pmid)
        )

        if existing is not None:
            continue

        publication = Publication(
            pmid=pmid,
            title=data["title"],
            authors=data["authors"],
            journal=data.get("journal"),
            publication_date=data.get("publication_date"),
            **{part: data.get(part) for part in ("publication_year", "publication_month", "publication_day")},
            doi=data.get("doi"),
            abstract=data.get("abstract"),
            first_discovered_by_orcid=source_orcid,
            first_discovered_researcher_id=source_researcher_id,
            status="PENDING",
        )

        db.add(publication)
        db.flush()

        new_count += 1

    db.commit()

    return new_count
