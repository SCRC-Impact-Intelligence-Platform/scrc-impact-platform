import unittest

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.database import Base, get_db
import app.models.forms  # noqa: F401
import app.models.publication  # noqa: F401
import app.models.publication_resource  # noqa: F401
import app.models.researcher  # noqa: F401
import app.models.resource  # noqa: F401
from app.api.researchers import router
from app.models.researcher import Researcher

class ResearcherImportTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        app = FastAPI()
        app.include_router(router)
        def session():
            with Session(self.engine) as db:
                yield db
        app.dependency_overrides[get_db] = session
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.engine.dispose()

    def upload(self, content):
        return self.client.post('/researchers/import', content=content, headers={'content-type':'text/csv'})

    def all(self):
        with Session(self.engine) as db:
            return db.scalars(select(Researcher).order_by(Researcher.id)).all()

    def test_create_then_idempotent(self):
        csv = 'name,email,orcid\nAileen,a@example.org,0000-0002-8203-8891\nMuhammad,m@example.org,N/A\n'
        self.assertEqual(self.upload(csv).json(), {'created':2,'skipped':0})
        self.assertEqual(self.upload(csv).json(), {'created':0,'skipped':2})
        self.assertEqual(len(self.all()),2)

    def test_existing_email_skips_name_change(self):
        self.upload('name,email,orcid\nAileen,a@example.org,0000-0002-8203-8891\n')
        result = self.upload('email,name,orcid\na@example.org,Aileen J.,0000-0002-8203-8891\n')
        self.assertEqual(result.json(), {'created': 0, 'skipped': 1})
        self.assertEqual(self.all()[0].name, 'Aileen')

    def test_existing_email_skips_orcid_change(self):
        self.upload('name,email,orcid\nA,a@example.org,\n')
        result = self.upload('name,email,orcid\nA,a@example.org,0000-0002-8203-8891\n')
        self.assertEqual(result.json(), {'created': 0, 'skipped': 1})
        self.assertIsNone(self.all()[0].orcid)

    def test_different_email_creates_new_record(self):
        self.upload('name,email,orcid\nA,a@example.org,\n')
        result = self.upload('name,email,orcid\nB,b@example.org,\n')
        self.assertEqual(result.json(), {'created': 1, 'skipped': 0})
        self.assertEqual(len(self.all()), 2)

    def test_missing_email_and_input_duplicates_rejected(self):
        self.assertEqual(self.upload('name,email,orcid\nA,,0000-0002-8203-8891\n').status_code,422)
        self.assertEqual(self.upload('name,email,orcid\nA,a@example.org,\nB,a@example.org,\n').json(), {'created': 1, 'skipped': 1})
        self.assertEqual(len(self.all()),1)

    def test_duplicate_email_rejected_by_database(self):
        self.upload('name,email,orcid\nA,a@example.org,\n')
        response = self.client.post('/researchers', json={
            'name': 'Another person', 'email': 'a@example.org', 'orcid': None,
        })
        self.assertEqual(response.status_code, 409)
        self.assertEqual(len(self.all()), 1)

    def test_reject_wrong_media_type(self):
        response=self.client.post('/researchers/import',json={'name':'A'})
        self.assertEqual(response.status_code,415)

    def test_no_orcid_preserves_existing_orcid(self):
        self.upload('name,email,orcid\nA,a@example.org,0000-0002-8203-8891\n')
        self.upload('name,email,orcid\nAnother Name,a@example.org,\n')
        self.assertEqual(self.all()[0].orcid,'0000-0002-8203-8891')

    def test_existing_email_skips_every_field_case_insensitively(self):
        self.upload('name,email,orcid\nOriginal,Case@Example.Org,0000-0002-8203-8891\n')
        result = self.upload('name,email,orcid\nReplacement,CASE@example.org,\n')
        self.assertEqual(result.json(), {'created': 0, 'skipped': 1})
        saved = self.all()[0]
        self.assertEqual(saved.name, 'Original')
        self.assertEqual(saved.email, 'case@example.org')
        self.assertEqual(saved.orcid, '0000-0002-8203-8891')
