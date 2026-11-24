"""Assembles the data behind a report and its exports."""

from sqlalchemy import Select, and_, case, func, or_, select
from sqlalchemy.orm import Session

from app.enums import PublicationStatus, ResourceType
from app.models.publication import Publication
from app.models.publication_resource import PublicationResource
from app.models.researcher import Researcher
from app.models.resource import Resource
from app.services.periods import MonthRange


def report_data(db: Session, period: MonthRange, resource: Resource | None = None) -> dict:
    """Verified (CONFIRMED) publications whose PubMed date falls in a range of months.

    Uses the stored date parts (a date range counts in the month it starts in).
    A publication dated only by year ("2026", "2026 Spring") is included when the
    period covers that whole calendar year. When the period covers the year only in
    part, it can't be placed, so it is returned in ``undated_publications``.
    Publications with no readable year at all belong to no period, so they are
    returned as ``no_date_publications`` on every report.

    With a ``resource``, every list and count only covers publications attributed to it.
    """
    P = Publication
    confirmed = select(P).where(P.status == PublicationStatus.CONFIRMED)
    if resource is not None:
        confirmed = confirmed.where(P.id.in_(_attributed_to(resource)))
    month_index = P.publication_year * 12 + P.publication_month - 1
    full_years = period.full_years()
    partial_years = sorted(set(period.touched_years()) - set(full_years))
    in_period = confirmed.where(or_(
        month_index.between(period.start_index, period.end_index),
        and_(P.publication_month.is_(None), P.publication_year.in_(full_years)),
    ))
    publications = db.scalars(
        in_period.order_by(
            P.publication_year,
            # Year-only dates last within their year, and a missing day first within its month.
            # CASE is portable (no NULLS FIRST on SQL Server).
            case((P.publication_month.is_(None), 13), else_=P.publication_month),
            case((P.publication_day.is_(None), 0), else_=1),
            P.publication_day,
            P.id,
        )
    ).all()
    undated = db.scalars(
        confirmed.where(P.publication_month.is_(None), P.publication_year.in_(partial_years)).order_by(P.id)
    ).all()
    no_date = db.scalars(confirmed.where(P.publication_year.is_(None)).order_by(P.id)).all()
    # A subquery, not a literal id list: SQL Server allows at most 2100 bound parameters.
    resources = _attributions(db, in_period.with_only_columns(P.id))
    attributed = [p for p in publications if p.id in resources]
    attributed_total, grant_attributed_total = _attributed_counts(db, resource)
    return {
        "start": period.start,
        "end": period.end,
        "period_label": period.label(),
        "resource_id": resource.id if resource else None,
        "resource_name": resource.name if resource else None,
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


def _attributed_to(resource: Resource) -> Select:
    return select(PublicationResource.publication_id).where(PublicationResource.resource_id == resource.id)


def _attributed_counts(db: Session, resource: Resource | None = None) -> tuple[int, int]:
    """All-time CONFIRMED publications attributed to any resource, and to a grant (FUNDING).

    With a ``resource``, only publications attributed to that resource are counted.
    """
    publication_id = PublicationResource.publication_id
    query = (
        select(
            func.count(func.distinct(publication_id)),
            func.count(func.distinct(case((Resource.type == ResourceType.FUNDING.value, publication_id)))),
        )
        .select_from(PublicationResource)
        .join(Resource, Resource.id == PublicationResource.resource_id)
        .join(Publication, Publication.id == publication_id)
        .where(Publication.status == PublicationStatus.CONFIRMED)
    )
    if resource is not None:
        query = query.where(Publication.id.in_(_attributed_to(resource)))
    total, grants = db.execute(query).one()
    return total, grants


def researcher_names(db: Session, publications: list[Publication]) -> dict[int, str]:
    ids = {p.first_discovered_researcher_id for p in publications} - {None}
    if not ids:
        return {}
    return dict(db.execute(select(Researcher.id, Researcher.name).where(Researcher.id.in_(ids))).all())
