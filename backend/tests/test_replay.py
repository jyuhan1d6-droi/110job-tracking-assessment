import uuid
import shutil
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.core.config import settings
from app.db.session import SessionLocal
from app.main import app
from app.models.collection import CollectionArtifact, CollectionRun
from app.models.job import Job
from app.schemas.replay import ReplayJob
from app.services.replay import _base_artifact_job, _normalized, _safe_path, list_replay_scenarios


def test_official_replay_manifest_and_hashes_are_valid():
    scenarios = list_replay_scenarios()
    assert {scenario.step_id for scenario in scenarios} == {
        "baseline", "requirements-change", "explicit-close", "source-failure"
    }
    assert all(scenario.valid for scenario in scenarios)
    assert all(scenario.source_code == "shixiseng" for scenario in scenarios)


def test_replay_permissions_and_source_failure_count_rule():
    with TestClient(app) as ordinary:
        assert ordinary.post(
            "/api/auth/login",
            json={"username": "jobseeker1", "password": settings.seed_jobseeker1_password},
        ).status_code == 200
        assert ordinary.get("/api/replay/scenarios").status_code == 403
        assert ordinary.post("/api/replay/scenarios/shixiseng-secretary:source-failure/runs").status_code == 403

    run_id = None
    try:
        with TestClient(app) as maintainer:
            assert maintainer.post(
                "/api/auth/login",
                json={"username": "maintainer", "password": settings.seed_maintainer_password},
            ).status_code == 200
            scenarios = maintainer.get("/api/replay/scenarios")
            assert scenarios.status_code == 200
            response = maintainer.post(
                "/api/replay/scenarios/shixiseng-secretary:source-failure/runs"
            )
            assert response.status_code == 200
            result = response.json()
            run_id = uuid.UUID(result["id"])
            assert result["status"] == "failed"
            assert result["failed_count"] == 0
            assert result["fetched_count"] == result["valid_count"] == 0
    finally:
        if run_id:
            with SessionLocal() as db:
                db.execute(delete(CollectionArtifact).where(CollectionArtifact.run_id == run_id))
                db.execute(delete(CollectionRun).where(CollectionRun.id == run_id))
                db.commit()
            run_evidence = Path(settings.evidence_root) / "replay" / "runs" / str(run_id)
            if run_evidence.is_dir() and (Path(settings.evidence_root) / "replay" / "runs") in run_evidence.parents:
                shutil.rmtree(run_evidence)


def test_replay_rejects_path_traversal():
    try:
        _safe_path("../outside.json", allowed_root=__import__("pathlib").Path("replay/scenarios"))
    except ValueError as exc:
        assert "不安全" in str(exc)
    else:
        raise AssertionError("path traversal should be rejected")


def test_replay_immutable_fields_are_checked_against_base_artifact_and_deadline_is_preserved():
    scenario = next(item for item in list_replay_scenarios() if item.step_id == "baseline")
    base = _base_artifact_job("shixiseng", scenario.provenance_file, "shixiseng:inn_9g4ply6sfzje")
    existing_deadline = datetime(2027, 10, 6, 23, 59, 59, tzinfo=timezone.utc)
    current = Job(
        external_identity=base.external_identity,
        title="当前真实采集可有更新标题",
        company="当前真实采集可有更新公司",
        city="当前真实采集可有更新城市",
        requirements=base.requirements,
        deadline_raw=base.deadline_raw,
        deadline_at=existing_deadline,
        recruitment_status=None,
        detail_url="https://current.example/job",
    )
    replay = ReplayJob(
        identity=base.external_identity, title=base.title, company=base.company, city=base.city,
        requirements=base.requirements, deadline=base.deadline_raw, status=None,
        detailUrl=base.detail_url,
    )
    normalized = _normalized(replay, source_code="shixiseng", current=current, base=base)
    assert normalized.deadline_at == existing_deadline

    changed_title = replay.model_copy(update={"title": "不是 baseArtifact 的标题"})
    try:
        _normalized(changed_title, source_code="shixiseng", current=current, base=base)
    except ValueError as exc:
        assert "title" in str(exc)
    else:
        raise AssertionError("replay immutable fields must match baseArtifact")


def test_replay_deadline_change_uses_shared_normalizer():
    scenario = next(item for item in list_replay_scenarios() if item.step_id == "baseline")
    base = _base_artifact_job("shixiseng", scenario.provenance_file, "shixiseng:inn_9g4ply6sfzje")
    current = Job(
        external_identity=base.external_identity, title=base.title, company=base.company,
        city=base.city, requirements=base.requirements, deadline_raw=base.deadline_raw,
        deadline_at=base.deadline_at, recruitment_status=None, detail_url=base.detail_url,
    )
    replay = ReplayJob(
        identity=base.external_identity, title=base.title, company=base.company, city=base.city,
        requirements=base.requirements, deadline="2028-01-02", status=None,
        detailUrl=base.detail_url,
    )
    normalized = _normalized(replay, source_code="shixiseng", current=current, base=base)
    assert normalized.deadline_at is not None
    assert normalized.deadline_at.year == 2028
    assert normalized.deadline_at.utcoffset().total_seconds() == 8 * 3600
