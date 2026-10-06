import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReplayJob(BaseModel):
    model_config = ConfigDict(extra="forbid")

    identity: str
    title: str
    company: str
    city: str
    requirements: str
    deadline: str | None
    status: str | None
    detail_url: str = Field(alias="detailUrl")
    explicit_closed_evidence: str | None = Field(default=None, alias="explicitClosedEvidence")


class ReplaySnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(alias="sourceId")
    jobs: list[ReplayJob]


class ReplayScenario(BaseModel):
    id: str
    step_id: str
    name: str
    source_code: str
    kind: str
    expected: str
    declared_fields: list[str]
    provenance_file: str
    provenance_sha256: str
    snapshot_file: str | None
    snapshot_sha256: str | None
    failure_reason: str | None
    valid: bool
    validation_error: str | None = None


class ReplayRunResponse(BaseModel):
    id: uuid.UUID
    status: str
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
