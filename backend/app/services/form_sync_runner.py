"""Shared runner for HTTP-triggered and scheduled Google Forms response sync."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enums import FormBatchState
from app.models.forms import FormBatch, SyncedFormResponse
from app.services.form_sync import sync_batch
from app.services.google_forms import get_responses


def sync_one_form(db: Session, batch_id: int, *, allow_ready: bool = False) -> dict:
    batch = db.get(FormBatch, batch_id)
    if batch is None:
        raise ValueError("Form batch not found")
    if batch.state == FormBatchState.COMPLETED:
        return {"processed": 0, "skipped": 1, "invalid": 0}
    permitted = {FormBatchState.SENT}
    if allow_ready:
        permitted.add(FormBatchState.READY)
    if batch.state not in permitted or not batch.google_form_id:
        raise ValueError("Form batch is not eligible for synchronization")
    # Reconcile batches already synced by the previous PoC version.
    if db.scalar(select(SyncedFormResponse.id).where(SyncedFormResponse.batch_id == batch_id)) is not None:
        batch.state = FormBatchState.COMPLETED.value
        db.commit()
        return {"processed": 0, "skipped": 1, "invalid": 0}
    return sync_batch(db, batch, get_responses(batch.google_form_id))


def sync_all_forms(db: Session) -> dict:
    ids = db.scalars(select(FormBatch.id).where(FormBatch.state == FormBatchState.SENT).order_by(FormBatch.id)).all()
    summary = {"batches": len(ids), "processed": 0, "skipped": 0, "invalid": 0, "failed": []}
    for batch_id in ids:
        try:
            result = sync_one_form(db, batch_id)
            for key in ("processed", "skipped", "invalid"):
                summary[key] += result[key]
        except Exception as exc:
            db.rollback()
            summary["failed"].append({"batch_id": batch_id, "error": type(exc).__name__})
    return summary
