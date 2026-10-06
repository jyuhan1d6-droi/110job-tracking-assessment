import uuid

from fastapi import APIRouter, Query, Response, status

from app.api.auth import CurrentUser, DbSession
from app.schemas.watches import WatchListResponse, WatchResponse
from app.services.watches import list_watched_jobs, unwatch_job, watch_job

router = APIRouter(tags=["watches"])


@router.post("/jobs/{job_id}/watch", response_model=WatchResponse)
def create_watch(job_id: uuid.UUID, user: CurrentUser, db: DbSession):
    watch = watch_job(db, user.id, job_id)
    if watch is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="岗位不存在")
    return watch


@router.delete("/jobs/{job_id}/watch", status_code=status.HTTP_204_NO_CONTENT)
def delete_watch(job_id: uuid.UUID, user: CurrentUser, db: DbSession) -> Response:
    unwatch_job(db, user.id, job_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/watches", response_model=WatchListResponse)
def watches(
    user: CurrentUser,
    db: DbSession,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    return list_watched_jobs(db, user.id, page, page_size)
