"""Parsed publication year/month/day, so reports filter and sort in SQL.

Revision ID: c3e5a7b9d1f2
Revises: a1c0d2e3f4a5
"""
from calendar import monthrange
import re

from alembic import op
import sqlalchemy as sa

revision = "c3e5a7b9d1f2"
down_revision = "a1c0d2e3f4a5"
branch_labels = None
depends_on = None

_BATCH = 500
_INDEX = "ix_publications_publication_year_month"


# Frozen copy of the parser at the time of this migration, so that replaying it
# later gives the same result even if app.services.pubdates changes or moves.
_MONTHS = {
    name: i
    for i, name in enumerate(
        ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], start=1
    )
}
_DATE = re.compile(
    r"^\s*(\d{4})"
    # Month: a name, "2026 03", or "2026-03-05". Not "2026 3rd Quarter" or the range "2011-12".
    r"(?:(?:[\s-]+([A-Za-z]{3})|\s+(\d{1,2})(?!\w)|-(\d{1,2})(?=-\d))(?:[\s-]+(\d{1,2})(?!\d))?)?"
)


def date_parts(value):
    match = _DATE.match(value or "")
    year, month, day = None, None, None
    if match is not None:
        year, raw_day = int(match.group(1)), match.group(5)
        token = match.group(2) or match.group(3) or match.group(4)
        if token is not None:
            number = int(token) if token.isdigit() else _MONTHS.get(token.lower())
            if number and 1 <= number <= 12:
                month = number
                if raw_day and 1 <= int(raw_day) <= monthrange(year or 2000, month)[1]:
                    day = int(raw_day)
    return {"publication_year": year, "publication_month": month, "publication_day": day}


def upgrade() -> None:
    for name in ("publication_year", "publication_month", "publication_day"):
        op.add_column("publications", sa.Column(name, sa.Integer(), nullable=True))
    op.create_index(_INDEX, "publications", ["publication_year", "publication_month"], unique=False)

    # Fill the new columns from the existing PubMed date text.
    publications = sa.table(
        "publications",
        sa.column("id", sa.Integer),
        sa.column("publication_date", sa.String),
        sa.column("publication_year", sa.Integer),
        sa.column("publication_month", sa.Integer),
        sa.column("publication_day", sa.Integer),
    )
    conn = op.get_bind()
    rows = conn.execute(
        sa.select(publications.c.id, publications.c.publication_date)
        .where(publications.c.publication_date.is_not(None))
    ).all()
    update = (
        publications.update()
        .where(publications.c.id == sa.bindparam("pid"))
        .values(
            publication_year=sa.bindparam("publication_year"),
            publication_month=sa.bindparam("publication_month"),
            publication_day=sa.bindparam("publication_day"),
        )
    )
    params = [{"pid": pid, **date_parts(text)} for pid, text in rows]
    for start in range(0, len(params), _BATCH):
        conn.execute(update, params[start:start + _BATCH])


def downgrade() -> None:
    op.drop_index(_INDEX, table_name="publications")
    for name in ("publication_day", "publication_month", "publication_year"):
        op.drop_column("publications", name)
