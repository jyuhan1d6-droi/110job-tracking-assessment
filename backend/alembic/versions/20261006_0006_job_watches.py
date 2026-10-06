"""Add job watch intervals."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261006_0006"
down_revision: str | None = "20261006_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "job_watches",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("watched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("unwatched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("unwatched_at IS NULL OR unwatched_at >= watched_at", name="ck_job_watches_time_order"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_watches_user_watched", "job_watches", ["user_id", "watched_at"])
    op.create_index("ix_job_watches_user_job", "job_watches", ["user_id", "job_id"])
    op.create_index("ix_job_watches_job_window", "job_watches", ["job_id", "watched_at", "unwatched_at"])
    op.create_index(
        "uq_job_watches_active_user_job",
        "job_watches",
        ["user_id", "job_id"],
        unique=True,
        postgresql_where=sa.text("unwatched_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_job_watches_active_user_job", table_name="job_watches")
    op.drop_index("ix_job_watches_job_window", table_name="job_watches")
    op.drop_index("ix_job_watches_user_job", table_name="job_watches")
    op.drop_index("ix_job_watches_user_watched", table_name="job_watches")
    op.drop_table("job_watches")
