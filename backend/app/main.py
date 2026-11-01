from pathlib import Path

from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from fastapi.staticfiles import StaticFiles

from app.database import engine
from app.models.researcher import Researcher
from app.api.researchers import router as researchers_router
from app.models.resource import Resource
from app.api.resources import router as resources_router
from app.models.publication import Publication
from app.api.publications import router as publications_router


app = FastAPI(
    title="SCRC Impact Intelligence Platform",
    version="0.1.0",
)

app.include_router(researchers_router)
app.include_router(resources_router)
app.include_router(publications_router)
app.mount(
    "/ui",
    StaticFiles(
        directory=Path(__file__).resolve().parents[2] / "frontend",
        html=True,
    ),
    name="ui",
)


@app.get("/")
def health_check():
    return {"status": "ok"}


@app.get("/health/db")
def database_health_check():
    """Readiness check: confirms the database is reachable."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(status_code=503, detail="database unavailable")
    return {"status": "ok"}
