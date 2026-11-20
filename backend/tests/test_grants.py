"""Grants API and the grants-received section of the quarterly report."""

import re
import unittest
import zipfile
from datetime import date
from decimal import Decimal
from io import BytesIO

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.grants import router as grants_router
from app.api.reports import router as reports_router
from app.database import Base, get_db
from app.models.grant import Grant
from app.models.publication_resource import PublicationResource  # noqa: F401  (foreign-key registration)
from app.models.researcher import Researcher
from app.models.resource import Resource  # noqa: F401
from app.services.report_export import grant_line


class GrantTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as db:
            db.add(Researcher(id=1, name="Tran Nguyen", email="t@example.edu"))
            db.add_all([
                Grant(title="Q4 start", funder="NIH", amount=Decimal("1250000"), award_date=date(2026, 10, 1), researcher_id=1),
                Grant(title="Q4 end", funder="CIRM", award_date=date(2026, 12, 31)),
                Grant(title="Q3", funder="NIH", award_date=date(2026, 9, 30)),
                Grant(title="Next year", funder="NIH", award_date=date(2027, 1, 1)),
            ])
            db.commit()
        app = FastAPI()
        app.include_router(grants_router)
        app.include_router(reports_router)

        def test_db():
            with Session(self.engine) as db:
                yield db

        app.dependency_overrides[get_db] = test_db
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.engine.dispose()

    def test_create_list_delete(self):
        created = self.client.post("/grants", json={
            "title": "Organoid core", "funder": "CIRM", "amount": "500000.50", "award_date": "2026-11-02",
        })
        self.assertEqual(created.status_code, 201, created.text)
        self.assertEqual(Decimal(created.json()["amount"]), Decimal("500000.50"))
        self.assertIn("Organoid core", [g["title"] for g in self.client.get("/grants").json()])
        self.assertEqual(self.client.delete(f"/grants/{created.json()['id']}").status_code, 204)
        self.assertEqual(self.client.delete(f"/grants/{created.json()['id']}").status_code, 404)

    def test_create_validation(self):
        base = {"title": "T", "funder": "F", "award_date": "2026-11-02"}
        self.assertEqual(self.client.post("/grants", json={**base, "researcher_id": 99}).status_code, 422)
        self.assertEqual(self.client.post("/grants", json={**base, "amount": -1}).status_code, 422)
        self.assertEqual(self.client.post("/grants", json={**base, "title": ""}).status_code, 422)

    def test_report_lists_grants_awarded_in_quarter(self):
        grants = self.client.get("/reports/quarterly?year=2026&quarter=4").json()["grants_received"]
        self.assertEqual([g["title"] for g in grants], ["Q4 start", "Q4 end"])  # boundaries included, by date
        self.assertEqual(grants[0]["researcher_name"], "Tran Nguyen")
        self.assertIsNone(grants[1]["researcher_name"])
        self.assertEqual(self.client.get("/reports/quarterly?year=2026&quarter=2").json()["grants_received"], [])

    def test_excel_sheet_only_when_grants(self):
        def sheet_names(quarter):
            response = self.client.get(f"/reports/quarterly/export?year=2026&quarter={quarter}&format=xlsx")
            with zipfile.ZipFile(BytesIO(response.content)) as workbook:
                return re.findall(r'<sheet name="([^"]+)"', workbook.read("xl/workbook.xml").decode())
        self.assertEqual(sheet_names(4)[-1], "Grants received")
        self.assertNotIn("Grants received", sheet_names(2))

    def test_pdf_export(self):
        for quarter in (2, 4):
            response = self.client.get(f"/reports/quarterly/export?year=2026&quarter={quarter}&format=pdf")
            self.assertTrue(response.content.startswith(b"%PDF"))

    def test_grant_line(self):
        self.assertEqual(
            grant_line({"title": "T", "funder": "NIH", "amount": Decimal("1250000"),
                        "award_date": date(2026, 10, 1), "researcher_name": "Tran Nguyen"}),
            "T (NIH) · $1,250,000.00 · awarded Oct 1, 2026 · Tran Nguyen",
        )
        self.assertEqual(
            grant_line({"title": "T", "funder": "CIRM", "amount": None,
                        "award_date": date(2026, 12, 31), "researcher_name": None}),
            "T (CIRM) · awarded Dec 31, 2026",
        )


if __name__ == "__main__":
    unittest.main()
