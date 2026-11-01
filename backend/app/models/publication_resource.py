from sqlalchemy import Table, Column, ForeignKey
from app.database import Base

# Confirmed attributions only; no YES/NO stored here.
publication_resources = Table(
    "publication_resources",
    Base.metadata,
    Column("publication_id", ForeignKey("publications.id"), primary_key=True),
    Column("resource_id", ForeignKey("resources.id"), primary_key=True),
)
