# Google Forms verification proof of concept

**Local-only experimental integration. Do not expose these endpoints to the internet.** Existing API has no authentication. Use synthetic research data and a test Google account until UCI approval.

## Branch

`git switch -c feat/google-forms-verification-poc`

## Google setup

1. Create a Google Cloud project, enable **Google Forms API**, configure the OAuth consent screen / test user, create an **OAuth Client ID** of type **Desktop app**.
2. Download its JSON to `backend/.secrets/google_oauth_client.json`. Keep it out of Git.
3. `cd backend && source .venv/bin/activate && python -m pip install -e .`
4. `python -m app.google_auth`; sign in to a Google account that owns the test forms. This stores a refreshable token in `backend/.secrets/google_token.json`.
5. `python -m uvicorn app.main:app --reload --host 127.0.0.1`

## Test

Use your existing Swagger endpoints to ensure at least two PENDING publications and active resources exist. In Swagger:

`POST /poc/forms`

```json
{"items":[{"publication_id":1,"resource_ids":[1,2]},{"publication_id":2,"resource_ids":[2]}]}
```

Confirm Google Form sharing settings permit your intended test responder. Copy the `responder_url` and open it, or send it to yourself. The PoC deliberately does **not** send email automatically. After actually sending it, optionally call `POST /poc/forms/{batch_id}/mark-sent`.

Fill **every** publication's Yes/No question, and choose at least one resource if Yes. Submit. Call `POST /poc/forms/{batch_id}/sync`; then `GET /publications` to see status changes. Run sync again and expect `processed: 0`.

### Constraints / known limitations

- Form response validation happens **during sync**, not inside Google Forms; submitting Yes with no resources is considered invalid and not applied.
- A whole multi-publication form submission is applied atomically or skipped if any item is malformed or already processed; no partial application.
- Form question option IDs use frozen resource IDs in labels; the server maps using Google question IDs stored at form creation.
- No email, user identity verification, publication status transitions beyond this path, retry orchestration, scheduling, deletion, auditing, or role-based access control. No production use.
- Avoid issuing multiple forms for the same pending publication; this PoC doesn't enforce exclusive invitations. A second response for a now-finalized publication will be treated as invalid.
- If Google Form creation succeeds but saving the local mapping fails, a remote orphan form may need manual cleanup.
- Repeated sync of an invalid response will keep reporting invalid; it is not silently marked processed.
- Response emails/identities are not authenticated; link possession alone is not scientific attribution evidence.
- Ask UCI IT for approval for Google data storage, API access, and the eventual MS SQL migration before using actual researcher responses.
