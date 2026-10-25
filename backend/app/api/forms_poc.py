"""Developer-only prototype; no authorization on these endpoints. NEVER expose publicly."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.publication import Publication
from app.models.resource import Resource
from app.models.forms_poc import FormBatch, FormQuestion
from app.schemas.forms_poc import FormCreate
from app.services.google_forms import create_google_form, get_responses
from app.services.form_sync import sync_batch

router = APIRouter(prefix="/poc/forms", tags=["Google Forms PoC (local only)"])


@router.post("", status_code=201)
def create_form(payload: FormCreate, db: Session = Depends(get_db)):
    if len({x.publication_id for x in payload.items}) != len(payload.items):
        raise HTTPException(422, "Duplicate publication IDs")
    items = []
    for selected in payload.items:
        publication = db.get(Publication, selected.publication_id)
        if not publication or publication.status != "PENDING":
            raise HTTPException(422, f"Publication {selected.publication_id} must be PENDING")
        if len(set(selected.resource_ids)) != len(selected.resource_ids):
            raise HTTPException(422, "Duplicate resource IDs")
        resources = db.scalars(select(Resource).where(Resource.id.in_(selected.resource_ids), Resource.is_active.is_(True))).all()
        if len(resources) != len(selected.resource_ids):
            raise HTTPException(422, "Missing or inactive resource")
        items.append({"publication_id": publication.id, "pmid": publication.pmid, "title": publication.title, "resources": [{"id": r.id, "name": r.name} for r in resources]})
    # Save local record first. If remote creation fails, leave CREATING for diagnosis.
    batch = FormBatch(state="CREATING")
    db.add(batch)
    db.commit()
    db.refresh(batch)
    try:
        form_id, uri, question_pairs = create_google_form(items)
    except Exception as exc:
        batch.state = "FAILED"
        db.commit()
        raise HTTPException(502, f"Google Forms creation failed: {type(exc).__name__}")
    batch.google_form_id, batch.responder_url, batch.state = form_id, uri, "READY"
    for item, (qid_yes, qid_resources) in zip(items, question_pairs):
        db.add(FormQuestion(batch_id=batch.id, publication_id=item["publication_id"], resource_ids=[r["id"] for r in item["resources"]], yes_question_id=qid_yes, resources_question_id=qid_resources))
    db.commit()
    return {"batch_id": batch.id, "google_form_id": form_id, "responder_url": uri, "state": batch.state}


@router.post("/{batch_id}/mark-sent")
def mark_sent(batch_id: int, db: Session = Depends(get_db)):
    batch = db.get(FormBatch, batch_id)
    if not batch or batch.state != "READY":
        raise HTTPException(404, "Ready form not found")
    questions = db.scalars(select(FormQuestion).where(FormQuestion.batch_id == batch_id)).all()
    for question in questions:
        publication = db.get(Publication, question.publication_id)
        if publication.status != "PENDING":
            raise HTTPException(409, "Publication is no longer PENDING")
        publication.status = "SENT"
    batch.state = "SENT"
    db.commit()
    return {"state": "SENT", "publications": len(questions)}


@router.post("/{batch_id}/sync")
def sync_form(batch_id: int, db: Session = Depends(get_db)):
    batch = db.get(FormBatch, batch_id)
    if not batch or batch.state not in ("READY", "SENT") or not batch.google_form_id:
        raise HTTPException(404, "Form batch not found")
    try:
        responses = get_responses(batch.google_form_id)
    except Exception as exc:
        raise HTTPException(502, f"Google Forms read failed: {type(exc).__name__}")
    return sync_batch(db, batch, responses)
