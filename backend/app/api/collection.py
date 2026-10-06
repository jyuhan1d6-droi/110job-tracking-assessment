import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.auth import require_maintainer
from app.db.session import get_db
from app.models.collection import CollectionArtifact
from app.models.user import User
from app.schemas.collection import ArtifactListResponse, RunListResponse, RunSummary, SourceStatus
from app.services.collection import CollectionConflictError
from app.services.collection_admin import (
    _summary, create_live_run, execute_live_run, get_run_summary, list_artifacts,
    list_runs, list_sources, mark_scheduling_failed, verified_artifact_path,
)

router = APIRouter(prefix="/collection", tags=["collection"])


@router.get("/sources", response_model=list[SourceStatus])
def sources(db: Annotated[Session, Depends(get_db)], _user: Annotated[User, Depends(require_maintainer)]):
    return list_sources(db)


@router.post("/sources/{source_code}/runs", response_model=RunSummary, status_code=status.HTTP_202_ACCEPTED)
def start_collection(
    source_code: str, background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)], user: Annotated[User, Depends(require_maintainer)],
):
    try:
        run = create_live_run(db, source_code, user.id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CollectionConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    try:
        background_tasks.add_task(execute_live_run, run.id)
    except Exception as exc:
        mark_scheduling_failed(db, run.id, f"后台任务调度失败：{exc}")
        raise HTTPException(status_code=500, detail="后台任务调度失败，运行已标记为失败") from exc
    return _summary(db, run)


@router.get("/runs", response_model=RunListResponse)
def runs(
    db: Annotated[Session, Depends(get_db)], _user: Annotated[User, Depends(require_maintainer)],
    source_code: str | None = None,
    run_status: Literal["pending", "running", "success", "partial", "failed"] | None = Query(None, alias="status"),
    mode: Literal["live", "replay"] = "live", page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    return list_runs(db, source_code=source_code, status=run_status, mode=mode, page=page, page_size=page_size)


@router.get("/runs/{run_id}", response_model=RunSummary)
def run_detail(run_id: uuid.UUID, db: Annotated[Session, Depends(get_db)], _user: Annotated[User, Depends(require_maintainer)]):
    result = get_run_summary(db, run_id)
    if result is None:
        raise HTTPException(status_code=404, detail="采集运行不存在")
    return result


@router.get("/runs/{run_id}/artifacts", response_model=ArtifactListResponse)
def artifacts(
    run_id: uuid.UUID, db: Annotated[Session, Depends(get_db)],
    _user: Annotated[User, Depends(require_maintainer)], page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    result = list_artifacts(db, run_id, page, page_size)
    if result is None:
        raise HTTPException(status_code=404, detail="采集运行不存在")
    return result


@router.get("/artifacts/{artifact_id}/download")
def download_artifact(
    artifact_id: uuid.UUID, db: Annotated[Session, Depends(get_db)],
    _user: Annotated[User, Depends(require_maintainer)],
):
    artifact = db.get(CollectionArtifact, artifact_id)
    if artifact is None:
        raise HTTPException(status_code=404, detail="采集证据不存在")
    try:
        path = verified_artifact_path(artifact)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return FileResponse(path, media_type=artifact.content_type or "application/octet-stream", filename=path.name)
