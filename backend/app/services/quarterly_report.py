"""Assembles the data behind the quarterly report and its exports."""

from sqlalchemy import case, select
from sqlalchemy.orm import Session

from app.enums import PublicationStatus
from app.models.publication import Publication
from app.models.researcher import Researcher


def quarterly_report_data(db: Session, year: int, quarter: int) -> dict:
    """Verified (CONFIRMED) publications whose PubMed date falls in a calendar quarter.

    Uses the stored date parts (a date range counts in the quarter it starts in).
    Publications from ``year`` with no month ("2026", "2026 Spring") can't be
    placed in a quarter; they are returned separately as ``undated_publications``.
    Publications with no readable year at all belong to no year, so they are
    returned as ``no_date_publications`` on every report.
    """
    P = Publication
    confirmed = select(P).where(P.status == PublicationStatus.CONFIRMED)
    confirmed_in_year = confirmed.where(P.publication_year == year)
    first_month = (quarter - 1) * 3 + 1
    publications = db.scalars(
        confirmed_in_year
        .where(P.publication_month.between(first_month, first_month + 2))
        # Missing day sorts first within its month; CASE is portable (no NULLS FIRST on SQL Server).
        .order_by(P.publication_month, case((P.publication_day.is_(None), 0), else_=1), P.publication_day, P.id)
    ).all()
    undated = db.scalars(confirmed_in_year.where(P.publication_month.is_(None)).order_by(P.id)).all()
    no_date = db.scalars(confirmed.where(P.publication_year.is_(None)).order_by(P.id)).all()
    return {
        "year": year,
        "quarter": quarter,
        "publications": publications,
        "undated_publications": undated,
        "no_date_publications": no_date,
    }


def researcher_names(db: Session, publications: list[Publication]) -> dict[int, str]:
    ids = {p.first_discovered_researcher_id for p in publications} - {None}
    if not ids:
        return {}
    return dict(db.execute(select(Researcher.id, Researcher.name).where(Researcher.id.in_(ids))).all())
