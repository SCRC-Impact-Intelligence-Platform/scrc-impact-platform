from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, Integer, JSON, String, Unicode
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Publication(Base):
    __tablename__ = "publications"
    __table_args__ = (
        Index("ix_publications_publication_year_month", "publication_year", "publication_month"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    pmid: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        Unicode,  # NVARCHAR(max) on SQL Server
        nullable=False,
    )

    authors: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
    )

    journal: Mapped[str | None] = mapped_column(
        Unicode(500),
        nullable=True,
    )

    publication_date: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # Parsed from publication_date (app.services.pubdates) so reports can filter
    # and sort in SQL. Month/day are None when PubMed gives only a year or season.
    publication_year: Mapped[int | None] = mapped_column(Integer, nullable=True)

    publication_month: Mapped[int | None] = mapped_column(Integer, nullable=True)

    publication_day: Mapped[int | None] = mapped_column(Integer, nullable=True)

    doi: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    abstract: Mapped[str | None] = mapped_column(
        Unicode,  # NVARCHAR(max) on SQL Server
        nullable=True,
    )

    first_discovered_researcher_id: Mapped[int | None] = mapped_column(
        ForeignKey("researchers.id"), nullable=True, index=True
    )

    first_discovered_by_orcid: Mapped[str | None] = mapped_column(
        String(19),
        nullable=True,
    )

    discovered_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="PENDING",
        nullable=False,
    )
