from sqlalchemy import select

from app.database import Base, engine, SessionLocal
from app.models.researcher import Researcher
from app.models.publication import Publication

from app.services.pubmed import discover_publications
from app.services.publications import save_publications


def main():
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        researchers = db.scalars(
            select(Researcher)
            .where(Researcher.is_active.is_(True))
            .order_by(Researcher.id)
        ).all()

        print(f"Found {len(researchers)} active researchers")

        total_new = 0

        for researcher in researchers:
            print("-" * 60)
            print(f"Researcher: {researcher.name}")
            print(f"ORCID: {researcher.orcid}")

            try:
                publications = discover_publications(
                    researcher.orcid
                )

                new_count = save_publications(
                    db=db,
                    source_orcid=researcher.orcid,
                    publications=publications,
                )

                total_new += new_count

                print(f"Found: {len(publications)}")
                print(f"New: {new_count}")

            except Exception as exc:
                db.rollback()
                print(f"Failed: {exc}")

        print("-" * 60)
        print(f"Total new publications: {total_new}")

    print("Discovery completed!")


if __name__ == "__main__":
    main()
