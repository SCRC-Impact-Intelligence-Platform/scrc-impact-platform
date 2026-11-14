"""Assembles the data behind the quarterly report and its exports."""

from sqlalchemy import Select, case, func, select
from sqlalchemy.orm import Session

from app.enums import PublicationStatus, ResourceType
from app.models.publication import Publication
from app.models.publication_resource import PublicationResource
from app.models.researcher import Researcher
from app.models.resource import Resource


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
    in_quarter = confirmed_in_year.where(P.publication_month.between(first_month, first_month + 2))
    publications = db.scalars(
        in_quarter
        # Missing day sorts first within its month; CASE is portable (no NULLS FIRST on SQL Server).
        .order_by(P.publication_month, case((P.publication_day.is_(None), 0), else_=1), P.publication_day, P.id)
    ).all()
    undated = db.scalars(confirmed_in_year.where(P.publication_month.is_(None)).order_by(P.id)).all()
    no_date = db.scalars(confirmed.where(P.publication_year.is_(None)).order_by(P.id)).all()
    # A subquery, not a literal id list: SQL Server allows at most 2100 bound parameters.
    resources = _attributions(db, in_quarter.with_only_columns(P.id))
    attributed = [p for p in publications if p.id in resources]
    attributed_total, grant_attributed_total = _attributed_counts(db)
    return {
        "year": year,
        "quarter": quarter,
        "publications": publications,
        "undated_publications": undated,
        "no_date_publications": no_date,
        "attributed_publications": [
            {"publication": p, "resources": resources[p.id]} for p in attributed
        ],
        "attribution_summary": {
            "attributed_in_period": len(attributed),
            "grant_attributed_in_period": sum(1 for p in attributed if any(map(is_grant, resources[p.id]))),
            "attributed_total": attributed_total,
            "grant_attributed_total": grant_attributed_total,
        },
    }


def is_grant(resource: dict) -> bool:
    """Whether an attributed resource (as returned in ``attributed_publications``) is a grant."""
    return resource["resource_type"] == ResourceType.FUNDING


def _attributions(db: Session, publication_ids: Select) -> dict[int, list[dict]]:
    """The resources attributed to each publication in the id subquery (unattributed ones absent)."""
    rows = db.execute(
        select(PublicationResource.publication_id, Resource.id, Resource.name, Resource.type,
               PublicationResource.criticality)
        .join(Resource, Resource.id == PublicationResource.resource_id)
        .where(PublicationResource.publication_id.in_(publication_ids))
        .order_by(Resource.name, Resource.id)
    ).all()
    result: dict[int, list[dict]] = {}
    for publication_id, resource_id, name, resource_type, criticality in rows:
        result.setdefault(publication_id, []).append({
            "resource_id": resource_id, "resource_name": name,
            "resource_type": resource_type, "criticality": criticality,
        })
    return result


def _attributed_counts(db: Session) -> tuple[int, int]:
    """All-time CONFIRMED publications attributed to any resource, and to a grant (FUNDING)."""
    publication_id = PublicationResource.publication_id
    total, grants = db.execute(
        select(
            func.count(func.distinct(publication_id)),
            func.count(func.distinct(case((Resource.type == ResourceType.FUNDING.value, publication_id)))),
        )
        .select_from(PublicationResource)
        .join(Resource, Resource.id == PublicationResource.resource_id)
        .join(Publication, Publication.id == publication_id)
        .where(Publication.status == PublicationStatus.CONFIRMED)
    ).one()
    return total, grants


def researcher_names(db: Session, publications: list[Publication]) -> dict[int, str]:
    ids = {p.first_discovered_researcher_id for p in publications} - {None}
    if not ids:
        return {}
    return dict(db.execute(select(Researcher.id, Researcher.name).where(Researcher.id.in_(ids))).all())
