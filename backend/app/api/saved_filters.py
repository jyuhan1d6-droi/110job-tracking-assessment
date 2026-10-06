import uuid

from fastapi import APIRouter, HTTPException, Response, status

from app.api.auth import CurrentUser, DbSession
from app.schemas.saved_filters import SavedFilterInput, SavedFilterResponse
from app.services.saved_filters import (
    DuplicateFilterNameError,
    create_saved_filter,
    delete_saved_filter,
    find_owned_filter,
    list_saved_filters,
    update_saved_filter,
)

router = APIRouter(prefix="/saved-filters", tags=["saved filters"])


def _not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="筛选方案不存在")


def _duplicate() -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail="已存在同名筛选方案")


@router.get("", response_model=list[SavedFilterResponse])
def index(user: CurrentUser, db: DbSession):
    return list_saved_filters(db, user.id)


@router.post("", response_model=SavedFilterResponse, status_code=status.HTTP_201_CREATED)
def create(payload: SavedFilterInput, user: CurrentUser, db: DbSession):
    try:
        return create_saved_filter(db, user.id, payload)
    except DuplicateFilterNameError:
        raise _duplicate()


@router.put("/{filter_id}", response_model=SavedFilterResponse)
def update(filter_id: uuid.UUID, payload: SavedFilterInput, user: CurrentUser, db: DbSession):
    item = find_owned_filter(db, user.id, filter_id)
    if item is None:
        raise _not_found()
    try:
        return update_saved_filter(db, item, payload)
    except DuplicateFilterNameError:
        raise _duplicate()


@router.delete("/{filter_id}", status_code=status.HTTP_204_NO_CONTENT)
def destroy(filter_id: uuid.UUID, user: CurrentUser, db: DbSession) -> Response:
    item = find_owned_filter(db, user.id, filter_id)
    if item is None:
        raise _not_found()
    delete_saved_filter(db, item)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
