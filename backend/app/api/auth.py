from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_session_token, new_session_token, verify_password
from app.db.session import get_db
from app.models.user import AuthSession, User

router = APIRouter(prefix="/auth", tags=["authentication"])
DbSession = Annotated[Session, Depends(get_db)]


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    display_name: str
    role: str


def _unauthorized() -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已失效，请重新登录")


def get_current_user(
    db: DbSession,
    session_token: Annotated[str | None, Cookie(alias=settings.session_cookie_name)] = None,
) -> User:
    if not session_token:
        raise _unauthorized()
    now = datetime.now(timezone.utc)
    auth_session = db.get(AuthSession, hash_session_token(session_token))
    if auth_session is None or auth_session.revoked_at is not None or auth_session.expires_at <= now:
        raise _unauthorized()
    user = db.get(User, auth_session.user_id)
    if user is None or not user.is_active:
        raise _unauthorized()
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_maintainer(user: CurrentUser) -> User:
    if user.role != "maintainer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要数据维护账号权限")
    return user


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=settings.session_hours * 60 * 60,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )


@router.post("/login", response_model=UserResponse)
def login(payload: LoginRequest, response: Response, db: DbSession) -> User:
    user = db.scalar(select(User).where(User.username == payload.username))
    if user is None or not user.is_active or not verify_password(user.password_hash, payload.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

    now = datetime.now(timezone.utc)
    token = new_session_token()
    db.add(
        AuthSession(
            id=hash_session_token(token),
            user_id=user.id,
            expires_at=now + timedelta(hours=settings.session_hours),
            last_seen_at=now,
        )
    )
    user.last_login_at = now
    db.commit()
    _set_session_cookie(response, token)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    db: DbSession,
    session_token: Annotated[str | None, Cookie(alias=settings.session_cookie_name)] = None,
) -> None:
    if session_token:
        auth_session = db.get(AuthSession, hash_session_token(session_token))
        if auth_session is not None and auth_session.revoked_at is None:
            auth_session.revoked_at = datetime.now(timezone.utc)
            db.commit()
    response.delete_cookie(settings.session_cookie_name, path="/", secure=settings.session_cookie_secure, samesite="lax")


@router.get("/me", response_model=UserResponse)
def me(user: CurrentUser) -> User:
    return user


@router.get("/maintainer/access-check", response_model=UserResponse)
def maintainer_access(user: Annotated[User, Depends(require_maintainer)]) -> User:
    return user
