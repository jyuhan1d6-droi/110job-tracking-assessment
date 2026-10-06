import math
import uuid
from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.job import Job, JobChangeSet, JobFieldChange
from app.models.source import Source
from app.models.watch import JobWatch, WatchEvent
from app.schemas.jobs import SourceBrief
from app.schemas.watch_events import (
    ChangedField,
    WatchEventDetail,
    WatchEventListItem,
    WatchEventListResponse,
)


def create_watch_events_for_change_set(db: Session, change_set: JobChangeSet) -> int:
    watches = list(db.scalars(
        select(JobWatch)
        .where(
            JobWatch.job_id == change_set.job_id,
            JobWatch.watched_at <= change_set.detected_at,
            or_(JobWatch.unwatched_at.is_(None), change_set.detected_at < JobWatch.unwatched_at),
        )
        .with_for_update()
    ))
    if not watches:
        return 0
    existing = set(db.scalars(
        select(WatchEvent.watch_id).where(
            WatchEvent.change_set_id == change_set.id,
            WatchEvent.watch_id.in_([watch.id for watch in watches]),
        )
    ))
    additions = [WatchEvent(watch_id=watch.id, change_set_id=change_set.id) for watch in watches if watch.id not in existing]
    db.add_all(additions)
    db.flush()
    return len(additions)


def _source(source: Source) -> SourceBrief:
    return SourceBrief(code=source.code, name=source.name, source_type=source.source_type, entry_url=source.entry_url)


def _fields_by_change(db: Session, change_ids: list[uuid.UUID]) -> dict[uuid.UUID, list[JobFieldChange]]:
    result: dict[uuid.UUID, list[JobFieldChange]] = {change_id: [] for change_id in change_ids}
    if change_ids:
        for field in db.scalars(
            select(JobFieldChange)
            .where(JobFieldChange.change_set_id.in_(change_ids))
            .order_by(JobFieldChange.created_at, JobFieldChange.id)
        ):
            result[field.change_set_id].append(field)
    return result


def _list_item(event, watch, change, job, source, fields) -> WatchEventListItem:
    return WatchEventListItem(
        id=event.id,
        watch_id=watch.id,
        watched_at=watch.watched_at,
        job_id=job.id,
        title=job.title,
        company=job.company,
        city=job.city,
        recruitment_status=job.recruitment_status,
        status_provided=job.status_provided,
        detected_at=change.detected_at,
        origin=change.origin,
        changed_fields=[field.field_name for field in fields],
        change_count=len(fields),
        source=_source(source),
    )


def list_watch_events(db: Session, user_id: uuid.UUID, page: int, page_size: int) -> WatchEventListResponse:
    owner = JobWatch.user_id == user_id
    total = db.scalar(select(func.count()).select_from(WatchEvent).join(JobWatch).where(owner)) or 0
    rows = db.execute(
        select(WatchEvent, JobWatch, JobChangeSet, Job, Source)
        .join(JobWatch, JobWatch.id == WatchEvent.watch_id)
        .join(JobChangeSet, JobChangeSet.id == WatchEvent.change_set_id)
        .join(Job, Job.id == JobChangeSet.job_id)
        .join(Source, Source.id == Job.source_id)
        .where(owner)
        .order_by(JobChangeSet.detected_at.desc(), WatchEvent.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    fields = _fields_by_change(db, [row[2].id for row in rows])
    return WatchEventListResponse(
        items=[_list_item(event, watch, change, job, source, fields[change.id]) for event, watch, change, job, source in rows],
        page=page,
        page_size=page_size,
        total=total,
        total_pages=math.ceil(total / page_size) if total else 0,
    )


def get_watch_event(db: Session, user_id: uuid.UUID, event_id: uuid.UUID) -> WatchEventDetail | None:
    row = db.execute(
        select(WatchEvent, JobWatch, JobChangeSet, Job, Source)
        .join(JobWatch, JobWatch.id == WatchEvent.watch_id)
        .join(JobChangeSet, JobChangeSet.id == WatchEvent.change_set_id)
        .join(Job, Job.id == JobChangeSet.job_id)
        .join(Source, Source.id == Job.source_id)
        .where(WatchEvent.id == event_id, JobWatch.user_id == user_id)
    ).one_or_none()
    if row is None:
        return None
    event, watch, change, job, source = row
    fields = _fields_by_change(db, [change.id])[change.id]
    item = _list_item(event, watch, change, job, source, fields)
    return WatchEventDetail(
        **item.model_dump(),
        detail_url=job.detail_url,
        changes=[ChangedField(field_name=f.field_name, before_text=f.before_text, after_text=f.after_text) for f in fields],
    )
