from logging.config import fileConfig

from alembic import context

from app.database import Base, DATABASE_URL, engine

# Import every model so its table is registered on Base.metadata.
import app.models.forms  # noqa: F401
import app.models.publication  # noqa: F401
import app.models.publication_resource  # noqa: F401
import app.models.researcher  # noqa: F401
import app.models.resource  # noqa: F401

# app.migrate and the tests may pass their own connection.
if context.config.config_file_name is not None and "connection" not in context.config.attributes:
    fileConfig(context.config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Write SQL to stdout instead of running it (alembic upgrade head --sql)."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def _run(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connection = context.config.attributes.get("connection")
    if connection is not None:
        _run(connection)
        return
    with engine.connect() as connection:
        _run(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
