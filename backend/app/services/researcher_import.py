"""Import researcher CSV records using email as the sole matching key."""

import csv
import io
from dataclasses import dataclass

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.researcher import Researcher
from app.schemas.researcher import ResearcherCreate

MAX_ROWS = 1000
EMPTY_ORCID = {"", "n/a", "na", "none", "null"}


@dataclass
class ImportResult:
    created: int = 0
    skipped: int = 0


def import_researchers(db: Session, content: str) -> ImportResult:
    """Match existing records by case-insensitive email, never by ORCID."""
    reader = csv.DictReader(io.StringIO(content.lstrip("\ufeff"), newline=""))
    if not reader.fieldnames:
        raise ValueError("CSV needs a header: name,email,orcid")
    headers = [value.strip().lower() for value in reader.fieldnames]
    if len(headers) != len(set(headers)) or set(headers) != {"name", "email", "orcid"}:
        raise ValueError("CSV columns must be exactly: name,email,orcid")
    rows = list(reader)
    if not rows:
        raise ValueError("CSV contains no researchers")
    if len(rows) > MAX_ROWS:
        raise ValueError(f"CSV exceeds {MAX_ROWS} researchers")

    records = []
    for line, row in enumerate(rows, 2):
        if None in row or any(value is None for value in row.values()):
            raise ValueError(f"Row {line}: invalid number of columns")
        data = {key.strip().lower(): value.strip() for key, value in row.items()}
        email = data["email"].lower()
        orcid = data["orcid"]
        if orcid.lower() in EMPTY_ORCID:
            orcid = None
        try:
            record = ResearcherCreate(name=data["name"], email=email, orcid=orcid)
        except ValidationError as exc:
            raise ValueError(f"Row {line}: invalid name, email or ORCID") from exc
        records.append(record)

    existing = db.scalars(select(Researcher)).all()
    by_email = {}
    for researcher in existing:
        by_email[researcher.email.casefold()] = researcher

    result = ImportResult()
    for record in records:
        email = str(record.email).casefold()
        # Email already exists: skip the entire row without modifying the researcher.
        # This also skips repeated emails within the same CSV upload.
        if email in by_email:
            result.skipped += 1
            continue

        researcher = Researcher(name=record.name, email=email, orcid=record.orcid)
        db.add(researcher)
        by_email[email] = researcher
        result.created += 1

    db.commit()
    return result
