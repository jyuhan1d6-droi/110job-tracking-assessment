import uuid
import shutil
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.core.config import settings
from app.db.session import SessionLocal
from app.main import app
from app.models.collection import CollectionArtifact, CollectionRun
from app.services.replay import _safe_path, list_replay_scenarios


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
