from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.core.config import settings
from app.core.security import hash_session_token
from app.db.session import SessionLocal
from app.initial_data import seed_users
from app.main import app
from app.models.user import AuthSession, User


def test_seed_users_is_idempotent_and_preserves_passwords():
    assert seed_users() == 0
    with SessionLocal() as db:
        before = {
            user.username: user.password_hash
            for user in db.scalars(select(User).where(User.username.in_(["jobseeker1", "jobseeker2", "maintainer"])))
        }
    assert seed_users() == 0
    with SessionLocal() as db:
        after = {
            user.username: user.password_hash
            for user in db.scalars(select(User).where(User.username.in_(before)))
        }
    assert before == after
    assert len(after) == 3


def test_three_seed_accounts_login_and_role_boundaries():
    accounts = (
        ("jobseeker1", settings.seed_jobseeker1_password, "job_seeker"),
        ("jobseeker2", settings.seed_jobseeker2_password, "job_seeker"),
        ("maintainer", settings.seed_maintainer_password, "maintainer"),
    )
    for username, password, expected_role in accounts:
        with TestClient(app) as client:
            login = client.post("/api/auth/login", json={"username": username, "password": password})
            assert login.status_code == 200
            assert login.json()["role"] == expected_role
            assert settings.session_cookie_name in login.cookies
            assert login.cookies[settings.session_cookie_name]
            set_cookie = login.headers["set-cookie"].lower()
            assert "httponly" in set_cookie
            assert "samesite=lax" in set_cookie

            me = client.get("/api/auth/me")
            assert me.status_code == 200
            assert me.json()["username"] == username

            access = client.get("/api/auth/maintainer/access-check")
            assert access.status_code == (200 if expected_role == "maintainer" else 403)
            if expected_role == "job_seeker":
                assert client.post("/api/collection/sources/360-careers/runs").status_code == 403

            assert client.post("/api/auth/logout").status_code == 204
            assert client.get("/api/auth/me").status_code == 401
            assert client.post("/api/auth/logout").status_code == 204


def test_invalid_login_and_forged_session_are_rejected():
    with TestClient(app) as client:
        wrong_user = client.post("/api/auth/login", json={"username": "missing", "password": "wrong"})
        wrong_password = client.post("/api/auth/login", json={"username": "jobseeker1", "password": "wrong"})
        assert wrong_user.status_code == wrong_password.status_code == 401
        assert wrong_user.json() == wrong_password.json()

        client.cookies.set(settings.session_cookie_name, "forged-session")
        assert client.get("/api/auth/me").status_code == 401


def test_logout_marks_session_revoked():
    with TestClient(app) as client:
        assert client.post(
            "/api/auth/login",
            json={"username": "maintainer", "password": settings.seed_maintainer_password},
        ).status_code == 200
        token = client.cookies[settings.session_cookie_name]
        assert client.post("/api/auth/logout").status_code == 204

    with SessionLocal() as db:
        auth_session = db.get(AuthSession, hash_session_token(token))
        assert auth_session is not None
        assert auth_session.revoked_at is not None
        assert db.scalar(select(func.count()).select_from(AuthSession)) >= 1


def test_expired_session_and_disabled_user_are_rejected():
    expired_token = "expired-test-session"
    now = datetime.now(timezone.utc)
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == "jobseeker1"))
        assert user is not None
        db.merge(
            AuthSession(
                id=hash_session_token(expired_token),
                user_id=user.id,
                created_at=now - timedelta(hours=2),
                expires_at=now - timedelta(hours=1),
                last_seen_at=now - timedelta(hours=2),
            )
        )
        db.commit()

    with TestClient(app) as client:
        client.cookies.set(settings.session_cookie_name, expired_token)
        assert client.get("/api/auth/me").status_code == 401

        assert client.post(
            "/api/auth/login",
            json={"username": "jobseeker1", "password": settings.seed_jobseeker1_password},
        ).status_code == 200
        with SessionLocal() as db:
            user = db.scalar(select(User).where(User.username == "jobseeker1"))
            user.is_active = False
            db.commit()
        try:
            assert client.get("/api/auth/me").status_code == 401
        finally:
            with SessionLocal() as db:
                user = db.scalar(select(User).where(User.username == "jobseeker1"))
                user.is_active = True
                db.commit()
