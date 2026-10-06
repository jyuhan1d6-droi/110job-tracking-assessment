import json
import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.collectors.base import CapturedResponse, CollectionRequestError, NormalizedJob, tracked_content_hash
from app.collectors.careers_360 import Careers360Collector, parse_detail as parse_360_detail
from app.collectors.shixiseng import parse_detail as parse_shixiseng_detail
from app.core.config import settings
from app.db.session import SessionLocal
from app.main import app
from app.models.collection import CollectionArtifact, CollectionRun
from app.models.job import Job, JobChangeSet
from app.models.source import Source
from app.models.user import User
from app.services.collection import _ingest_job, collect_360_careers


def _run_artifacts(db, source, user, marker: str, *, valid: int, new: int = 0, unchanged: int = 0):
    run = CollectionRun(
        source_id=source.id, triggered_by_user_id=user.id, mode="live", status="success",
        fetched_count=valid, valid_count=valid, new_count=new, changed_count=0,
        unchanged_count=unchanged, failed_count=0, request_metadata={"acceptance": marker},
    )
    db.add(run)
    db.flush()
    artifacts = []
    for kind in ("list_json", "detail_json"):
        artifact = CollectionArtifact(
            run_id=run.id, artifact_type=kind, relative_path=f"acceptance/{run.id}/{kind}.json",
            request_url="https://example.test", byte_size=2, sha256=(marker[0] * 64),
            request_headers={}, response_headers={}, artifact_metadata={},
        )
        db.add(artifact)
        artifacts.append(artifact)
    db.flush()
    return run, artifacts


def _normalized(identity: str, title: str, requirements: str = "Python 后端与数据库"):
    return NormalizedJob(
        external_identity=identity, title=title, company="测试公司", city="北京",
        requirements=requirements, detail_url=f"https://example.test/{identity}",
        content_hash=tracked_content_hash(requirements, None, None),
    )


def test_job_01_committed_real_evidence_has_two_sources_and_at_least_ten_valid_jobs_each():
    root = Path(os.environ["SOURCE_EVIDENCE_ROOT"])
    careers = root / "raw/360-careers/84f5e79e-f965-4d20-adbe-2db8aad456c6"
    shixiseng = root / "raw/shixiseng/fb11537c-bed7-422b-bf91-059b3b287c0b"
    career_jobs = [parse_360_detail(json.loads(path.read_bytes())) for path in careers.glob("detail-*.json")]
    internship_jobs = []
    for path in shixiseng.glob("detail-*.html"):
        job_id = path.stem.removeprefix("detail-")
        internship_jobs.append(parse_shixiseng_detail(path.read_bytes(), job_id))
    assert len(career_jobs) >= 10 and len(internship_jobs) >= 10
    assert len({job.external_identity for job in career_jobs}) == len(career_jobs)
    assert len({job.external_identity for job in internship_jobs}) == len(internship_jobs)
    assert all(job.detail_url.startswith("https://") for job in career_jobs + internship_jobs)


def test_job_02_and_03_repeat_is_unchanged_while_same_title_different_identity_stays_distinct():
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == "maintainer"))
        source = db.scalar(select(Source).where(Source.code == "360-careers"))
        baseline = db.scalar(select(Job).where(Job.external_identity == "360-careers:test-baseline"))
        repeat, repeat_artifacts = _run_artifacts(db, source, user, "a", valid=1, unchanged=1)
        same = _normalized(baseline.external_identity, baseline.title)
        assert _ingest_job(
            db, run=repeat, source=source, normalized=same,
            list_artifact=repeat_artifacts[0], detail_artifact=repeat_artifacts[1],
            observed_at=datetime.now(timezone.utc),
        ) == "unchanged"
        assert db.scalar(select(JobChangeSet).where(JobChangeSet.run_id == repeat.id)) is None

        distinct, distinct_artifacts = _run_artifacts(db, source, user, "b", valid=2, new=2)
        for identity in ("360-careers:same-title-1", "360-careers:same-title-2"):
            assert _ingest_job(
                db, run=distinct, source=source, normalized=_normalized(identity, "完全同名岗位"),
                list_artifact=distinct_artifacts[0], detail_artifact=distinct_artifacts[1],
                observed_at=datetime.now(timezone.utc),
            ) == "new"
        assert len(list(db.scalars(select(Job).where(Job.title == "完全同名岗位")))) == 2


