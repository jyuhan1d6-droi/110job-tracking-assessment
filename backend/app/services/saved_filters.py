import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.saved_filter import SavedFilter
from app.schemas.saved_filters import SavedFilterInput


class DuplicateFilterNameError(Exception):
    pass


def list_saved_filters(db: Session, user_id: uuid.UUID) -> list[SavedFilter]:
    return list(db.scalars(
        select(SavedFilter)
        .where(SavedFilter.user_id == user_id)
        .order_by(SavedFilter.updated_at.desc(), SavedFilter.id.asc())
    ))


def find_owned_filter(db: Session, user_id: uuid.UUID, filter_id: uuid.UUID) -> SavedFilter | None:
    return db.scalar(select(SavedFilter).where(SavedFilter.id == filter_id, SavedFilter.user_id == user_id))


def _commit(db: Session, item: SavedFilter) -> SavedFilter:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if getattr(exc.orig, "sqlstate", None) == "23505":
            raise DuplicateFilterNameError from exc
        raise
    db.refresh(item)
    return item


def create_saved_filter(db: Session, user_id: uuid.UUID, payload: SavedFilterInput) -> SavedFilter:
    item = SavedFilter(user_id=user_id, **payload.model_dump())
    db.add(item)
    return _commit(db, item)


def update_saved_filter(db: Session, item: SavedFilter, payload: SavedFilterInput) -> SavedFilter:
    for field, value in payload.model_dump().items():
        setattr(item, field, value)
    return _commit(db, item)


def delete_saved_filter(db: Session, item: SavedFilter) -> None:
    db.delete(item)
    db.commit()
