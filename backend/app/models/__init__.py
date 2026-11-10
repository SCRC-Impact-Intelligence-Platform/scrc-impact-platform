"""Register all SQLAlchemy tables on the shared Base.metadata."""

from app.models.researcher import Researcher
from app.models.resource import Resource
from app.models.publication import Publication
from app.models.publication_resource import PublicationResource
from app.models.forms import FormBatch, FormQuestion, SyncedFormResponse

__all__ = [
    "Researcher",
    "Resource",
    "Publication",
    "PublicationResource",
    "FormBatch",
    "FormQuestion",
    "SyncedFormResponse",
]
