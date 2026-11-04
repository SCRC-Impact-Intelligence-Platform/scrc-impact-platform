# SCRC Google Forms → Email Invitation (local-only MVP)

## Flow

1. Researchers have emails and optionally ORCIDs. Discovery sets `first_discovered_researcher_id` for **new** publications. This is the first discoverer, not proof of authorship.
2. On `/forms`, choose a researcher, then pending publications first discovered for that researcher; choose candidate resources for each.
3. `POST /forms` creates a Google Form and a `READY` FormBatch containing the designated `researcher_id`.
4. `GET /forms/{batch_id}/invitation-draft` builds the default recipient, subject and body with the genuine Form URL. The browser allows editing the subject/body.
5. `POST /forms/{batch_id}/send-invitation` sends plain text with SMTP STARTTLS **only if** the deployment explicitly enables sending and the researcher email is allowlisted. SMTP accepted does **not** prove delivery. A successful SMTP acceptance marks batch/Publications `SENT`; scheduled Sync continues until `COMPLETED`.

## Schema / local DB reset required

This change adds `publications.first_discovered_researcher_id` and `form_batches.researcher_id`, `invitation_to`, `invitation_sent_at`. SQLAlchemy `create_all()` **does not alter existing tables**. For a disposable local SQLite DB, stop the FastAPI process and CLI, then rename/delete `backend/local.db` and restart FastAPI. You will lose all test researchers/resources/publications/forms/attributions; rebuild test data and rerun discovery to populate new source IDs. For persisted data, write a reviewed Alembic migration instead; do not simply delete production data.

## SMTP configuration

Joseph's C# snippet indicates `mta.service.uci.edu:587`, STARTTLS, sender `DoNotReply@uci.edu`, and no default OS credentials. It **does not** prove anonymous sending is permitted or that your account/server is authorized. Obtain explicit confirmation of supported network, sender identity, authentication, and whether UCI VPN/internal server access is required.

By default sending is disabled. Copy `backend/.env.example` to `backend/.env`
(which is Git-ignored), then edit its values. Install dependencies once per venv:

```bash
python -m pip install -e ".[dev]"
```

The app automatically loads `backend/.env` at startup. Explicit shell environment
variables take precedence. Start it normally:

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1
```

Use `SMTP_ENABLE_SEND=false` until IT authorizes the relay/sender, then enable
only when testing to a controlled recipient in `SMTP_ALLOWED_RECIPIENTS`. The
optional SMTP username/password are needed only if IT requires authentication.

Never put SMTP credentials in Git, browser code, or Docker images. `defaultCredentials=false` means not to use default OS credentials; it does **not** imply no credentials. On port 587 use `starttls()`, not `SMTP_SSL()` (implicit TLS).

**Security boundary:** The existing FastAPI admin routes have no authentication. This workflow is for localhost development only. Do not expose these endpoints on a network or enable broad recipient sending until administrator authentication, authorization, CSRF protection (if cookie sessions), delivery auditing, rate limiting, recipient restrictions, retry/idempotency policy, and deployment-approved credential storage are implemented. Sending may be accepted by SMTP yet DB commit fail, so retry requires reconciliation to prevent duplicates.

Existing `POST /forms/{id}/mark-sent` is a manual marker; do not use it for SMTP sending. Do not place secrets in uploaded ZIP archives.
