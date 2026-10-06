import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.auth import CurrentUser
from app.db.session import get_db
from app.schemas.jobs import JobDetail, JobListResponse, JobSummary
from app.services.jobs import get_job_detail, job_summary, list_cities, search_jobs

router = APIRouter(prefix="/jobs", tags=["jobs"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=JobListResponse)
def jobs(
    user: CurrentUser,
    db: DbSession,
    keyword: str | None = Query(default=None, max_length=200),
    city: str | None = Query(default=None, max_length=150),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> JobListResponse:
    return search_jobs(db, keyword=keyword, city=city, page=page, page_size=page_size, user_id=user.id)


@router.get("/cities", response_model=list[str])
def cities(_user: CurrentUser, db: DbSession) -> list[str]:
    return list_cities(db)


@router.get("/summary", response_model=JobSummary)
def summary(_user: CurrentUser, db: DbSession) -> JobSummary:
    return job_summary(db)


@router.get("/{job_id}", response_model=JobDetail)
def detail(job_id: uuid.UUID, user: CurrentUser, db: DbSession) -> JobDetail:
    job = get_job_detail(db, job_id, user.id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="岗位不存在")
    return job
