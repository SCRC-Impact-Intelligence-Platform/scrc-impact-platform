## Database

The backend uses Microsoft SQL Server. Set the `DATABASE_URL` environment
variable (required; see `backend/.env.example`).

### Local stack (SQL Server + backend in Docker)

```bash
docker compose up --build        # UI: http://localhost:8000/ui
docker compose exec backend python -m app.cli   # run publication discovery
docker compose down -v           # stop and wipe the local database
```

`GET /health/db` returns 503 when the database is unreachable (use it as the
Kubernetes readiness probe).
