from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.researcher import Researcher
from app.schemas.researcher import (
    ResearcherCreate,
    ResearcherUpdate,
    ResearcherResponse,
)

router = APIRouter(
    prefix="/researchers",
    tags=["Researchers"],
)


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
            detail="Researcher ORCID already exists",
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
        if value is None:
            raise HTTPException(
                status_code=422,
                detail=f"{field} cannot be null",
            )
        setattr(researcher, field, value)

    db.commit()
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