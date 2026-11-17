from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.grant import Grant
from app.models.researcher import Researcher
from app.schemas.grant import GrantCreate, GrantResponse

router = APIRouter(prefix="/grants", tags=["Grants"])


@router.get("", response_model=list[GrantResponse])
def list_grants(db: Session = Depends(get_db)):
    return db.scalars(select(Grant).order_by(Grant.award_date.desc(), Grant.id)).all()


@router.post("", response_model=GrantResponse, status_code=201)
def create_grant(payload: GrantCreate, db: Session = Depends(get_db)):
    # Checked here so a bad id is a 422, not a foreign-key error from the database.
    if payload.researcher_id is not None and db.get(Researcher, payload.researcher_id) is None:
        raise HTTPException(422, "Researcher not found")
    grant = Grant(**payload.model_dump())
    db.add(grant)
    db.commit()
    db.refresh(grant)
    return grant


@router.delete("/{grant_id}", status_code=204)
def delete_grant(grant_id: int, db: Session = Depends(get_db)):
    grant = db.get(Grant, grant_id)
    if grant is None:
        raise HTTPException(404, "Grant not found")
    db.delete(grant)
    db.commit()