def test_job_07_source_failure_preserves_jobs_and_does_not_block_other_source(monkeypatch):
    monkeypatch.setattr(Careers360Collector, "fetch_list", lambda _self: (_ for _ in ()).throw(CollectionRequestError("受控超时")))
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == "maintainer"))
        original_id = db.scalar(select(Job.id).where(Job.external_identity == "360-careers:test-baseline"))
        failed = collect_360_careers(db, triggered_by_user_id=user.id)
        assert failed.status == "failed" and failed.failed_count == 0
        assert db.get(Job, original_id) is not None

        def response(payload: dict):
            body = json.dumps(payload).encode()
            return CapturedResponse(
                body=body, request_url="https://hr.360.cn/test-controlled", status_code=200,
                content_type="application/json", response_headers={}, retry_count=0,
                captured_at=datetime.now(timezone.utc),
            )

        monkeypatch.setattr(Careers360Collector, "fetch_list", lambda _self: response({"code": 0, "data": []}))
        empty = collect_360_careers(db, triggered_by_user_id=user.id)
        assert empty.status == "failed" and empty.error_code == "NO_VALID_JOBS"
        assert db.get(Job, original_id) is not None

        monkeypatch.setattr(Careers360Collector, "fetch_list", lambda _self: response({"code": 0, "data": "invalid"}))
        invalid = collect_360_careers(db, triggered_by_user_id=user.id)
        assert invalid.status == "failed" and invalid.error_code == "SOURCE_REQUEST_FAILED"
        assert db.get(Job, original_id) is not None

        other = db.scalar(select(Source).where(Source.code == "shixiseng"))
        success, artifacts = _run_artifacts(db, other, user, "c", valid=1, new=1)
        assert _ingest_job(
            db, run=success, source=other,
            normalized=_normalized("shixiseng:isolated-success", "独立成功岗位"),
            list_artifact=artifacts[0], detail_artifact=artifacts[1], observed_at=datetime.now(timezone.utc),
        ) == "new"
        assert db.scalar(select(Job.id).where(Job.external_identity == "shixiseng:isolated-success"))


def test_job_09_saved_filter_reuse_recomputes_against_refreshed_jobs_and_survives_login():
    with TestClient(app) as client:
        assert client.post("/api/auth/login", json={"username": "jobseeker1", "password": settings.seed_jobseeker1_password}).status_code == 200
        saved = client.post("/api/saved-filters", json={"name": "北京 Python", "keyword": "Python", "city": "北京"})
        assert saved.status_code == 201
        filter_id = saved.json()["id"]
        before = client.get("/api/jobs", params={"keyword": "Python", "city": "北京"}).json()
        assert before["total"] == 1

        with SessionLocal() as db:
            user = db.scalar(select(User).where(User.username == "maintainer"))
            source = db.scalar(select(Source).where(Source.code == "360-careers"))
            baseline = db.scalar(select(Job).where(Job.external_identity == "360-careers:test-baseline"))
            baseline.requirements = "不再匹配原筛选条件"
            baseline.current_content_hash = tracked_content_hash(baseline.requirements, None, None)
            run, artifacts = _run_artifacts(db, source, user, "d", valid=1, new=1)
            _ingest_job(
                db, run=run, source=source,
                normalized=_normalized("360-careers:filter-refresh", "Python 新岗位"),
                list_artifact=artifacts[0], detail_artifact=artifacts[1], observed_at=datetime.now(timezone.utc),
            )
            db.commit()

        after = client.get("/api/jobs", params={"keyword": "Python", "city": "北京"}).json()
        assert after["total"] == 1
        assert after["items"][0]["title"] == "Python 新岗位"
        client.post("/api/auth/logout")
        assert client.post("/api/auth/login", json={"username": "jobseeker1", "password": settings.seed_jobseeker1_password}).status_code == 200
        assert any(item["id"] == filter_id for item in client.get("/api/saved-filters").json())
