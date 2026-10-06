"""track replay processing time separately

Revision ID: 20261006_0008
Revises: 20261006_0007
"""

from alembic import op
import sqlalchemy as sa


revision = "20261006_0008"
down_revision = "20261006_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("last_replay_seen_at", sa.DateTime(timezone=True), nullable=True))
    # Repair the prior replay bug only when a structured value for the exact same
    # raw deadline is already preserved in this job's observation history.
    op.execute(
        """
        UPDATE jobs AS j
        SET deadline_at = known.deadline_at
        FROM (
            SELECT jo.job_id, jo.deadline_raw, max(jo.deadline_at) AS deadline_at
            FROM job_observations AS jo
            WHERE jo.deadline_at IS NOT NULL
            GROUP BY jo.job_id, jo.deadline_raw
        ) AS known
        WHERE known.job_id = j.id
          AND j.deadline_raw IS NOT NULL
          AND j.deadline_at IS NULL
          AND known.deadline_raw = j.deadline_raw
        """
    )
    op.execute(
        """
        UPDATE jobs AS j
        SET last_replay_seen_at = latest.observed_at
        FROM (
            SELECT jo.job_id, max(jo.observed_at) AS observed_at
            FROM job_observations AS jo
            JOIN collection_runs AS cr ON cr.id = jo.run_id
            WHERE cr.mode = 'replay'
            GROUP BY jo.job_id
        ) AS latest
        WHERE latest.job_id = j.id
        """
    )


def downgrade() -> None:
    op.drop_column("jobs", "last_replay_seen_at")
