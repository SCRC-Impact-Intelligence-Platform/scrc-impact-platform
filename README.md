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
