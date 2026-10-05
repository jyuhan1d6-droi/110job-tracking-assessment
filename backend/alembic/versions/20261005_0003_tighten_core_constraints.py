"""Remove redundant observation flag and tighten core value constraints."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261005_0003"
down_revision: str | None = "20261005_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("job_observations", "requirements_provided")

    op.create_check_constraint(
        "ck_jobs_status_provided", "jobs", "status_provided = (recruitment_status IS NOT NULL)"
    )
    op.create_check_constraint(
        "ck_jobs_deadline_provided",
        "jobs",
        "(deadline_provided AND deadline_raw IS NOT NULL) OR "
        "(NOT deadline_provided AND deadline_raw IS NULL AND deadline_at IS NULL)",
    )
    op.create_check_constraint(
        "ck_jobs_content_hash", "jobs", "current_content_hash ~ '^[0-9a-f]{64}$'"
    )

    op.create_check_constraint(
        "ck_job_observations_status_provided",
        "job_observations",
        "status_provided = (recruitment_status IS NOT NULL)",
    )
    op.create_check_constraint(
        "ck_job_observations_deadline_provided",
        "job_observations",
        "(deadline_provided AND deadline_raw IS NOT NULL) OR "
        "(NOT deadline_provided AND deadline_raw IS NULL AND deadline_at IS NULL)",
    )
    op.create_check_constraint(
        "ck_job_observations_content_hash", "job_observations", "content_hash ~ '^[0-9a-f]{64}$'"
    )
    op.create_check_constraint(
        "ck_job_change_sets_hash", "job_change_sets", "change_hash ~ '^[0-9a-f]{64}$'"
    )


def downgrade() -> None:
    op.drop_constraint("ck_job_change_sets_hash", "job_change_sets", type_="check")
    op.drop_constraint("ck_job_observations_content_hash", "job_observations", type_="check")
    op.drop_constraint("ck_job_observations_deadline_provided", "job_observations", type_="check")
    op.drop_constraint("ck_job_observations_status_provided", "job_observations", type_="check")
    op.drop_constraint("ck_jobs_content_hash", "jobs", type_="check")
    op.drop_constraint("ck_jobs_deadline_provided", "jobs", type_="check")
    op.drop_constraint("ck_jobs_status_provided", "jobs", type_="check")

    op.add_column(
        "job_observations",
        sa.Column("requirements_provided", sa.Boolean(), server_default=sa.text("true"), nullable=False),
    )
    op.alter_column("job_observations", "requirements_provided", server_default=None)
