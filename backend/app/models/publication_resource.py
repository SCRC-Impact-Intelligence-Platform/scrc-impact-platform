from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PublicationResource(Base):
    """A confirmed publication–resource attribution and its criticality."""

    __tablename__ = "publication_resources"

    publication_id: Mapped[int] = mapped_column(
        ForeignKey("publications.id"), primary_key=True
    )
    resource_id: Mapped[int] = mapped_column(
        ForeignKey("resources.id"), primary_key=True
    )
    criticality: Mapped[str] = mapped_column(String(20), nullable=False)
