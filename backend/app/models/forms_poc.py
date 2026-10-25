from datetime import datetime, timezone

from sqlalchemy import ForeignKey, JSON, String, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class FormBatch(Base):
    __tablename__ = "form_batches"
    id: Mapped[int] = mapped_column(primary_key=True)
    google_form_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    responder_url: Mapped[str | None] = mapped_column(String(2048))
    state: Mapped[str] = mapped_column(String(20), default="CREATING")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class FormQuestion(Base):
    __tablename__ = "form_questions"
    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("form_batches.id"), index=True)
    publication_id: Mapped[int] = mapped_column(ForeignKey("publications.id"))
    resource_ids: Mapped[list] = mapped_column(JSON)
    yes_question_id: Mapped[str] = mapped_column(String(255))
    resources_question_id: Mapped[str] = mapped_column(String(255))
    __table_args__ = (UniqueConstraint("batch_id", "publication_id"),)


class SyncedFormResponse(Base):
    __tablename__ = "synced_form_responses"
    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("form_batches.id"))
    google_response_id: Mapped[str] = mapped_column(String(255))
    processed_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    __table_args__ = (UniqueConstraint("batch_id", "google_response_id"),)
