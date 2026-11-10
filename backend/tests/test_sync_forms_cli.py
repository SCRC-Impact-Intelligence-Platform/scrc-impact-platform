"""Regression tests for standalone Google Forms sync CLI startup."""

import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine

from app.database import Base
import app.models  # noqa: F401 - exercise central model registration
from app import sync_forms_cli


class SyncFormsCliTests(unittest.TestCase):
    def test_all_foreign_key_tables_are_registered(self):
        self.assertEqual(
            set(Base.metadata.tables),
            {
                "researchers", "resources", "publications",
                "publication_resources", "form_batches", "form_questions",
                "synced_form_responses",
            },
        )
        engine = create_engine("sqlite:///:memory:")
        try:
            Base.metadata.create_all(engine)
        finally:
            engine.dispose()

    def test_help_does_not_start_sync(self):
        backend = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [sys.executable, "-m", "app.sync_forms_cli", "--help"],
            cwd=backend, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("usage:", result.stdout)
        self.assertIn("Synchronize responses", result.stdout)
        self.assertNotIn("'batches':", result.stdout)

    def test_cli_calls_shared_runner_once(self):
        with patch.object(sync_forms_cli, "SessionLocal") as session, patch.object(
            sync_forms_cli, "sync_all_forms",
            return_value={"processed": 1, "failed": []},
        ) as runner, patch("builtins.print"):
            sync_forms_cli.main()
        runner.assert_called_once_with(session.return_value.__enter__.return_value)

    def test_cli_exits_nonzero_on_batch_failure(self):
        with patch.object(sync_forms_cli, "SessionLocal"), patch.object(
            sync_forms_cli, "sync_all_forms",
            return_value={"processed": 0, "failed": [{"batch_id": 1}]},
        ), patch("builtins.print"):
            with self.assertRaises(SystemExit) as exc:
                sync_forms_cli.main()
        self.assertEqual(exc.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
