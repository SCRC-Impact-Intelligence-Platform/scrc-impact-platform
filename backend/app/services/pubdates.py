"""Parse PubMed's free-text publication dates into stored year/month/day parts.

``Publication.publication_date`` keeps PubMed's text ("2026 Oct 12", "2026 Oct",
"2026 Jan-Feb", "2025 Dec-2026 Jan", "2026 Spring", "2026"). The parsed parts are
stored alongside it so reports can filter and sort in SQL. New papers use PubMed's
separate Year/Month/Day fields; the text parser covers MedlineDate and older rows. A range is dated by
its start, so each publication falls in exactly one quarter.
"""

from calendar import monthrange
import re

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


def _resolve(year: int, month_token: str | None, day: str | None) -> tuple[int, int | None, int | None]:
    """Validate a month token and day against the calendar."""
    if month_token is None:
        return year, None, None
    month = int(month_token) if month_token.isdigit() else _MONTHS.get(month_token[:3].lower())
    if not month or not 1 <= month <= 12:
        return year, None, None
    day_num = int(day) if day and day.isdigit() else None
    return year, month, day_num if day_num and 1 <= day_num <= monthrange(year or 2000, month)[1] else None


def parse_date(value: str | None) -> tuple[int, int | None, int | None] | None:
    """(year, month, day) from a PubMed date; month/day are None when absent."""
    if not value:
        return None
    match = _DATE.match(value)
    if match is None:
        return None
    return _resolve(int(match.group(1)), match.group(2) or match.group(3) or match.group(4), match.group(5))


def date_parts(value: str | None) -> dict:
    """Column values for Publication.publication_year/month/day."""
    year, month, day = parse_date(value) or (None, None, None)
    return {"publication_year": year, "publication_month": month, "publication_day": day}


def structured_date_parts(year: str | None, month: str | None, day: str | None) -> dict | None:
    """Column values from PubMed's separate Year/Month/Day fields; None without a year."""
    if not year or not year.strip().isdigit():
        return None
    parts = _resolve(int(year), month.strip() if month else None, day.strip() if day else None)
    return dict(zip(("publication_year", "publication_month", "publication_day"), parts))


def stored_date_parts(paper: dict) -> dict:
    """Date columns for a fetched paper: its structured fields, else parsed from the text."""
    if "publication_year" in paper:
        return {k: paper[k] for k in ("publication_year", "publication_month", "publication_day")}
    return date_parts(paper.get("publication_date"))
