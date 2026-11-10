"""Alembic migrations against a real SQL Server (skipped when Docker isn't available)."""

import unittest
import warnings

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError

from app import migrate
from app.database import Base
import app.models.forms  # noqa: F401
import app.models.publication  # noqa: F401
import app.models.publication_resource  # noqa: F401
import app.models.researcher  # noqa: F401
import app.models.resource  # noqa: F401

IMAGE = "mcr.microsoft.com/mssql/server:2022-latest"
INITIAL = "18497563da61"


def _start_container():
    """A running SQL Server container, or None if this machine can't run one."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            from testcontainers.mssql import SqlServerContainer
        container = SqlServerContainer(IMAGE, dialect="mssql+pymssql", dbname="master")
        container.start()
        return container
    except Exception as exc:  # no Docker, or the optional test packages aren't installed
        print(f"Skipping SQL Server migration tests: {exc}")
        return None


class SqlServerMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.container = _start_container()
        if cls.container is None:
            raise unittest.SkipTest("SQL Server container unavailable")
        cls.url = make_url(cls.container.get_connection_url())
        cls.admin = create_engine(cls.url, isolation_level="AUTOCOMMIT")

    @classmethod
    def tearDownClass(cls):
        cls.admin.dispose()
        cls.container.stop()

    def setUp(self):
        with self.admin.connect() as conn:
            conn.execute(text("DROP DATABASE IF EXISTS scrc_test"))
            conn.execute(text("CREATE DATABASE scrc_test"))
        self.engine = create_engine(self.url.set(database="scrc_test"))

    def tearDown(self):
        self.engine.dispose()

    def assert_matches_models(self):
        with self.engine.connect() as conn:
            diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)
        self.assertEqual(diff, [], "migrations and models disagree")

    def test_upgrade_matches_models(self):
        migrate.upgrade(self.engine)
        self.assert_matches_models()
        migrate.check_schema_current(self.engine)

    def test_many_null_orcids_but_no_duplicates(self):
        migrate.upgrade(self.engine)
        insert = text("INSERT INTO researchers (name, email, orcid, is_active) VALUES (:n, 'r@x.org', :o, 1)")
        with self.engine.begin() as conn:
            for name, orcid in (("A", None), ("B", None), ("C", "0000-0002-8203-8891")):
                conn.execute(insert, {"n": name, "o": orcid})
        with self.assertRaises(IntegrityError), self.engine.begin() as conn:
            conn.execute(insert, {"n": "D", "o": "0000-0002-8203-8891"})

    def test_many_form_batches_without_a_form(self):
        migrate.upgrade(self.engine)
        insert = text("INSERT INTO form_batches (state, created_at) VALUES ('CREATING', SYSUTCDATETIME())")
        with self.engine.begin() as conn:
            conn.execute(insert)
            conn.execute(insert)

    def test_startup_check(self):
        with self.assertRaises(RuntimeError):
            migrate.check_schema_current(self.engine)  # empty database
        migrate.upgrade(self.engine, INITIAL)
        with self.assertRaises(RuntimeError):
            migrate.check_schema_current(self.engine)  # behind
        migrate.upgrade(self.engine)
        with self.engine.begin() as conn:
            conn.execute(text("UPDATE alembic_version SET version_num = '9999'"))
        with self.assertLogs("app.migrate", "WARNING"):
            migrate.check_schema_current(self.engine)  # ahead: only warns

    def test_upgrade_refuses_rows_it_cannot_fill(self):
        migrate.upgrade(self.engine, INITIAL)
        with self.engine.begin() as conn:
            conn.execute(text("INSERT INTO researchers (name, orcid, is_active) VALUES ('A', '1', 1)"))
        with self.assertRaisesRegex(RuntimeError, "researchers has rows"):
            migrate.upgrade(self.engine)

    def test_downgrade_to_initial(self):
        migrate.upgrade(self.engine)
        with self.engine.begin() as conn:
            command.downgrade(migrate.alembic_config(conn), INITIAL)
        self.assertNotIn("email", {c["name"] for c in inspect(self.engine).get_columns("researchers")})


if __name__ == "__main__":
    unittest.main()
