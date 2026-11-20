from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, Unicode
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Grant(Base):
    """A grant awarded to the center or one of its researchers."""

    __tablename__ = "grants"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(Unicode(500), nullable=False)
    funder: Mapped[str] = mapped_column(Unicode(255), nullable=False)
    # Total award in US dollars, when known.
    amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    award_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    researcher_id: Mapped[int | None] = mapped_column(ForeignKey("researchers.id"), nullable=True, index=True)
