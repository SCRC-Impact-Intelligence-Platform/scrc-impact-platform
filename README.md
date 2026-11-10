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

### Schema changes (Alembic)

Tables are managed by Alembic migrations in `backend/alembic/versions/`. The
container runs `alembic upgrade head` on startup, applying any new migrations.

After changing a model, generate a migration (runs in the container, which has
the SQL Server driver), review the file, and commit it with the model change:

```bash
docker compose run --rm --user "$(id -u):$(id -g)" -v "$PWD/backend:/srv/backend" \
  backend alembic revision --autogenerate -m "describe the change"
```

Autogenerate can't detect renames (it sees a drop + add, losing data), so
check the generated file. `alembic upgrade head --sql` prints the SQL instead
of running it, for a DBA to apply by hand.
