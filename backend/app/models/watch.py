import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class JobWatch(Base):
    __tablename__ = "job_watches"
    __table_args__ = (
        CheckConstraint(
            "unwatched_at IS NULL OR unwatched_at >= watched_at",
            name="ck_job_watches_time_order",
        ),
        Index("ix_job_watches_user_watched", "user_id", "watched_at"),
        Index("ix_job_watches_user_job", "user_id", "job_id"),
        Index("ix_job_watches_job_window", "job_id", "watched_at", "unwatched_at"),
        Index(
            "uq_job_watches_active_user_job",
            "user_id",
            "job_id",
            unique=True,
            postgresql_where=text("unwatched_at IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="RESTRICT"), nullable=False
    )
    watched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    unwatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class WatchEvent(Base):
    __tablename__ = "watch_events"
    __table_args__ = (
        UniqueConstraint("watch_id", "change_set_id", name="uq_watch_events_watch_change"),
        Index("ix_watch_events_watch_id", "watch_id"),
        Index("ix_watch_events_change_set_id", "change_set_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    watch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_watches.id", ondelete="RESTRICT"), nullable=False
    )
    change_set_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_change_sets.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
