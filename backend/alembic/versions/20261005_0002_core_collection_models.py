"""Create core collection, evidence, job, observation and change models."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261005_0002"
down_revision: str | None = "20261005_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("display_name", sa.String(100), server_default="", nullable=False))
    op.add_column("users", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))
    op.create_check_constraint("ck_users_role", "users", "role IN ('maintainer', 'job_seeker')")
    op.alter_column("users", "display_name", server_default=None)

    op.add_column("sources", sa.Column("official_evidence_url", sa.String(512), nullable=True))
    op.add_column("sources", sa.Column("collector_key", sa.String(64), server_default="", nullable=False))
    op.add_column("sources", sa.Column("request_interval_ms", sa.Integer(), server_default="1500", nullable=False))
    op.add_column("sources", sa.Column("timeout_seconds", sa.Integer(), server_default="15", nullable=False))
    op.add_column("sources", sa.Column("max_retries", sa.Integer(), server_default="2", nullable=False))
    op.add_column("sources", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    op.create_check_constraint(
        "ck_sources_type", "sources", "source_type IN ('recruitment_platform', 'company_careers')"
    )
    op.create_check_constraint("ck_sources_request_interval", "sources", "request_interval_ms >= 0")
    op.create_check_constraint("ck_sources_timeout", "sources", "timeout_seconds > 0")
    op.create_check_constraint("ck_sources_retries", "sources", "max_retries >= 0")
    op.alter_column("sources", "collector_key", server_default=None)
    op.alter_column("sources", "request_interval_ms", server_default=None)
    op.alter_column("sources", "timeout_seconds", server_default=None)
    op.alter_column("sources", "max_retries", server_default=None)

    op.create_table(
        "collection_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("triggered_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mode", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("fetched_count", sa.Integer(), nullable=False),
        sa.Column("valid_count", sa.Integer(), nullable=False),
        sa.Column("new_count", sa.Integer(), nullable=False),
        sa.Column("changed_count", sa.Integer(), nullable=False),
        sa.Column("unchanged_count", sa.Integer(), nullable=False),
        sa.Column("failed_count", sa.Integer(), nullable=False),
        sa.Column("error_code", sa.String(100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("request_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("mode IN ('live', 'replay')", name="ck_collection_runs_mode"),
        sa.CheckConstraint(
            "status IN ('pending', 'running', 'success', 'partial', 'failed')",
            name="ck_collection_runs_status",
        ),
        sa.CheckConstraint(
            "fetched_count >= 0 AND valid_count >= 0 AND new_count >= 0 "
            "AND changed_count >= 0 AND unchanged_count >= 0 AND failed_count >= 0",
            name="ck_collection_runs_nonnegative_counts",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'running') OR new_count + changed_count + unchanged_count = valid_count",
            name="ck_collection_runs_completed_counts",
        ),
        sa.CheckConstraint("finished_at IS NULL OR finished_at >= started_at", name="ck_collection_runs_time_order"),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["triggered_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_collection_runs_active_source",
        "collection_runs",
        ["source_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('pending', 'running')"),
    )

    op.create_table(
        "collection_artifacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("artifact_type", sa.String(32), nullable=False),
        sa.Column("relative_path", sa.Text(), nullable=False),
        sa.Column("request_url", sa.Text(), nullable=False),
        sa.Column("content_type", sa.String(128), nullable=True),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("byte_size", sa.BigInteger(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("request_headers", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("response_headers", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("artifact_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.CheckConstraint(
            "artifact_type IN ('list_html', 'detail_html', 'list_json', 'detail_json', "
            "'replay_manifest', 'replay_snapshot')",
            name="ck_collection_artifacts_type",
        ),
        sa.CheckConstraint("byte_size >= 0", name="ck_collection_artifacts_size"),
        sa.CheckConstraint("sha256 ~ '^[0-9a-f]{64}$'", name="ck_collection_artifacts_sha256"),
        sa.ForeignKeyConstraint(["run_id"], ["collection_runs.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("relative_path"),
    )
    op.create_index("ix_collection_artifacts_run_id", "collection_artifacts", ["run_id"])

    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_identity", sa.String(512), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("company", sa.String(300), nullable=False),
        sa.Column("city", sa.String(150), nullable=False),
        sa.Column("requirements", sa.Text(), nullable=False),
        sa.Column("deadline_raw", sa.Text(), nullable=True),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deadline_provided", sa.Boolean(), nullable=False),
        sa.Column("recruitment_status", sa.String(32), nullable=True),
        sa.Column("status_provided", sa.Boolean(), nullable=False),
        sa.Column("detail_url", sa.Text(), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_live_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_changed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_content_hash", sa.String(64), nullable=False),
        sa.Column("created_by_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_visible", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "recruitment_status IS NULL OR recruitment_status IN ('open', 'closed')", name="ck_jobs_status"
        ),
        sa.ForeignKeyConstraint(["created_by_run_id"], ["collection_runs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["updated_by_run_id"], ["collection_runs.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_id", "external_identity", name="uq_jobs_source_identity"),
    )
    op.create_index("ix_jobs_city", "jobs", ["city"])
    op.create_index("ix_jobs_last_seen", "jobs", ["last_seen_at"])
    op.create_index("ix_jobs_source_status", "jobs", ["source_id", "recruitment_status"])

    op.create_table(
        "job_observations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_identity", sa.String(512), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("company", sa.String(300), nullable=False),
        sa.Column("city", sa.String(150), nullable=False),
        sa.Column("requirements", sa.Text(), nullable=False),
        sa.Column("requirements_provided", sa.Boolean(), nullable=False),
        sa.Column("deadline_raw", sa.Text(), nullable=True),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deadline_provided", sa.Boolean(), nullable=False),
        sa.Column("recruitment_status", sa.String(32), nullable=True),
        sa.Column("status_provided", sa.Boolean(), nullable=False),
        sa.Column("detail_url", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("list_artifact_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("detail_artifact_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("explicit_closed", sa.Boolean(), nullable=False),
        sa.Column("closed_evidence_text", sa.Text(), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "recruitment_status IS NULL OR recruitment_status IN ('open', 'closed')",
            name="ck_job_observations_status",
        ),
        sa.CheckConstraint(
            "recruitment_status IS DISTINCT FROM 'closed' OR "
            "(status_provided AND explicit_closed AND "
            "(detail_artifact_id IS NOT NULL OR closed_evidence_text IS NOT NULL))",
            name="ck_job_observations_explicit_closed",
        ),
        sa.ForeignKeyConstraint(["detail_artifact_id"], ["collection_artifacts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["list_artifact_id"], ["collection_artifacts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["run_id"], ["collection_runs.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id", "external_identity", name="uq_job_observations_run_identity"),
        sa.UniqueConstraint("run_id", "job_id", name="uq_job_observations_run_job"),
    )
    op.create_index("ix_job_observations_run_id", "job_observations", ["run_id"])

    op.create_table(
        "job_change_sets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("observation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("change_hash", sa.String(64), nullable=False),
        sa.Column("origin", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("origin IN ('live', 'replay')", name="ck_job_change_sets_origin"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["observation_id"], ["job_observations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["run_id"], ["collection_runs.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("observation_id", name="uq_job_change_sets_observation"),
        sa.UniqueConstraint("run_id", "job_id", name="uq_job_change_sets_run_job"),
    )

    op.create_table(
        "job_field_changes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("change_set_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("field_name", sa.String(32), nullable=False),
        sa.Column("before_text", sa.Text(), nullable=True),
        sa.Column("after_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "field_name IN ('requirements', 'deadline', 'recruitment_status')",
            name="ck_job_field_changes_name",
        ),
        sa.CheckConstraint("before_text IS DISTINCT FROM after_text", name="ck_job_field_changes_distinct"),
        sa.ForeignKeyConstraint(["change_set_id"], ["job_change_sets.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("change_set_id", "field_name", name="uq_job_field_changes_set_field"),
    )
    op.create_index("ix_job_field_changes_change_set_id", "job_field_changes", ["change_set_id"])


def downgrade() -> None:
    op.drop_index("ix_job_field_changes_change_set_id", table_name="job_field_changes")
    op.drop_table("job_field_changes")
    op.drop_table("job_change_sets")
    op.drop_index("ix_job_observations_run_id", table_name="job_observations")
    op.drop_table("job_observations")
    op.drop_index("ix_jobs_source_status", table_name="jobs")
    op.drop_index("ix_jobs_last_seen", table_name="jobs")
    op.drop_index("ix_jobs_city", table_name="jobs")
    op.drop_table("jobs")
    op.drop_index("ix_collection_artifacts_run_id", table_name="collection_artifacts")
    op.drop_table("collection_artifacts")
    op.drop_index("uq_collection_runs_active_source", table_name="collection_runs")
    op.drop_table("collection_runs")

    op.drop_constraint("ck_sources_retries", "sources", type_="check")
    op.drop_constraint("ck_sources_timeout", "sources", type_="check")
    op.drop_constraint("ck_sources_request_interval", "sources", type_="check")
    op.drop_constraint("ck_sources_type", "sources", type_="check")
    op.drop_column("sources", "updated_at")
    op.drop_column("sources", "max_retries")
    op.drop_column("sources", "timeout_seconds")
    op.drop_column("sources", "request_interval_ms")
    op.drop_column("sources", "collector_key")
    op.drop_column("sources", "official_evidence_url")

    op.drop_constraint("ck_users_role", "users", type_="check")
    op.drop_column("users", "last_login_at")
    op.drop_column("users", "updated_at")
    op.drop_column("users", "display_name")
