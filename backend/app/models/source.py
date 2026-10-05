import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Source(Base):
    __tablename__ = "sources"
    __table_args__ = (
        CheckConstraint(
            "source_type IN ('recruitment_platform', 'company_careers')", name="ck_sources_type"
        ),
        CheckConstraint("request_interval_ms >= 0", name="ck_sources_request_interval"),
        CheckConstraint("timeout_seconds > 0", name="ck_sources_timeout"),
        CheckConstraint("max_retries >= 0", name="ck_sources_retries"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    entry_url: Mapped[str] = mapped_column(String(512), nullable=False)
    official_evidence_url: Mapped[str | None] = mapped_column(String(512))
    collector_key: Mapped[str] = mapped_column(String(64), nullable=False)
    request_interval_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=1500)
    timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
