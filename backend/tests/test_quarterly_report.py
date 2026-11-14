"""Quarterly report: CONFIRMED publications whose stored date falls in the quarter."""

import re
import unittest
import zipfile
from io import BytesIO

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.reports import router
from app.database import Base, get_db
from app.models.publication import Publication
from app.models.publication_resource import PublicationResource
from app.models.resource import Resource
from app.services.citations import format_citations
from app.services.pubdates import date_parts, parse_date


class ParseDateTests(unittest.TestCase):
    def test_formats(self):
        cases = {
            "2026 Oct 12": (2026, 10, 12),
            "2026 Oct": (2026, 10, None),
            "2026 Jan-Feb": (2026, 1, None),
            "2025 Dec-2026 Jan": (2025, 12, None),  # a range is dated by its start
            "2026-03-05": (2026, 3, 5),
            "2026": (2026, None, None),
            "2026 Spring": (2026, None, None),
            "2026 Oct 123": (2026, 10, None),
            "2026 Feb 30": (2026, 2, None),  # impossible day
            "2024 Feb 29": (2024, 2, 29),
            "2026 Apr 31": (2026, 4, None),
            "2026 3rd Quarter": (2026, None, None),
            "2011-12": (2011, None, None),  # year range, not December
            "1998-1999": (1998, None, None),
            "2026 03": (2026, 3, None),
            "2026 03 05": (2026, 3, 5),
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(parse_date(value), expected)
        self.assertIsNone(parse_date(None))
        self.assertIsNone(parse_date("unknown"))

    def test_structured_fields(self):
        from app.services.pubdates import structured_date_parts

        keys = ("publication_year", "publication_month", "publication_day")
        self.assertEqual(structured_date_parts("2026", "Oct", "12"), dict(zip(keys, (2026, 10, 12))))
        self.assertEqual(structured_date_parts("2026", "3", None), dict(zip(keys, (2026, 3, None))))
        self.assertEqual(structured_date_parts("2026", "Feb", "30"), dict(zip(keys, (2026, 2, None))))
        self.assertEqual(structured_date_parts("2026", None, None), dict(zip(keys, (2026, None, None))))
        self.assertIsNone(structured_date_parts(None, "Oct", None))

    def test_date_parts(self):
        self.assertEqual(
            date_parts("2026 Oct"), {"publication_year": 2026, "publication_month": 10, "publication_day": None}
        )


def _pub(pmid, date, status="CONFIRMED"):
    return Publication(pmid=pmid, title=pmid, authors=[], status=status, publication_date=date, **date_parts(date))


class QuarterlyReportEndpointTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as db:
            db.add_all([
                _pub("1", "2026 Feb 3"),
                _pub("2", "2026 Jan"),
                _pub("3", "2026 Jan 9", status="PENDING"),
                _pub("4", "2026 Apr 1"),
                _pub("5", "2025 Jan 1"),
                _pub("6", "2026"),
                _pub("7", "2025 Summer"),
                _pub("8", "2026 Feb 12"),
                _pub("9", "2026 Mar 31"),
                _pub("10", "2025 Dec-2026 Jan"),
                _pub("11", None),
                _pub("12", "Winter 2025-2026"),
                _pub("13", None, status="PENDING"),
            ])
            db.add_all([
                Resource(id=1, name="Flow Cytometer", type="EQUIPMENT"),
                Resource(id=2, name="CIRM Grant", type="FUNDING"),
            ])
            db.flush()
            ids = {p.pmid: p.id for p in db.scalars(select(Publication))}
            db.add_all([
                PublicationResource(publication_id=ids["1"], resource_id=1, criticality="CRITICAL"),
                PublicationResource(publication_id=ids["1"], resource_id=2, criticality="MINOR"),
                PublicationResource(publication_id=ids["9"], resource_id=1, criticality="SIGNIFICANT"),
                PublicationResource(publication_id=ids["4"], resource_id=2, criticality="CRITICAL"),  # Q2
                PublicationResource(publication_id=ids["6"], resource_id=2, criticality="MINOR"),  # no month
                PublicationResource(publication_id=ids["3"], resource_id=2, criticality="MINOR"),  # not CONFIRMED
            ])
            db.commit()
        app = FastAPI()
        app.include_router(router)

        def test_db():
            with Session(self.engine) as db:
                yield db

        app.dependency_overrides[get_db] = test_db
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.engine.dispose()

    def report(self, year, quarter):
        response = self.client.get(f"/reports/quarterly?year={year}&quarter={quarter}")
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_lists_confirmed_in_quarter_in_date_order(self):
        body = self.report(2026, 1)
        self.assertEqual((body["year"], body["quarter"]), (2026, 1))
        # Missing day first, then by day ("Feb 3" before "Feb 12", not text order).
        self.assertEqual([p["pmid"] for p in body["publications"]], ["2", "1", "8", "9"])
        self.assertEqual([p["pmid"] for p in body["undated_publications"]], ["6"])
        self.assertEqual([p["pmid"] for p in body["no_date_publications"]], ["11", "12"])

    def test_attributed_publications_and_summary(self):
        body = self.report(2026, 1)
        attributed = body["attributed_publications"]
        # Same order as the quarter's list; unattributed publications left out.
        self.assertEqual([a["publication"]["pmid"] for a in attributed], ["1", "9"])
        self.assertEqual(
            [(r["resource_name"], r["resource_type"], r["criticality"]) for r in attributed[0]["resources"]],
            [("CIRM Grant", "FUNDING", "MINOR"), ("Flow Cytometer", "EQUIPMENT", "CRITICAL")],
        )
        self.assertEqual(body["attribution_summary"], {
            "attributed_in_period": 2,
            "grant_attributed_in_period": 1,
            # All CONFIRMED attributed publications, any date; PENDING "3" excluded.
            "attributed_total": 4,
            "grant_attributed_total": 3,
        })

    def test_summary_with_no_attributions_in_period(self):
        body = self.report(2025, 4)
        self.assertEqual(body["attributed_publications"], [])
        self.assertEqual(body["attribution_summary"]["attributed_in_period"], 0)
        self.assertEqual(body["attribution_summary"]["attributed_total"], 4)

    def test_range_counts_in_starting_quarter(self):
        self.assertEqual([p["pmid"] for p in self.report(2025, 4)["publications"]], ["10"])

    def test_excel_export(self):
        with Session(self.engine) as db:
            hostile = _pub("99", "2026 Mar 2")
            hostile.title = "=HYPERLINK(1)"
            db.add(hostile)
            db.commit()
        response = self.client.get("/reports/quarterly/export?year=2026&quarter=1&format=xlsx")
        self.assertEqual(response.status_code, 200)
        self.assertIn("verified-publications-2026-Q1.xlsx", response.headers["content-disposition"])
        with zipfile.ZipFile(BytesIO(response.content)) as workbook:
            strings = workbook.read("xl/sharedStrings.xml").decode()
            sheets = [workbook.read(name).decode() for name in workbook.namelist()
                      if name.startswith("xl/worksheets/sheet")]
            workbook_xml = workbook.read("xl/workbook.xml").decode()
        # Data only: the publication list stays the first sheet; summary counts are in the PDF.
        names = re.findall(r'<sheet name="([^"]+)"', workbook_xml)
        self.assertEqual(names, ["Publications", "Attributed publications", "Not in a quarter"])
        self.assertIn("=HYPERLINK(1)", strings)
        self.assertIn("Flow Cytometer (Critical)", strings)
        for sheet in sheets:
            self.assertNotIn("<f>", sheet)  # stored as text, never as a formula

    def test_pdf_export(self):
        with Session(self.engine) as db:
            risky = _pub("98", "2026 Mar 3")
            risky.title = "<img src='http://example.invalid/x'> & co"
            db.add(risky)
            db.commit()
        response = self.client.get("/reports/quarterly/export?year=2026&quarter=1&format=pdf")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_export_with_no_results(self):
        for fmt in ("xlsx", "pdf"):
            self.assertEqual(self.client.get(f"/reports/quarterly/export?year=1999&quarter=1&format={fmt}").status_code, 200)

    def test_invalid_export_format_rejected(self):
        self.assertEqual(self.client.get("/reports/quarterly/export?year=2026&quarter=1&format=doc").status_code, 422)

    def test_invalid_quarter_rejected(self):
        self.assertEqual(self.client.get("/reports/quarterly?year=2026&quarter=5").status_code, 422)


class CitationTests(unittest.TestCase):
    def test_nlm_citation(self):
        p = Publication(pmid="123", title="Stem cell repair", authors=["Lee AB", "Garcia J", "Study Group"],
                        journal="Journal X", doi="10.1234/test", publication_year=2026, publication_month=10)
        citation = format_citations([p])["123"]
        self.assertTrue(citation.startswith("Lee AB, Garcia J"), citation)
        self.assertIn("Stem cell repair", citation)
        self.assertIn("10.1234/test", citation)
        self.assertIn("2026 Oct.", citation)

    def test_sparse_publication(self):
        p = Publication(pmid="7", title="Only a title", authors=[])
        self.assertIn("Only a title", format_citations([p])["7"])
