import uuid
from datetime import datetime

from pydantic import BaseModel


class SourceBrief(BaseModel):
    code: str
    name: str
    source_type: str
    entry_url: str


class JobListItem(BaseModel):
    id: uuid.UUID
    title: str
    company: str
    city: str
    requirements_summary: str
    deadline_raw: str | None
    deadline_provided: bool
    recruitment_status: str | None
    status_provided: bool
    detail_url: str
    last_seen_at: datetime
    last_live_seen_at: datetime | None
    last_update_mode: str
    source: SourceBrief
    is_watched: bool


class JobDetail(BaseModel):
    id: uuid.UUID
    external_identity: str
    title: str
    company: str
    city: str
    requirements: str
    deadline_raw: str | None
    deadline_at: datetime | None
    deadline_provided: bool
    recruitment_status: str | None
    status_provided: bool
    detail_url: str
    first_seen_at: datetime
    last_seen_at: datetime
    last_live_seen_at: datetime | None
    last_update_mode: str
    last_changed_at: datetime | None
    source: SourceBrief
    is_watched: bool


class AppliedFilters(BaseModel):
    keyword: str
    city: str


class JobListResponse(BaseModel):
    items: list[JobListItem]
    page: int
    page_size: int
    total: int
    total_pages: int
    filters: AppliedFilters


class JobSummary(BaseModel):
    total_visible_jobs: int
    sources_with_jobs: int
    last_collected_at: datetime | None
