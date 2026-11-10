"""API regression tests for resource-centric attribution summaries."""
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.api.attributions import router
from app.models.researcher import Researcher  # noqa: F401  (foreign-key registration)
from app.models.resource import Resource
from app.models.publication import Publication
from app.models.publication_resource import PublicationResource


class ResourceImpactTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.db.add_all([
            Resource(id=1, name="Machine A", type="EQUIPMENT", is_active=True),
            Resource(id=2, name="Machine B", type="EQUIPMENT", is_active=True),
            Resource(id=3, name="Former Machine", type="EQUIPMENT", is_active=False),
            Publication(id=10, pmid="100", title="First paper", authors=[], status="CONFIRMED"),
            Publication(id=11, pmid="101", title="Second paper", authors=[], status="CONFIRMED"),
            Publication(id=12, pmid="102", title="Other only", authors=[], status="NEEDS_REVIEW"),
        ])
        self.db.flush()
        self.db.add_all([
            PublicationResource(publication_id=10, resource_id=1, criticality="CRITICAL"),
            PublicationResource(publication_id=11, resource_id=1, criticality="SIGNIFICANT"),
            PublicationResource(publication_id=11, resource_id=2, criticality="MINOR"),
        ])
        self.db.commit()
        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_db] = lambda: self.db
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.db.close()
        self.engine.dispose()

    def test_summary_includes_zero_and_inactive_resources(self):
        res = self.client.get("/attributions/summary")
        self.assertEqual(res.status_code, 200)
        items = {r["resource_name"]: r for r in res.json()}
        self.assertEqual(items["Machine A"]["publication_count"], 2)
        self.assertEqual(items["Machine A"]["critical_count"], 1)
        self.assertEqual(items["Machine A"]["significant_count"], 1)
        self.assertEqual(items["Machine A"]["minor_count"], 0)
        self.assertEqual(items["Machine B"]["publication_count"], 1)
        self.assertEqual(items["Machine B"]["minor_count"], 1)
        self.assertEqual(items["Former Machine"]["publication_count"], 0)
        self.assertFalse(items["Former Machine"]["is_active"])
        self.assertEqual(sum(x["publication_count"] for x in items.values()), 3)

    def test_details_lists_actual_publications_and_criticality(self):
        res = self.client.get("/resources/1/attributions")
        self.assertEqual(res.status_code, 200)
        self.assertEqual([(r["pmid"], r["criticality"]) for r in res.json()],
                         [("100", "CRITICAL"), ("101", "SIGNIFICANT")])
        self.assertEqual(self.client.get("/resources/3/attributions").json(), [])

    def test_unknown_resource_returns_404(self):
        self.assertEqual(self.client.get("/resources/99/attributions").status_code, 404)

    def test_existing_publication_endpoint_unchanged(self):
        res = self.client.get("/publications/10/attributions")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()[0]["criticality"], "CRITICAL")


if __name__ == "__main__":
    unittest.main()
