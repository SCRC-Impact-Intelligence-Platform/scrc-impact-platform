# SCRC Backend

## PubMed publication discovery (CLI)

Run from the `backend/` directory with the Python virtual environment active:

```bash
cd backend
source .venv/bin/activate  # macOS/Linux; skip if already active
```

Discover publications for **all active researchers** (`is_active=True`):

```bash
# Default: last 3 calendar months
python -m app.cli

# Custom lookback: last 36 months (useful for local testing/backfill)
python -m app.cli --months 36

# Other examples
python -m app.cli --months 12
python -m app.cli --help
```

`--months` must be a positive integer. The lookback window begins on the
first day of the month, N months before the current month, and ends today.
For example, on 2026-11-01, `--months 36` searches 2023-11-01 through
2026-11-01.

The CLI searches PubMed by each active researcher's ORCID, filters by
**publication date**, paginates through search results, and retrieves metadata
using EFetch (including DOI and abstract when PubMed provides them).
Only PMIDs not already in the database are inserted; running the same search
again does not duplicate publications or reset their review status.

> PubMed records may not have a DOI or abstract, so either field can still be
> `null`. A publication-date window may also omit older papers newly indexed
> by PubMed. The CLI writes to the configured local database.

### Tests

```bash
python -m unittest discover -s tests -v
```

### View imported records

Start the API (`python -m uvicorn app.main:app --reload`) and inspect
`GET /publications` at <http://127.0.0.1:8000/docs>.
