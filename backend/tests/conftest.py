import os
from pathlib import Path

import pytest
from sqlalchemy import text, select

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.collection import CollectionRun
from app.models.job import Job
from app.models.source import Source
from app.models.user import User


BUSINESS_TABLES = (
    "watch_events", "job_watches", "saved_filters", "job_field_changes", "job_change_sets",
    "job_observations", "jobs", "collection_artifacts", "collection_runs", "auth_sessions",
)


def _assert_isolated_environment() -> None:
    database_name = settings.database_url.rsplit("/", 1)[-1].split("?", 1)[0]
    if settings.app_env != "test" or not database_name.endswith("_test"):
        raise RuntimeError("测试拒绝运行：必须使用 APP_ENV=test 和独立的 *_test 数据库")
    evidence = Path(settings.evidence_root).resolve()
    source = Path(os.environ.get("SOURCE_EVIDENCE_ROOT", "/source-evidence")).resolve()
    if evidence == source or source in evidence.parents:
        raise RuntimeError("测试 evidence 目录必须与只读正式证据目录隔离")


def _clean_database() -> None:
    with SessionLocal() as db:
        db.execute(text(f"TRUNCATE TABLE {', '.join(BUSINESS_TABLES)} RESTART IDENTITY CASCADE"))
        db.commit()


def _seed_baseline_job() -> None:
    with SessionLocal() as db:
        maintainer = db.scalar(select(User).where(User.username == "maintainer"))
        source = db.scalar(select(Source).where(Source.code == "360-careers"))
        run = CollectionRun(
            source_id=source.id, triggered_by_user_id=maintainer.id, mode="live", status="success",
            fetched_count=1, valid_count=1, new_count=1, changed_count=0,
            unchanged_count=0, failed_count=0, request_metadata={"fixture": True},
        )
        db.add(run)
        db.flush()
        db.add(Job(
            source_id=source.id, external_identity="360-careers:test-baseline", title="测试基线岗位",
            company="360", city="北京", requirements="Python 后端与数据库",
            deadline_provided=False, status_provided=False,
            detail_url="https://hr.360.cn/hr/detail/test-baseline",
            first_seen_at=run.started_at, last_seen_at=run.started_at, last_live_seen_at=run.started_at,
            current_content_hash="0" * 64, created_by_run_id=run.id, updated_by_run_id=run.id,
            is_visible=True,
        ))
        db.commit()


@pytest.fixture(scope="session", autouse=True)
def isolated_test_guard():
    _assert_isolated_environment()
    yield


@pytest.fixture(autouse=True)
def clean_test_state():
    evidence_root = Path(settings.evidence_root)
    original_paths = {path.resolve() for path in evidence_root.rglob("*")} if evidence_root.exists() else set()
    _clean_database()
    _seed_baseline_job()
    yield
    _clean_database()
    if evidence_root.exists():
        new_paths = sorted(
            (path for path in evidence_root.rglob("*") if path.resolve() not in original_paths),
            key=lambda path: len(path.parts), reverse=True,
        )
        for path in new_paths:
            if path.is_file() or path.is_symlink():
                path.unlink(missing_ok=True)
            elif path.is_dir():
                try:
                    path.rmdir()
                except OSError:
                    pass
