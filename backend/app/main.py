from pathlib import Path

from dotenv import load_dotenv

# Local settings; explicit environment variables take precedence.
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from fastapi import FastAPI, HTTPException
from sqlalchemy import text

from app.database import engine
from app.models.researcher import Researcher
from app.api.researchers import router as researchers_router
from app.models.resource import Resource
from app.api.resources import router as resources_router
from app.models.publication import Publication
from app.api.publications import router as publications_router
from app.api.forms import router as forms_router
from app.api.attributions import router as attributions_router
from app.models.forms import FormBatch, FormQuestion, SyncedFormResponse
from app.models.publication_resource import PublicationResource  # noqa: F401


app = FastAPI(
    title="SCRC Impact Intelligence Platform",
    version="0.1.0",
)

app.include_router(researchers_router)
app.include_router(resources_router)
app.include_router(publications_router)
app.include_router(forms_router)
app.include_router(attributions_router)


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
