import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.jobs import JobListItem


class WatchResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    watched_at: datetime
    is_active: bool


class WatchedJobItem(BaseModel):
    watch_id: uuid.UUID
    watched_at: datetime
    job: JobListItem


class WatchListResponse(BaseModel):
    items: list[WatchedJobItem]
    page: int
    page_size: int
    total: int
    total_pages: int
