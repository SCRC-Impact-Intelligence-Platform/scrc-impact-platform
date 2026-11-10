"""Confidence filtering must happen in SQL before pagination."""

import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.publications import router
from app.database import Base, get_db
from app.models.publication import Publication


class PublicationConfidenceFilterTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as db:
            db.add_all(
                [
                    Publication(pmid="111", title="ORCID paper", authors=[], status="PENDING", first_discovered_by_orcid="0000-0002-8203-8891"),
                    Publication(pmid="222", title="Name paper", authors=[], status="PENDING", first_discovered_by_orcid=None),
                    Publication(pmid="333", title="Another name paper", authors=[], status="CONFIRMED", first_discovered_by_orcid=None),
                ]
            )
            db.commit()

        self.app = FastAPI()
        self.app.include_router(router)

        def test_db():
            with Session(self.engine) as db:
                yield db

        self.app.dependency_overrides[get_db] = test_db
        self.client = TestClient(self.app)

    def tearDown(self):
        self.client.close()
        self.engine.dispose()

    def test_high_filter_before_pagination(self):
        response = self.client.get('/publications?confidence=HIGH&limit=1&offset=0')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([p['pmid'] for p in response.json()], ['111'])

    def test_low_and_status_filters(self):
        response = self.client.get('/publications?confidence=LOW&status=PENDING')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([p['pmid'] for p in response.json()], ['222'])

    def test_invalid_confidence_rejected(self):
        response = self.client.get('/publications?confidence=MEDIUM')
        self.assertEqual(response.status_code, 422)


if __name__ == '__main__':
    unittest.main()
