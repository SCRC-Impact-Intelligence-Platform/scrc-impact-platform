"""Database schema checks, on top of the Alembic migrations in alembic/versions.

    alembic upgrade head             # apply migrations
    python -m app.migrate            # exit 1 if the database is behind

The API and CLIs only check the schema at startup; they never change it.
"""

import argparse
import logging
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)
ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"


def alembic_config(connection=None) -> Config:
    config = Config(str(ALEMBIC_INI))
    if connection is not None:
        config.attributes["connection"] = connection
    return config


def upgrade(engine: Engine, revision: str = "head") -> None:
    with engine.begin() as connection:
        command.upgrade(alembic_config(connection), revision)


def check_schema_current(engine: Engine | None = None) -> None:
    """Raise with instructions if the database is behind the latest migration.

    A database *ahead* of this code (revisions it doesn't know) only logs a warning:
    that's an old pod restarting after a migration, or a release rollback.
    Migrations must stay backward compatible with the previous release for this to hold.
    """
    if engine is None:
        from app.database import engine
    script = ScriptDirectory.from_config(alembic_config())
    expected = set(script.get_heads())
    with engine.connect() as connection:
        current = set(MigrationContext.configure(connection).get_current_heads())
    if current - {rev.revision for rev in script.walk_revisions()}:
        logger.warning("Database is at %s, newer than this code (%s).", sorted(current), sorted(expected))
        return
    if current != expected:
        raise RuntimeError(
            f"Database schema is at {sorted(current) or 'no Alembic version'}, expected {sorted(expected)}. "
            "Run `alembic upgrade head` before starting the app."
        )


if __name__ == "__main__":
    argparse.ArgumentParser(description="Check the database schema is up to date").parse_args()
    try:
        check_schema_current()
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1)
    print("Database schema is up to date.")
