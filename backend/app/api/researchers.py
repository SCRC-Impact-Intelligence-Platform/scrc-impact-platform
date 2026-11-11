from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.researcher import Researcher
from app.services.researcher_import import import_researchers
from app.schemas.researcher import (
    ResearcherCreate,
    ResearcherUpdate,
    ResearcherResponse,
    ResearcherImportResponse,
)

router = APIRouter(
    prefix="/researchers",
    tags=["Researchers"],
)


@router.post("/import", response_model=ResearcherImportResponse)
async def import_researcher_csv(request: Request, db: Session = Depends(get_db)):
    # Raw text/csv avoids adding multipart dependencies to this backend.
    if request.headers.get("content-type", "").split(";")[0].strip().lower() != "text/csv":
        raise HTTPException(415, "Send a CSV file with Content-Type: text/csv")
    payload = await request.body()
    if len(payload) > 2_000_000:
        raise HTTPException(413, "CSV must be at most 2 MB")
    try:
        result = import_researchers(db, payload.decode("utf-8-sig"))
    except UnicodeDecodeError:
        raise HTTPException(422, "CSV must be UTF-8 encoded")
    except ValueError as exc:
        db.rollback()
        raise HTTPException(422, str(exc)) from exc
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "CSV import violates a database uniqueness constraint") from exc
    return ResearcherImportResponse(**vars(result))


@router.get("", response_model=list[ResearcherResponse])
def list_researchers(db: Session = Depends(get_db)):
    stmt = select(Researcher).order_by(Researcher.id)

    return db.scalars(stmt).all()


@router.get(
    "/{researcher_id}",
    response_model=ResearcherResponse,
)
def get_researcher(
    researcher_id: int,
    db: Session = Depends(get_db),
):
    researcher = db.get(Researcher, researcher_id)

    if researcher is None:
        raise HTTPException(
            status_code=404,
            detail="Researcher not found",
        )

    return researcher


@router.post(
    "",
    response_model=ResearcherResponse,
    status_code=201,
)
def create_researcher(
    payload: ResearcherCreate,
    db: Session = Depends(get_db),
):
    researcher = Researcher(**payload.model_dump())

    db.add(researcher)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Researcher email or ORCID already exists",
        )

    db.refresh(researcher)
    return researcher


@router.patch(
    "/{researcher_id}",
    response_model=ResearcherResponse,
)
def update_researcher(
    researcher_id: int,
    payload: ResearcherUpdate,
    db: Session = Depends(get_db),
):
    researcher = db.get(Researcher, researcher_id)

    if researcher is None:
        raise HTTPException(
            status_code=404,
            detail="Researcher not found",
        )

    changes = payload.model_dump(exclude_unset=True)

    for field, value in changes.items():
        if value is None and field != "orcid":
            raise HTTPException(
                status_code=422,
                detail=f"{field} cannot be null",
            )
        setattr(researcher, field, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Researcher email or ORCID already exists",
        )
    db.refresh(researcher)

    return researcher


@router.delete(
    "/{researcher_id}",
    status_code=204,
)
def delete_researcher(
    researcher_id: int,
    db: Session = Depends(get_db),
):
    researcher = db.get(Researcher, researcher_id)

    if researcher is None:
        raise HTTPException(
            status_code=404,
            detail="Researcher not found",
        )

    db.delete(researcher)
    db.commit()