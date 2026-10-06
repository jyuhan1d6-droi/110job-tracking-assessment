"""Add watch events without backfilling historical changes."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261006_0007"
down_revision: str | None = "20261006_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "watch_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("watch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("change_set_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["change_set_id"], ["job_change_sets.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["watch_id"], ["job_watches.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("watch_id", "change_set_id", name="uq_watch_events_watch_change"),
    )
    op.create_index("ix_watch_events_watch_id", "watch_events", ["watch_id"])
    op.create_index("ix_watch_events_change_set_id", "watch_events", ["change_set_id"])


def downgrade() -> None:
    op.drop_index("ix_watch_events_change_set_id", table_name="watch_events")
    op.drop_index("ix_watch_events_watch_id", table_name="watch_events")
    op.drop_table("watch_events")
