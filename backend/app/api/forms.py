"""Local-only Forms management. Add administrator authorization before deployment."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.publication import Publication
from app.models.resource import Resource
from app.models.researcher import Researcher
from app.models.forms import FormBatch, FormQuestion, SyncedFormResponse
from app.schemas.forms import FormCreate, FormBatchResponse, FormBatchDetail, FormQuestionResponse
from app.enums import FormBatchState
from app.schemas.invitation import SendInvitationRequest
from app.services.smtp_mail import send_smtp_message, smtp_configured, generate_invitation
from app.services.google_forms import create_google_form
from app.services.form_sync_runner import sync_one_form, sync_all_forms

router = APIRouter(prefix="/forms", tags=["Forms (local development)"])


@router.get("", response_model=list[FormBatchResponse])
def list_forms(db: Session = Depends(get_db)):
    return db.scalars(select(FormBatch).order_by(FormBatch.id.desc())).all()


@router.get("/{batch_id}", response_model=FormBatchDetail)
def get_form(batch_id: int, db: Session = Depends(get_db)):
    batch = db.get(FormBatch, batch_id)
    if batch is None:
        raise HTTPException(404, "Form batch not found")
    questions = db.scalars(
        select(FormQuestion).where(FormQuestion.batch_id == batch_id).order_by(FormQuestion.id)
    ).all()
    return FormBatchDetail(
        id=batch.id, researcher_id=batch.researcher_id, invitation_to=batch.invitation_to, invitation_sent_at=batch.invitation_sent_at, google_form_id=batch.google_form_id,
        responder_url=batch.responder_url, state=batch.state,
        created_at=batch.created_at,
        questions=[FormQuestionResponse.model_validate(q) for q in questions],
    )


@router.post("", status_code=201)
def create_form(payload: FormCreate, db: Session = Depends(get_db)):
    researcher = db.get(Researcher, payload.researcher_id)
    if researcher is None or not researcher.is_active:
        raise HTTPException(422, "Active researcher not found")
    if len({x.publication_id for x in payload.items}) != len(payload.items):
        raise HTTPException(422, "Duplicate publication IDs")
    items = []
    for selected in payload.items:
        publication = db.get(Publication, selected.publication_id)
        if not publication or publication.status != "PENDING":
            raise HTTPException(422, f"Publication {selected.publication_id} must be PENDING")
        if publication.first_discovered_researcher_id != researcher.id:
            raise HTTPException(422, f"Publication {publication.id} was not first discovered for researcher {researcher.id}")
        if len(set(selected.resource_ids)) != len(selected.resource_ids):
            raise HTTPException(422, "Duplicate resource IDs")
        resources = db.scalars(select(Resource).where(Resource.id.in_(selected.resource_ids), Resource.is_active.is_(True))).all()
        if len(resources) != len(selected.resource_ids):
            raise HTTPException(422, "Missing or inactive resource")
        items.append({"publication_id": publication.id, "pmid": publication.pmid, "title": publication.title, "resources": [{"id": r.id, "name": r.name} for r in resources]})
    # Save local record first. If remote creation fails, leave CREATING for diagnosis.
    batch = FormBatch(state=FormBatchState.CREATING.value, researcher_id=researcher.id)
    db.add(batch)
    db.commit()
    db.refresh(batch)
    try:
        form_id, uri, question_pairs = create_google_form(items)
    except Exception as exc:
        batch.state = FormBatchState.FAILED.value
        db.commit()
        raise HTTPException(502, f"Google Forms creation failed: {type(exc).__name__}")
    batch.google_form_id, batch.responder_url, batch.state = form_id, uri, FormBatchState.READY.value
    for item, (qid_yes, qid_resources) in zip(items, question_pairs):
        db.add(FormQuestion(batch_id=batch.id, publication_id=item["publication_id"], resource_ids=[r["id"] for r in item["resources"]], yes_question_id=qid_yes, resources_question_id=qid_resources))
    db.commit()
    return {"batch_id": batch.id, "google_form_id": form_id, "responder_url": uri, "state": batch.state}


@router.post("/{batch_id}/mark-sent")
def mark_sent(batch_id: int, db: Session = Depends(get_db)):
    batch = db.get(FormBatch, batch_id)
    if not batch or batch.state != FormBatchState.READY.value:
        raise HTTPException(404, "Ready form not found")
    if db.scalar(select(SyncedFormResponse.id).where(SyncedFormResponse.batch_id == batch_id)) is not None:
        raise HTTPException(409, "Form already has a processed response")
    questions = db.scalars(select(FormQuestion).where(FormQuestion.batch_id == batch_id)).all()
    for question in questions:
        publication = db.get(Publication, question.publication_id)
        if publication.status != "PENDING":
            raise HTTPException(409, "Publication is no longer PENDING")
        publication.status = "SENT"
    batch.state = FormBatchState.SENT.value
    db.commit()
    return {"state": "SENT", "publications": len(questions)}


@router.post("/sync")
def sync_all(db: Session = Depends(get_db)):
    return sync_all_forms(db)


@router.post("/{batch_id}/sync")
def sync_form(batch_id: int, db: Session = Depends(get_db)):
    try:
        return sync_one_form(db, batch_id, allow_ready=True)
    except ValueError as exc:
        raise HTTPException(409, str(exc))
    except Exception:
        db.rollback()
        raise HTTPException(502, "Google Forms synchronization failed")


@router.get("/{batch_id}/invitation-draft")
def invitation_draft(batch_id: int, db: Session = Depends(get_db)):
    batch = db.get(FormBatch, batch_id)
    if batch is None or not batch.researcher_id or not batch.responder_url:
        raise HTTPException(404, "Form invitation not available")
    researcher = db.get(Researcher, batch.researcher_id)
    return generate_invitation(researcher.name, researcher.email, batch.responder_url)


@router.post("/{batch_id}/send-invitation")
def send_invitation(batch_id: int, payload: SendInvitationRequest, db: Session = Depends(get_db)):
    # Local development only: do not expose this endpoint without administrator auth.
    if not smtp_configured():
        raise HTTPException(503, "SMTP sending disabled; configure and authorize it first")
    batch = db.get(FormBatch, batch_id)
    if batch is None or batch.state != FormBatchState.READY.value or not batch.researcher_id:
        raise HTTPException(409, "Form must be READY and have a researcher")
    researcher = db.get(Researcher, batch.researcher_id)
    questions = db.scalars(select(FormQuestion).where(FormQuestion.batch_id == batch_id)).all()
    if not questions or not batch.responder_url or batch.responder_url not in payload.body:
        raise HTTPException(422, "Invitation must contain the generated Google Form URL")
    for question in questions:
        publication = db.get(Publication, question.publication_id)
        if not publication or publication.status != "PENDING":
            raise HTTPException(409, "Publication is no longer PENDING")
    try:
        send_smtp_message(to=researcher.email, subject=payload.subject, body=payload.body)
    except ValueError as exc:
        raise HTTPException(403, str(exc))
    except Exception:
        raise HTTPException(502, "SMTP server did not accept the message; check server logs")
    # An SMTP acceptance does not guarantee inbox delivery.
    from datetime import datetime, timezone
    batch.invitation_to = researcher.email
    batch.invitation_sent_at = datetime.now(timezone.utc)
    batch.state = FormBatchState.SENT.value
    for question in questions:
        db.get(Publication, question.publication_id).status = "SENT"
    db.commit()
    return {"state": "SENT", "recipient": researcher.email, "batch_id": batch.id}
