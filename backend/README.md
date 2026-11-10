# SCRC Backend

## Database schema

Migrations live in `alembic/versions/`; apply them with `alembic upgrade head`.
The API and CLIs check the schema at startup and refuse to run if the database
is behind (`python -m app.migrate` runs the same check). See the root README
for generating migrations.

## Running tests

```bash
DATABASE_URL=sqlite:// python -m unittest discover -s tests -v
```

`tests/test_migrations.py` runs the migrations against a real SQL Server in
Docker (`pip install -e ".[dev]"`); it is skipped when Docker isn't available.

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

The CLI searches PubMed by ORCID when available, otherwise by author name
restricted to UCI affiliation (name-based results still require review). It filters by
**publication date**, paginates through search results, and retrieves metadata
using EFetch (including DOI and abstract when PubMed provides them).
Only PMIDs not already in the database are inserted; running the same search
again does not duplicate publications or reset their review status.

> PubMed records may not have a DOI or abstract, so either field can still be
> `null`. A publication-date window may also omit older papers newly indexed
> by PubMed. The CLI writes to the configured local database.

### View imported records

Start the API (`python -m uvicorn app.main:app --reload`) and inspect
`GET /publications` at <http://127.0.0.1:8000/docs>.

## Google Forms OAuth Setup (Local Development)

The backend uses Google OAuth 2.0 to create Google Forms and retrieve responses.

### Prerequisites

1. Enable the Google Forms API in the shared Google Cloud project.
2. Ask a project maintainer to add your Google account under:
   Google Auth Platform → Audience → Test users.
3. Obtain the Desktop OAuth client configuration from a project
   maintainer through an approved secure channel.

### Setup

From the `backend/` directory:

```bash
mkdir -p .secrets
```

Save the OAuth client configuration as:

```text
backend/.secrets/google_oauth_client.json
```

Activate the Python virtual environment and install dependencies:

```bash
source .venv/bin/activate
python -m pip install -e .
```

Complete OAuth authorization:

```bash
python -m app.google_auth
```

Sign in with your Google account and approve the requested Google Forms permissions.

After successful authorization, the backend stores your credentials at:

```text
backend/.secrets/google_token.json
```

### Important Notes

- Never commit or share `google_token.json`.
- Do not commit `google_oauth_client.json`.
- Each developer should authorize their own Google account.
- Forms created by one account are not automatically accessible to other accounts.
- The OAuth app is currently in External / Testing mode.
- Google refresh tokens issued in this mode generally expire after 7 days for the Forms scopes.
- Run `python -m app.google_auth` again if reauthorization is required.
- Production authentication and credential management will be configured separately.

## Three-question Verification and Criticality

Generated Google Forms ask each selected publication about SCRC resource use
(`Yes / No / Unsure`), equipment (including free-text `Other`), and overall
criticality (`Critical / Significant / Minor`). Confirmed equipment selections
are stored in `publication_resources` with the same criticality for all selected
machines. `Unsure` and unresolved `Other` answers are tracked separately.

See [FORM_CRITICALITY.md](FORM_CRITICALITY.md) for the complete response-to-status
mapping, sync validation rules, and local database reset implications.

## Email Invitations

For SMTP setup and local email testing, see
[EMAIL_WORKFLOW.md](EMAIL_WORKFLOW.md#smtp-configuration-local-development).