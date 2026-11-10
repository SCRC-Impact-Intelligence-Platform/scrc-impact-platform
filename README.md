# SCRC Impact Intelligence Platform

A UCI Stem Cell Research Center capstone platform for discovering research publications, verifying SCRC resource usage through Google Forms, and reporting confirmed publication–resource attributions.

## Documentation

- [Backend setup, PubMed discovery, and Google OAuth](backend/README.md)
- [Three-question verification, Criticality, Other, and Unsure](backend/FORM_CRITICALITY.md)
- [SMTP email invitations and local testing](backend/EMAIL_WORKFLOW.md)
- [Frontend development](frontend/README.md)

## Local development

Use two terminals after completing the backend and frontend setup instructions:

```bash
# From backend/ with the Python environment activated
python -m uvicorn app.main:app --reload

# From frontend/ in a separate terminal
npm run dev
```

Open the frontend at <http://127.0.0.1:5173> and the API docs at <http://127.0.0.1:8000/docs>.

## Database

The backend uses Microsoft SQL Server. Set the `DATABASE_URL` environment
variable (required; see `backend/.env.example`).

### Local stack (SQL Server + backend in Docker)

```bash
docker compose up --build        # UI: http://localhost:8080
docker compose exec backend python -m app.cli   # run publication discovery
docker compose down -v           # stop and wipe the local database
```

`GET /health/db` returns 503 when the database is unreachable (use it as the
Kubernetes readiness probe).

### Schema (development)

There are no migrations. The backend creates any missing tables from the
SQLAlchemy models when it starts; it never changes or deletes existing tables.
After changing a model, reset the local database so the tables are recreated:

```bash
docker compose down -v && docker compose up --build
```
