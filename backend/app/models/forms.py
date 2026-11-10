from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Index, JSON, String, DateTime, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from app.enums import FormBatchState


def utcnow():
    return datetime.now(timezone.utc)


class FormBatch(Base):
    __tablename__ = "form_batches"
    # Filtered so SQL Server allows many batches without a form yet.
    __table_args__ = (
        Index(
            "uq_form_batches_google_form_id",
            "google_form_id",
            unique=True,
            mssql_where=text("google_form_id IS NOT NULL"),
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    researcher_id: Mapped[int | None] = mapped_column(ForeignKey("researchers.id"), nullable=True)
    invitation_to: Mapped[str | None] = mapped_column(String(320), nullable=True)
    invitation_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    google_form_id: Mapped[str | None] = mapped_column(String(255))
    responder_url: Mapped[str | None] = mapped_column(String(2048))
    state: Mapped[str] = mapped_column(String(20), default=FormBatchState.CREATING.value)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class FormQuestion(Base):
    __tablename__ = "form_questions"
    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("form_batches.id"), index=True)
    publication_id: Mapped[int] = mapped_column(ForeignKey("publications.id"))
    resource_ids: Mapped[list] = mapped_column(JSON)
    yes_question_id: Mapped[str] = mapped_column(String(255))
    resources_question_id: Mapped[str] = mapped_column(String(255))
    criticality_question_id: Mapped[str] = mapped_column(String(255))
    # Persist the researcher's original answers, even when no attribution exists.
    usage_answer: Mapped[str | None] = mapped_column(String(10), nullable=True)
    other_resource_text: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    reported_criticality: Mapped[str | None] = mapped_column(String(20), nullable=True)
    __table_args__ = (UniqueConstraint("batch_id", "publication_id"),)


class SyncedFormResponse(Base):
    __tablename__ = "synced_form_responses"
    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("form_batches.id"))
    google_response_id: Mapped[str] = mapped_column(String(255))
    processed_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    __table_args__ = (UniqueConstraint("batch_id", "google_response_id"),)
