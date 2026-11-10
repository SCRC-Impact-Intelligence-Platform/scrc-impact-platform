"""First discoverer is explicit even when they have no ORCID."""
import unittest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from app.database import Base
from app.models.researcher import Researcher
from app.models.publication import Publication
from app.services.publications import save_publications


class DiscoverySourceTests(unittest.TestCase):
    def test_name_discovery_tracks_researcher_id_and_deduplicates(self):
        engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        Base.metadata.create_all(engine)
        try:
            with Session(engine) as db:
                db.add(Researcher(name='Example Person', email='test@example.edu', orcid=None))
                db.commit()
                researcher_id = db.scalar(select(Researcher.id))
                papers = [{'pmid':'101', 'title':'Paper', 'authors':['Person E']}]
                self.assertEqual(save_publications(db, None, papers, source_researcher_id=researcher_id), 1)
                self.assertEqual(save_publications(db, None, papers, source_researcher_id=researcher_id), 0)
                found = db.scalar(select(Publication))
                self.assertEqual(found.first_discovered_researcher_id, researcher_id)
                self.assertIsNone(found.first_discovered_by_orcid)
        finally:
            engine.dispose()
