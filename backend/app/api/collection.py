import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.api.auth import require_maintainer
from app.db.session import get_db
from app.models.collection import CollectionRun
from app.models.user import User
from app.services.collection import CollectionConflictError, collect_360_careers

router = APIRouter(prefix="/collection", tags=["collection"])


class RunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    started_at: datetime
    finished_at: datetime | None
    fetched_count: int
    valid_count: int
    new_count: int
    changed_count: int
    unchanged_count: int
    failed_count: int
    error_code: str | None
    error_message: str | None
    request_metadata: dict


@router.post("/sources/360-careers/runs", response_model=RunResponse)
def run_360_collection(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_maintainer)],
) -> CollectionRun:
    try:
        return collect_360_careers(db, triggered_by_user_id=user.id)
    except CollectionConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/runs/{run_id}", response_model=RunResponse)
def get_run(
    run_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    _user: Annotated[User, Depends(require_maintainer)],
) -> CollectionRun:
    run = db.get(CollectionRun, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="采集运行不存在")
    return run
