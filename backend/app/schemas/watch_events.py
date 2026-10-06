import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.jobs import SourceBrief


class ChangedField(BaseModel):
    field_name: str
    before_text: str | None
    after_text: str | None


class WatchEventListItem(BaseModel):
    id: uuid.UUID
    watch_id: uuid.UUID
    watched_at: datetime
    job_id: uuid.UUID
    title: str
    company: str
    city: str
    recruitment_status: str | None
    status_provided: bool
    detected_at: datetime
    origin: str
    changed_fields: list[str]
    change_count: int
    source: SourceBrief


class WatchEventListResponse(BaseModel):
    items: list[WatchEventListItem]
    page: int
    page_size: int
    total: int
    total_pages: int


class WatchEventDetail(WatchEventListItem):
    detail_url: str
    changes: list[ChangedField]
