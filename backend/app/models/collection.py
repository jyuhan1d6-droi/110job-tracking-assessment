import uuid
from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CollectionRun(Base):
    __tablename__ = "collection_runs"
    __table_args__ = (
        CheckConstraint("mode IN ('live', 'replay')", name="ck_collection_runs_mode"),
        CheckConstraint(
            "status IN ('pending', 'running', 'success', 'partial', 'failed')",
            name="ck_collection_runs_status",
        ),
        CheckConstraint(
            "fetched_count >= 0 AND valid_count >= 0 AND new_count >= 0 "
            "AND changed_count >= 0 AND unchanged_count >= 0 AND failed_count >= 0",
            name="ck_collection_runs_nonnegative_counts",
        ),
        CheckConstraint(
            "status IN ('pending', 'running') OR new_count + changed_count + unchanged_count = valid_count",
            name="ck_collection_runs_completed_counts",
        ),
        CheckConstraint("finished_at IS NULL OR finished_at >= started_at", name="ck_collection_runs_time_order"),
        Index(
            "uq_collection_runs_active_source",
            "source_id",
            unique=True,
            postgresql_where=text("status IN ('pending', 'running')"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False)
    triggered_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    mode: Mapped[str] = mapped_column(String(16), nullable=False, default="live")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    http_status: Mapped[int | None] = mapped_column(Integer)
    fetched_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    valid_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    new_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    changed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unchanged_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_code: Mapped[str | None] = mapped_column(String(100))
    error_message: Mapped[str | None] = mapped_column(Text)
    request_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class CollectionArtifact(Base):
    __tablename__ = "collection_artifacts"
    __table_args__ = (
        CheckConstraint(
            "artifact_type IN ('list_html', 'detail_html', 'list_json', 'detail_json', "
            "'replay_manifest', 'replay_snapshot')",
            name="ck_collection_artifacts_type",
        ),
        CheckConstraint("byte_size >= 0", name="ck_collection_artifacts_size"),
        CheckConstraint("sha256 ~ '^[0-9a-f]{64}$'", name="ck_collection_artifacts_sha256"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("collection_runs.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    artifact_type: Mapped[str] = mapped_column(String(32), nullable=False)
    relative_path: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    request_url: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(128))
    http_status: Mapped[int | None] = mapped_column(Integer)
    byte_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    request_headers: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    response_headers: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    artifact_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
