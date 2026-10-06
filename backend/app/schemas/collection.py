import uuid
from datetime import datetime

from pydantic import BaseModel


class RunSummary(BaseModel):
    id: uuid.UUID
    source_code: str
    source_name: str
    triggered_by: str
    status: str
    mode: str
    started_at: datetime
    finished_at: datetime | None
    fetched_count: int
    valid_count: int
    new_count: int
    changed_count: int
    unchanged_count: int
    failed_count: int
    error_code: str | None
    error_message: str | None
    request_metadata: dict
    artifact_count: int = 0


class SourceStatus(BaseModel):
    code: str
    name: str
    source_type: str
    entry_url: str
    official_evidence_url: str | None
    enabled: bool
    request_interval_ms: int
    timeout_seconds: int
    max_retries: int
    active_run: RunSummary | None
    latest_run: RunSummary | None
    latest_success_at: datetime | None


class RunListResponse(BaseModel):
    items: list[RunSummary]
    page: int
    page_size: int
    total: int
    total_pages: int


class ArtifactResponse(BaseModel):
    id: uuid.UUID
    artifact_type: str
    relative_path: str
    request_url: str
    content_type: str | None
    http_status: int | None
    byte_size: int
    sha256: str
    captured_at: datetime
    request_headers: dict
    response_headers: dict
    artifact_metadata: dict


class ArtifactListResponse(BaseModel):
    items: list[ArtifactResponse]
    page: int
    page_size: int
    total: int
    total_pages: int
