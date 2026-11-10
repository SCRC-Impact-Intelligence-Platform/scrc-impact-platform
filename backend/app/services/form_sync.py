"""Validate a Google submission before atomically persisting all publication outcomes."""
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enums import FormBatchState, ResourceCriticality
from app.models.forms import FormQuestion, SyncedFormResponse
from app.models.publication import Publication
from app.models.publication_resource import PublicationResource


logger = logging.getLogger(__name__)

CRITICALITIES = {value.value for value in ResourceCriticality}
OTHER_OPTION = "Other (not listed)"


def _values(answers: dict, question_id: str) -> list[str]:
    return [a["value"] for a in answers.get(question_id, {}).get("textAnswers", {}).get("answers", [])]


def _parse_equipment(values: list[str], permitted: set[int]) -> tuple[list[int], str | None]:
    """Parse selected machine IDs and the fixed Other option (or legacy free text)."""
    ids = []
    others = []
    for value in values:
        prefix, sep, _ = value.partition(":")
        if sep and prefix.isascii() and prefix.isdecimal():
            resource_id = int(prefix)
            if resource_id not in permitted:
                raise ValueError("Unapproved resource ID")
            ids.append(resource_id)
        else:
            # Current forms use a fixed "Other (not listed)" checkbox.
            # Keep support for responses from earlier free-text forms.
            others.append(value)
    if len(ids) != len(set(ids)) or len(others) > 1:
        raise ValueError("Duplicate or ambiguous equipment selections")
    other = others[0].strip() if others else None
    if other is not None and (not other or len(other) > 2000):
        raise ValueError("Invalid Other resource description")
    return ids, other


def sync_batch(db: Session, batch, responses: list[dict]) -> dict:
    if batch.state == FormBatchState.COMPLETED:
        return {"processed": 0, "skipped": len(responses), "invalid": 0}
    questions = db.scalars(select(FormQuestion).where(FormQuestion.batch_id == batch.id)).all()
    result = {"processed": 0, "skipped": 0, "invalid": 0}
    already = db.scalar(select(SyncedFormResponse.id).where(SyncedFormResponse.batch_id == batch.id))
    if already:
        batch.state = FormBatchState.COMPLETED.value
        db.commit()
        return {"processed": 0, "skipped": len(responses), "invalid": 0}
    if len(responses) > 1:
        raise ValueError("Multiple submissions for one batch; manual review required")
    for response in responses:
        response_id = response["responseId"]
        if db.scalar(select(SyncedFormResponse.id).where(
            SyncedFormResponse.batch_id == batch.id,
            SyncedFormResponse.google_response_id == response_id,
        )):
            result["skipped"] += 1
            continue
        answers = response.get("answers", {})
        updates = []
        try:
            for question in questions:
                yes = _values(answers, question.yes_question_id)
                selected = _values(answers, question.resources_question_id)
                criticality_answers = _values(answers, question.criticality_question_id)
                if len(yes) != 1 or yes[0] not in ("Yes", "No", "Unsure"):
                    raise ValueError("Invalid usage answer")
                ids, other = _parse_equipment(selected, set(question.resource_ids))
                if len(criticality_answers) > 1:
                    raise ValueError("Multiple criticality answers")
                raw_criticality = criticality_answers[0].upper() if criticality_answers else None
                if raw_criticality is not None and raw_criticality not in CRITICALITIES:
                    raise ValueError("Invalid criticality")
                if yes[0] == "Yes":
                    if not ids and not other:
                        raise ValueError("Yes requires a resource or Other")
                    if not raw_criticality:
                        raise ValueError("Yes requires a criticality")
                    # Other-only requires manual review to resolve the resource.
                    status = "CONFIRMED" if ids else "NEEDS_REVIEW"
                else:
                    if selected or criticality_answers:
                        raise ValueError("No/Unsure cannot specify equipment or criticality")
                    status = "REJECTED" if yes[0] == "No" else "UNSURE"
                publication = db.get(Publication, question.publication_id)
                if publication is None or publication.status not in ("PENDING", "SENT"):
                    raise ValueError("Publication no longer eligible")
                updates.append((question, publication, yes[0], ids, other, raw_criticality, status))
        except (ValueError, KeyError, TypeError) as exc:
            logger.warning("Invalid form response for batch %s: %s", batch.id, exc)
            result["invalid"] += 1
            continue
        # No changes until every publication in the response is valid.
        for question, publication, answer, ids, other, criticality, status in updates:
            question.usage_answer = answer
            question.other_resource_text = other
            question.reported_criticality = criticality
            publication.status = status
            for rid in ids:
                db.add(PublicationResource(
                    publication_id=publication.id,
                    resource_id=rid,
                    criticality=criticality,
                ))
        db.add(SyncedFormResponse(batch_id=batch.id, google_response_id=response_id))
        batch.state = FormBatchState.COMPLETED.value
        db.commit()
        result["processed"] += 1
    return result
