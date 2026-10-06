import uuid

from fastapi import APIRouter, HTTPException, Query, status

from app.api.auth import CurrentUser, DbSession
from app.schemas.watch_events import WatchEventDetail, WatchEventListResponse
from app.services.watch_events import get_watch_event, list_watch_events

router = APIRouter(prefix="/watch-events", tags=["watch events"])


@router.get("", response_model=WatchEventListResponse)
def index(
    user: CurrentUser,
    db: DbSession,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    return list_watch_events(db, user.id, page, page_size)


@router.get("/{event_id}", response_model=WatchEventDetail)
def detail(event_id: uuid.UUID, user: CurrentUser, db: DbSession):
    event = get_watch_event(db, user.id, event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="关注动态不存在")
    return event
