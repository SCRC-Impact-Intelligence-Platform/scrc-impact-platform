"""Translate submitted Google Form responses into publication outcomes."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.forms import FormQuestion, SyncedFormResponse
from app.enums import FormBatchState
from app.models.publication import Publication
from app.models.publication_resource import publication_resources


def _values(answers: dict, question_id: str) -> list[str]:
    return [a["value"] for a in answers.get(question_id, {}).get("textAnswers", {}).get("answers", [])]


def sync_batch(db: Session, batch, responses: list[dict]) -> dict:
    # A completed batch is immutable; it is never processed again.
    if batch.state == FormBatchState.COMPLETED:
        return {"processed": 0, "skipped": len(responses), "invalid": 0}
    questions = db.scalars(select(FormQuestion).where(FormQuestion.batch_id == batch.id)).all()
    result = {"processed": 0, "skipped": 0, "invalid": 0}
    # Exactly one valid submission per batch. If multiple distinct submissions
    # are present before syncing, stop and require administrator reconciliation.
    already = db.scalar(select(SyncedFormResponse).where(SyncedFormResponse.batch_id == batch.id))
    if already:
        batch.state = FormBatchState.COMPLETED.value
        db.commit()
        return {"processed": 0, "skipped": len(responses), "invalid": 0}
    if len(responses) > 1:
        raise ValueError("Multiple submissions for one batch; manual review required")
    for response in responses:
        response_id = response["responseId"]
        if db.scalar(select(SyncedFormResponse.id).where(SyncedFormResponse.batch_id == batch.id, SyncedFormResponse.google_response_id == response_id)):
            result["skipped"] += 1
            continue
        answers = response.get("answers", {})
        updates = []
        valid = True
        for question in questions:
            yes = _values(answers, question.yes_question_id)
            selected = _values(answers, question.resources_question_id)
            if len(yes) != 1 or yes[0] not in ("Yes", "No"):
                valid = False
                break
            permitted = set(question.resource_ids)
            resource_ids = []
            for value in selected:
                try:
                    rid = int(value.split(":", 1)[0])
                except ValueError:
                    valid = False
                    break
                resource_ids.append(rid)
            if not valid or len(resource_ids) != len(set(resource_ids)) or not set(resource_ids) <= permitted:
                valid = False
                break
            if (yes[0] == "Yes" and not resource_ids) or (yes[0] == "No" and resource_ids):
                valid = False
                break
            publication = db.get(Publication, question.publication_id)
            if publication.status not in ("PENDING", "SENT"):
                valid = False
                break
            updates.append((publication, yes[0], resource_ids))
        if not valid:
            result["invalid"] += 1
            continue
        # One database transaction per Google submission.
        for publication, answer, resource_ids in updates:
            publication.status = "CONFIRMED" if answer == "Yes" else "REJECTED"
            for resource_id in resource_ids:
                db.execute(publication_resources.insert().values(publication_id=publication.id, resource_id=resource_id))
        db.add(SyncedFormResponse(batch_id=batch.id, google_response_id=response_id))
        batch.state = FormBatchState.COMPLETED.value
        db.commit()
        result["processed"] += 1
    return result
