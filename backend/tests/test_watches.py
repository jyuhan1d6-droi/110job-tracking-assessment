import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select

from app.core.config import settings
from app.db.session import SessionLocal
from app.main import app
from app.models.job import Job
from app.models.user import User
from app.models.watch import JobWatch
from app.services.watches import watch_covers


def _client(username: str, password: str) -> TestClient:
    client = TestClient(app)
    assert client.post("/api/auth/login", json={"username": username, "password": password}).status_code == 200
    return client


def test_watch_requires_login_and_missing_job_is_not_watchable():
    with TestClient(app) as client:
        assert client.get("/api/watches").status_code == 401
        assert client.post(f"/api/jobs/{uuid.uuid4()}/watch").status_code == 401
    with _client("jobseeker1", settings.seed_jobseeker1_password) as client:
        assert client.post(f"/api/jobs/{uuid.uuid4()}/watch").status_code == 404


def test_three_account_watch_isolation_idempotency_and_refollow():
    accounts = (
        ("jobseeker1", settings.seed_jobseeker1_password),
        ("jobseeker2", settings.seed_jobseeker2_password),
        ("maintainer", settings.seed_maintainer_password),
    )
    with SessionLocal() as db:
        job_id = db.scalar(select(Job.id).where(Job.is_visible.is_(True)).limit(1))
        user_ids = list(db.scalars(select(User.id).where(User.username.in_([x[0] for x in accounts]))))
        assert job_id and len(user_ids) == 3
        db.execute(delete(JobWatch).where(JobWatch.job_id == job_id, JobWatch.user_id.in_(user_ids)))
        db.commit()

    clients = [_client(*account) for account in accounts]
    created_ids: set[uuid.UUID] = set()
    try:
        first_ids = []
        for client in clients:
            first = client.post(f"/api/jobs/{job_id}/watch")
            assert first.status_code == 200
            first_ids.append(first.json()["id"])
            created_ids.add(uuid.UUID(first.json()["id"]))
            repeated = client.post(f"/api/jobs/{job_id}/watch")
            assert repeated.status_code == 200
            assert repeated.json()["id"] == first.json()["id"]
            listing = client.get("/api/watches").json()
            assert sum(item["job"]["id"] == str(job_id) for item in listing["items"]) == 1

        assert len(set(first_ids)) == 3
        assert clients[0].delete(f"/api/jobs/{job_id}/watch").status_code == 204
        assert clients[0].delete(f"/api/jobs/{job_id}/watch").status_code == 204
        assert all(item["job"]["id"] != str(job_id) for item in clients[0].get("/api/watches").json()["items"])
        assert any(item["job"]["id"] == str(job_id) for item in clients[1].get("/api/watches").json()["items"])

        second = clients[0].post(f"/api/jobs/{job_id}/watch")
        assert second.status_code == 200
        assert second.json()["id"] != first_ids[0]
        created_ids.add(uuid.UUID(second.json()["id"]))

        detail = clients[0].get(f"/api/jobs/{job_id}").json()
        assert detail["is_watched"] is True
        clients[0].delete(f"/api/jobs/{job_id}/watch")
        assert clients[0].get(f"/api/jobs/{job_id}").json()["is_watched"] is False
    finally:
        with SessionLocal() as db:
            db.execute(delete(JobWatch).where(JobWatch.id.in_(created_ids)))
            db.commit()
        for client in clients:
            client.close()


def test_watch_time_boundary_is_left_closed_right_open():
    start = datetime(2026, 10, 6, 1, 0, tzinfo=timezone.utc)
    end = start + timedelta(hours=1)
    watch = JobWatch(user_id=uuid.uuid4(), job_id=uuid.uuid4(), watched_at=start, unwatched_at=end)
    assert watch_covers(watch, start - timedelta(microseconds=1)) is False
    assert watch_covers(watch, start) is True
    assert watch_covers(watch, end - timedelta(microseconds=1)) is True
    assert watch_covers(watch, end) is False
