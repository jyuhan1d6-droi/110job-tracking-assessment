import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.core.config import settings
from app.db.session import SessionLocal
from app.main import app
from app.models.collection import CollectionRun
from app.models.source import Source
from app.models.user import User
from app.services.collection import CollectionConflictError
from app.services.collection_admin import create_live_run, mark_scheduling_failed, recover_interrupted_live_runs


def test_collection_admin_endpoints_require_maintainer_and_expose_history():
    with TestClient(app) as ordinary:
        assert ordinary.post("/api/auth/login", json={
            "username": "jobseeker1", "password": settings.seed_jobseeker1_password,
        }).status_code == 200
        assert ordinary.get("/api/collection/sources").status_code == 403
        assert ordinary.get("/api/collection/runs").status_code == 403
        assert ordinary.get(f"/api/collection/runs/{uuid.uuid4()}/artifacts").status_code == 403

    with TestClient(app) as maintainer:
        assert maintainer.post("/api/auth/login", json={
            "username": "maintainer", "password": settings.seed_maintainer_password,
        }).status_code == 200
        sources = maintainer.get("/api/collection/sources")
        assert sources.status_code == 200
        assert {item["code"] for item in sources.json()} == {"360-careers", "shixiseng"}
        runs = maintainer.get("/api/collection/runs", params={"mode": "live"})
        assert runs.status_code == 200
        assert "http_status" not in runs.text


def test_active_run_unique_constraint_is_the_conflict_backstop():
    run_id = None
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == "maintainer"))
        source = db.scalar(select(Source).where(Source.code == "360-careers"))
        try:
            run = create_live_run(db, source.code, user.id)
            run_id = run.id
            with pytest.raises(CollectionConflictError):
                create_live_run(db, source.code, user.id)
            mark_scheduling_failed(db, run.id, "test scheduling failure")
            db.refresh(run)
            assert run.status == "failed"
            assert run.error_code == "TASK_SCHEDULING_FAILED"
        finally:
            if run_id:
                db.execute(delete(CollectionRun).where(CollectionRun.id == run_id))
                db.commit()


def test_startup_recovery_only_marks_live_active_runs_failed():
    created = []
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == "maintainer"))
        sources = list(db.scalars(select(Source).order_by(Source.code)))
        live = CollectionRun(source_id=sources[0].id, triggered_by_user_id=user.id, mode="live", status="pending", request_metadata={})
        replay = CollectionRun(source_id=sources[1].id, triggered_by_user_id=user.id, mode="replay", status="pending", request_metadata={})
        db.add_all([live, replay])
        db.commit()
        created = [live.id, replay.id]
        try:
            assert recover_interrupted_live_runs() == 1
            db.expire_all()
            assert db.get(CollectionRun, live.id).status == "failed"
            assert db.get(CollectionRun, live.id).error_code == "PROCESS_INTERRUPTED"
            assert db.get(CollectionRun, replay.id).status == "pending"
        finally:
            db.execute(delete(CollectionRun).where(CollectionRun.id.in_(created)))
            db.commit()
