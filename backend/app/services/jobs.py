import math
import uuid

from sqlalchemy import distinct, exists, false, func, or_, select
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.source import Source
from app.models.watch import JobWatch
from app.schemas.jobs import (
    AppliedFilters,
    JobDetail,
    JobListItem,
    JobListResponse,
    JobSummary,
    SourceBrief,
)


def _source_brief(source: Source) -> SourceBrief:
    return SourceBrief(
        code=source.code,
        name=source.name,
        source_type=source.source_type,
        entry_url=source.entry_url,
    )


def _clean_filter(value: str | None) -> str:
    return (value or "").strip()


def build_job_list_item(job: Job, source: Source, is_watched: bool) -> JobListItem:
    summary = job.requirements[:240]
    if len(job.requirements) > 240:
        summary += "…"
    return JobListItem(
        id=job.id,
        title=job.title,
        company=job.company,
        city=job.city,
        requirements_summary=summary,
        deadline_raw=job.deadline_raw,
        deadline_provided=job.deadline_provided,
        recruitment_status=job.recruitment_status,
        status_provided=job.status_provided,
        detail_url=job.detail_url,
        last_seen_at=job.last_seen_at,
        source=_source_brief(source),
        is_watched=is_watched,
    )


def _watch_expression(user_id: uuid.UUID | None):
    if user_id is None:
        return false()
    return exists(select(JobWatch.id).where(
        JobWatch.job_id == Job.id,
        JobWatch.user_id == user_id,
        JobWatch.unwatched_at.is_(None),
    ))


def search_jobs(
    db: Session,
    *,
    keyword: str | None,
    city: str | None,
    page: int,
    page_size: int,
    user_id: uuid.UUID | None = None,
) -> JobListResponse:
    clean_keyword = _clean_filter(keyword)
    clean_city = _clean_filter(city)
    conditions = [Job.is_visible.is_(True)]
    if clean_keyword:
        conditions.append(
            or_(
                Job.title.icontains(clean_keyword, autoescape=True),
                Job.requirements.icontains(clean_keyword, autoescape=True),
            )
        )
    if clean_city:
        conditions.append(Job.city == clean_city)

    total = db.scalar(select(func.count()).select_from(Job).where(*conditions)) or 0
    rows = db.execute(
        select(Job, Source, _watch_expression(user_id))
        .join(Source, Source.id == Job.source_id)
        .where(*conditions)
        .order_by(Job.last_seen_at.desc(), Job.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    items = []
    for job, source, is_watched in rows:
        items.append(build_job_list_item(job, source, is_watched))
    return JobListResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=math.ceil(total / page_size) if total else 0,
        filters=AppliedFilters(keyword=clean_keyword, city=clean_city),
    )


def list_cities(db: Session) -> list[str]:
    return list(
        db.scalars(
            select(distinct(Job.city))
            .where(Job.is_visible.is_(True), Job.city != "")
            .order_by(Job.city)
        )
    )


def job_summary(db: Session) -> JobSummary:
    total, sources, latest = db.execute(
        select(
            func.count(Job.id),
            func.count(distinct(Job.source_id)),
            func.max(Job.last_seen_at),
        ).where(Job.is_visible.is_(True))
    ).one()
    return JobSummary(
        total_visible_jobs=total or 0,
        sources_with_jobs=sources or 0,
        last_collected_at=latest,
    )


def get_job_detail(db: Session, job_id: uuid.UUID, user_id: uuid.UUID | None = None) -> JobDetail | None:
    row = db.execute(
        select(Job, Source, _watch_expression(user_id))
        .join(Source, Source.id == Job.source_id)
        .where(Job.id == job_id, Job.is_visible.is_(True))
    ).one_or_none()
    if row is None:
        return None
    job, source, is_watched = row
    return JobDetail(
        id=job.id,
        external_identity=job.external_identity,
        title=job.title,
        company=job.company,
        city=job.city,
        requirements=job.requirements,
        deadline_raw=job.deadline_raw,
        deadline_at=job.deadline_at,
        deadline_provided=job.deadline_provided,
        recruitment_status=job.recruitment_status,
        status_provided=job.status_provided,
        detail_url=job.detail_url,
        first_seen_at=job.first_seen_at,
        last_seen_at=job.last_seen_at,
        last_changed_at=job.last_changed_at,
        source=_source_brief(source),
        is_watched=is_watched,
    )
