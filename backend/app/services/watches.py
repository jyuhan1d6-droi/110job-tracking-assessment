import math
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.source import Source
from app.models.watch import JobWatch
from app.schemas.watches import WatchedJobItem, WatchListResponse, WatchResponse
from app.services.jobs import build_job_list_item


def active_watch(db: Session, user_id: uuid.UUID, job_id: uuid.UUID) -> JobWatch | None:
    return db.scalar(select(JobWatch).where(
        JobWatch.user_id == user_id,
        JobWatch.job_id == job_id,
        JobWatch.unwatched_at.is_(None),
    ))


def _lock_active_watch(db: Session, user_id: uuid.UUID, job_id: uuid.UUID) -> JobWatch | None:
    return db.scalar(
        select(JobWatch)
        .where(
            JobWatch.user_id == user_id,
            JobWatch.job_id == job_id,
            JobWatch.unwatched_at.is_(None),
        )
        .with_for_update()
    )


def watch_job(db: Session, user_id: uuid.UUID, job_id: uuid.UUID) -> WatchResponse | None:
    job_exists = db.scalar(select(Job.id).where(Job.id == job_id, Job.is_visible.is_(True)))
    if job_exists is None:
        return None
    current = active_watch(db, user_id, job_id)
    if current is None:
        current = JobWatch(user_id=user_id, job_id=job_id, watched_at=datetime.now(timezone.utc))
        db.add(current)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            current = active_watch(db, user_id, job_id)
            if current is None:
                raise
        db.refresh(current)
    return WatchResponse(id=current.id, job_id=current.job_id, watched_at=current.watched_at, is_active=True)


def unwatch_job(db: Session, user_id: uuid.UUID, job_id: uuid.UUID) -> None:
    current = _lock_active_watch(db, user_id, job_id)
    if current is not None:
        current.unwatched_at = datetime.now(timezone.utc)
        db.commit()


def list_watched_jobs(db: Session, user_id: uuid.UUID, page: int, page_size: int) -> WatchListResponse:
    conditions = (
        JobWatch.user_id == user_id,
        JobWatch.unwatched_at.is_(None),
        Job.is_visible.is_(True),
    )
    total = db.scalar(
        select(func.count()).select_from(JobWatch).join(Job, Job.id == JobWatch.job_id).where(*conditions)
    ) or 0
    rows = db.execute(
        select(JobWatch, Job, Source)
        .join(Job, Job.id == JobWatch.job_id)
        .join(Source, Source.id == Job.source_id)
        .where(*conditions)
        .order_by(JobWatch.watched_at.desc(), JobWatch.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return WatchListResponse(
        items=[WatchedJobItem(
            watch_id=watch.id,
            watched_at=watch.watched_at,
            job=build_job_list_item(job, source, True),
        ) for watch, job, source in rows],
        page=page,
        page_size=page_size,
        total=total,
        total_pages=math.ceil(total / page_size) if total else 0,
    )


def watch_covers(watch: JobWatch, changed_at: datetime) -> bool:
    return watch.watched_at <= changed_at and (watch.unwatched_at is None or changed_at < watch.unwatched_at)
