from sqlalchemy import Boolean, Index, String, Unicode, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Researcher(Base):
    __tablename__ = "researchers"
    # Filtered so SQL Server allows many researchers without an ORCID.
    __table_args__ = (
        Index("uq_researchers_orcid", "orcid", unique=True, mssql_where=text("orcid IS NOT NULL")),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        Unicode(255),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
    )

    orcid: Mapped[str | None] = mapped_column(
        String(19),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )