from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.resource import Resource
from app.schemas.resource import (
    ResourceCreate,
    ResourceUpdate,
    ResourceResponse,
)

router = APIRouter(
    prefix="/resources",
    tags=["Resources"],
)


@router.get("", response_model=list[ResourceResponse])
def list_resources(db: Session = Depends(get_db)):
    stmt = select(Resource).order_by(Resource.id)
    return db.scalars(stmt).all()


@router.get(
    "/{resource_id}",
    response_model=ResourceResponse,
)
def get_resource(
    resource_id: int,
    db: Session = Depends(get_db),
):
    resource = db.get(Resource, resource_id)

    if resource is None:
        raise HTTPException(404, "Resource not found")

    return resource


@router.post(
    "",
    response_model=ResourceResponse,
    status_code=201,
)
def create_resource(
    payload: ResourceCreate,
    db: Session = Depends(get_db),
):
    resource = Resource(**payload.model_dump())

    db.add(resource)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Resource already exists")

    db.refresh(resource)
    return resource


@router.patch(
    "/{resource_id}",
    response_model=ResourceResponse,
)
def update_resource(
    resource_id: int,
    payload: ResourceUpdate,
    db: Session = Depends(get_db),
):
    resource = db.get(Resource, resource_id)

    if resource is None:
        raise HTTPException(404, "Resource not found")

    changes = payload.model_dump(exclude_unset=True)

    for field, value in changes.items():
        if value is None:
            raise HTTPException(
                422,
                f"{field} cannot be null",
            )
        setattr(resource, field, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Resource already exists")

    db.refresh(resource)
    return resource


@router.delete(
    "/{resource_id}",
    status_code=204,
)
def delete_resource(
    resource_id: int,
    db: Session = Depends(get_db),
):
    resource = db.get(Resource, resource_id)

    if resource is None:
        raise HTTPException(404, "Resource not found")

    db.delete(resource)
    db.commit()
