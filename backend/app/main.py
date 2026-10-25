from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, engine
from app.models.researcher import Researcher
from app.api.researchers import router as researchers_router
from app.models.resource import Resource
from app.api.resources import router as resources_router
from app.models.publication import Publication
from app.api.publications import router as publications_router
from app.api.forms_poc import router as forms_poc_router
from app.models.forms_poc import FormBatch, FormQuestion, SyncedFormResponse
from app.models.publication_resource import publication_resources


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="SCRC Impact Intelligence Platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(researchers_router)
app.include_router(resources_router)
app.include_router(publications_router)
app.include_router(forms_poc_router)


@app.get("/")
def health_check():
    return {"status": "ok"}