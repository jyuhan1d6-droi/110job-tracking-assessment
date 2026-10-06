import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("source_id", "external_identity", name="uq_jobs_source_identity"),
        CheckConstraint(
            "recruitment_status IS NULL OR recruitment_status IN ('open', 'closed')",
            name="ck_jobs_status",
        ),
        CheckConstraint(
            "status_provided = (recruitment_status IS NOT NULL)", name="ck_jobs_status_provided"
        ),
        CheckConstraint(
            "(deadline_provided AND deadline_raw IS NOT NULL) OR "
            "(NOT deadline_provided AND deadline_raw IS NULL AND deadline_at IS NULL)",
            name="ck_jobs_deadline_provided",
        ),
        CheckConstraint("current_content_hash ~ '^[0-9a-f]{64}$'", name="ck_jobs_content_hash"),
        Index("ix_jobs_city", "city"),
        Index("ix_jobs_source_status", "source_id", "recruitment_status"),
        Index("ix_jobs_last_seen", "last_seen_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False)
    external_identity: Mapped[str] = mapped_column(String(512), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    company: Mapped[str] = mapped_column(String(300), nullable=False)
    city: Mapped[str] = mapped_column(String(150), nullable=False)
    requirements: Mapped[str] = mapped_column(Text, nullable=False)
    deadline_raw: Mapped[str | None] = mapped_column(Text)
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deadline_provided: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recruitment_status: Mapped[str | None] = mapped_column(String(32))
    status_provided: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    detail_url: Mapped[str] = mapped_column(Text, nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_live_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_replay_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    current_content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_by_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("collection_runs.id", ondelete="RESTRICT"), nullable=False
    )
    updated_by_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("collection_runs.id", ondelete="RESTRICT"), nullable=False
    )
    is_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class JobObservation(Base):
    __tablename__ = "job_observations"
    __table_args__ = (
        UniqueConstraint("run_id", "job_id", name="uq_job_observations_run_job"),
        UniqueConstraint("run_id", "external_identity", name="uq_job_observations_run_identity"),
        CheckConstraint(
            "recruitment_status IS NULL OR recruitment_status IN ('open', 'closed')",
            name="ck_job_observations_status",
        ),
        CheckConstraint(
            "status_provided = (recruitment_status IS NOT NULL)",
            name="ck_job_observations_status_provided",
        ),
        CheckConstraint(
            "(deadline_provided AND deadline_raw IS NOT NULL) OR "
            "(NOT deadline_provided AND deadline_raw IS NULL AND deadline_at IS NULL)",
            name="ck_job_observations_deadline_provided",
        ),
        CheckConstraint("content_hash ~ '^[0-9a-f]{64}$'", name="ck_job_observations_content_hash"),
        CheckConstraint(
            "recruitment_status IS DISTINCT FROM 'closed' OR "
            "(status_provided AND explicit_closed AND "
            "(detail_artifact_id IS NOT NULL OR closed_evidence_text IS NOT NULL))",
            name="ck_job_observations_explicit_closed",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("collection_runs.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id", ondelete="RESTRICT"), nullable=False)
    external_identity: Mapped[str] = mapped_column(String(512), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    company: Mapped[str] = mapped_column(String(300), nullable=False)
    city: Mapped[str] = mapped_column(String(150), nullable=False)
    requirements: Mapped[str] = mapped_column(Text, nullable=False)
    deadline_raw: Mapped[str | None] = mapped_column(Text)
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deadline_provided: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recruitment_status: Mapped[str | None] = mapped_column(String(32))
    status_provided: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    detail_url: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    list_artifact_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("collection_artifacts.id", ondelete="RESTRICT")
    )
    detail_artifact_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("collection_artifacts.id", ondelete="RESTRICT")
    )
    explicit_closed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    closed_evidence_text: Mapped[str | None] = mapped_column(Text)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class JobChangeSet(Base):
    __tablename__ = "job_change_sets"
    __table_args__ = (
        UniqueConstraint("run_id", "job_id", name="uq_job_change_sets_run_job"),
        UniqueConstraint("observation_id", name="uq_job_change_sets_observation"),
        CheckConstraint("origin IN ('live', 'replay')", name="ck_job_change_sets_origin"),
        CheckConstraint("change_hash ~ '^[0-9a-f]{64}$'", name="ck_job_change_sets_hash"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id", ondelete="RESTRICT"), nullable=False)
    run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("collection_runs.id", ondelete="RESTRICT"), nullable=False
    )
    observation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("job_observations.id", ondelete="RESTRICT"), nullable=False
    )
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    change_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    origin: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class JobFieldChange(Base):
    __tablename__ = "job_field_changes"
    __table_args__ = (
        UniqueConstraint("change_set_id", "field_name", name="uq_job_field_changes_set_field"),
        CheckConstraint(
            "field_name IN ('requirements', 'deadline', 'recruitment_status')",
            name="ck_job_field_changes_name",
        ),
        CheckConstraint("before_text IS DISTINCT FROM after_text", name="ck_job_field_changes_distinct"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    change_set_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("job_change_sets.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    field_name: Mapped[str] = mapped_column(String(32), nullable=False)
    before_text: Mapped[str | None] = mapped_column(Text)
    after_text: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
