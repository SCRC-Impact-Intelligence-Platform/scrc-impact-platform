import argparse
from datetime import date
from sqlalchemy import select
from app.database import SessionLocal
from app.models.researcher import Researcher
from app.services.pubmed import discover_publications, months_ago
from app.services.publications import save_publications


def main(months: int = 3):
    if months < 1:
        raise ValueError("--months must be a positive integer")
    end = date.today()
    start = months_ago(end, months)
    print(f"Publication date window: {start} to {end}")
    with SessionLocal() as db:
        researchers = db.scalars(select(Researcher).where(Researcher.is_active.is_(True)).order_by(Researcher.id)).all()
        print(f"Found {len(researchers)} active researchers")
        total = 0
        failures = 0
        for researcher in researchers:
            method = "ORCID" if researcher.orcid else "NAME (review required)"
            print(f"Researcher: {researcher.name} (search: {method})")
            try:
                papers = discover_publications(researcher.orcid, name=researcher.name, start_date=start, end_date=end)
                new = save_publications(db=db, source_orcid=researcher.orcid, source_researcher_id=researcher.id, publications=papers)
                total += new
                print(f"Found: {len(papers)}; new: {new}; with DOI: {sum(bool(p['doi']) for p in papers)}; with abstract: {sum(bool(p['abstract']) for p in papers)}")
            except Exception as exc:
                db.rollback()
                failures += 1
                print(f"FAILED for {researcher.name}: {type(exc).__name__}: {exc}")
        print(f"Total new publications: {total}; failed researchers: {failures}")
        if failures:
            raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Discover recent PubMed publications")
    parser.add_argument("--months", type=int, default=3, help="Lookback period in months (default: 3)")
    args = parser.parse_args()
    if args.months < 1:
        parser.error("--months must be a positive integer")
    main(months=args.months)
