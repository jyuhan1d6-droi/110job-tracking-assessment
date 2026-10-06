import hashlib
import math
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.collection import CollectionArtifact, CollectionRun
from app.models.source import Source
from app.models.user import User
from app.schemas.collection import (
    ArtifactListResponse, ArtifactResponse, RunListResponse, RunSummary, SourceStatus,
)
from app.services.collection import CollectionConflictError, collect_360_careers
from app.services.collection_shixiseng import collect_shixiseng


def _summary(db: Session, run: CollectionRun, source: Source | None = None, user: User | None = None) -> RunSummary:
    source = source or db.get(Source, run.source_id)
    user = user or db.get(User, run.triggered_by_user_id)
    artifact_count = db.scalar(
        select(func.count()).select_from(CollectionArtifact).where(CollectionArtifact.run_id == run.id)
    ) or 0
    return RunSummary(
        id=run.id, source_code=source.code, source_name=source.name,
        triggered_by=user.display_name, status=run.status, mode=run.mode,
        started_at=run.started_at, finished_at=run.finished_at,
        fetched_count=run.fetched_count, valid_count=run.valid_count,
        new_count=run.new_count, changed_count=run.changed_count,
        unchanged_count=run.unchanged_count, failed_count=run.failed_count,
        error_code=run.error_code, error_message=run.error_message,
        request_metadata=run.request_metadata, artifact_count=artifact_count,
    )


def create_live_run(db: Session, source_code: str, user_id: uuid.UUID) -> CollectionRun:
    source = db.scalar(select(Source).where(Source.code == source_code, Source.enabled.is_(True)))
    if source is None or source.collector_key not in {"360_careers", "shixiseng"}:
        raise LookupError("采集来源不存在、已禁用或没有可用采集器")
    run = CollectionRun(
        source_id=source.id, triggered_by_user_id=user_id, mode="live", status="pending",
        request_metadata={"collector": source.collector_key, "scheduled": True},
    )
    db.add(run)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        constraint = getattr(getattr(exc, "orig", None), "diag", None)
        if getattr(constraint, "constraint_name", None) == "uq_collection_runs_active_source":
            raise CollectionConflictError(f"{source.name} 已有正在执行的采集") from exc
        raise
    db.refresh(run)
    return run


def mark_scheduling_failed(db: Session, run_id: uuid.UUID, message: str) -> None:
    run = db.get(CollectionRun, run_id)
    if run and run.mode == "live" and run.status == "pending":
        run.status = "failed"
        run.finished_at = datetime.now(timezone.utc)
        run.error_code = "TASK_SCHEDULING_FAILED"
        run.error_message = message[:4000]
        db.commit()


def execute_live_run(run_id: uuid.UUID) -> None:
    with SessionLocal() as db:
        run = db.get(CollectionRun, run_id)
        if run is None or run.mode != "live" or run.status != "pending":
            return
        source = db.get(Source, run.source_id)
        try:
            if source.collector_key == "360_careers":
                collect_360_careers(db, triggered_by_user_id=run.triggered_by_user_id, existing_run=run)
            elif source.collector_key == "shixiseng":
                collect_shixiseng(db, triggered_by_user_id=run.triggered_by_user_id, existing_run=run)
            else:
                raise ValueError("来源没有可用采集器")
        except Exception as exc:
            db.rollback()
            run = db.get(CollectionRun, run_id)
            if run and run.status in {"pending", "running"}:
                run.status = "failed"
                run.finished_at = datetime.now(timezone.utc)
                run.error_code = "BACKGROUND_EXECUTION_FAILED"
                run.error_message = str(exc)[:4000]
                db.commit()


def recover_interrupted_live_runs() -> int:
    with SessionLocal() as db:
        runs = list(db.scalars(select(CollectionRun).where(
            CollectionRun.mode == "live", CollectionRun.status.in_(("pending", "running"))
        )))
        now = datetime.now(timezone.utc)
        for run in runs:
            run.status = "failed"
            run.finished_at = now
            run.error_code = "PROCESS_INTERRUPTED"
            run.error_message = "后端进程重启，未完成的真实采集已终止"
        db.commit()
        return len(runs)


def list_sources(db: Session) -> list[SourceStatus]:
    result = []
    for source in db.scalars(select(Source).order_by(Source.name)):
        active = db.scalar(select(CollectionRun).where(
            CollectionRun.source_id == source.id, CollectionRun.mode == "live",
            CollectionRun.status.in_(("pending", "running")),
        ).order_by(CollectionRun.started_at.desc()))
        latest = db.scalar(select(CollectionRun).where(
            CollectionRun.source_id == source.id, CollectionRun.mode == "live",
            CollectionRun.status.notin_(("pending", "running")),
        ).order_by(CollectionRun.started_at.desc()))
        latest_success = db.scalar(select(func.max(CollectionRun.finished_at)).where(
            CollectionRun.source_id == source.id, CollectionRun.mode == "live",
            CollectionRun.status.in_(("success", "partial")),
        ))
        result.append(SourceStatus(
            code=source.code, name=source.name, source_type=source.source_type,
            entry_url=source.entry_url, official_evidence_url=source.official_evidence_url,
            enabled=source.enabled, request_interval_ms=source.request_interval_ms,
            timeout_seconds=source.timeout_seconds, max_retries=source.max_retries,
            active_run=_summary(db, active, source) if active else None,
            latest_run=_summary(db, latest, source) if latest else None,
            latest_success_at=latest_success,
        ))
    return result


def list_runs(db: Session, *, source_code: str | None, status: str | None, mode: str, page: int, page_size: int) -> RunListResponse:
    conditions = [CollectionRun.mode == mode]
    if source_code:
        conditions.append(Source.code == source_code)
    if status:
        conditions.append(CollectionRun.status == status)
    base = select(CollectionRun, Source, User).join(Source).join(User, User.id == CollectionRun.triggered_by_user_id).where(*conditions)
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = db.execute(base.order_by(CollectionRun.started_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return RunListResponse(
        items=[_summary(db, run, source, user) for run, source, user in rows],
        page=page, page_size=page_size, total=total,
        total_pages=math.ceil(total / page_size) if total else 0,
    )


def get_run_summary(db: Session, run_id: uuid.UUID) -> RunSummary | None:
    run = db.get(CollectionRun, run_id)
    return _summary(db, run) if run else None


def list_artifacts(db: Session, run_id: uuid.UUID, page: int, page_size: int) -> ArtifactListResponse | None:
    if db.get(CollectionRun, run_id) is None:
        return None
    total = db.scalar(select(func.count()).select_from(CollectionArtifact).where(CollectionArtifact.run_id == run_id)) or 0
    items = list(db.scalars(select(CollectionArtifact).where(CollectionArtifact.run_id == run_id)
        .order_by(CollectionArtifact.captured_at, CollectionArtifact.id)
        .offset((page - 1) * page_size).limit(page_size)))
    return ArtifactListResponse(
        items=[ArtifactResponse.model_validate(item, from_attributes=True) for item in items],
        page=page, page_size=page_size, total=total,
        total_pages=math.ceil(total / page_size) if total else 0,
    )


def verified_artifact_path(artifact: CollectionArtifact) -> Path:
    root = Path(settings.evidence_root).resolve()
    path = (root / artifact.relative_path).resolve()
    if root != path and root not in path.parents:
        raise ValueError("证据文件路径超出 evidence 根目录")
    if not path.is_file():
        raise FileNotFoundError("证据文件不存在")
    body_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    if path.stat().st_size != artifact.byte_size or body_hash != artifact.sha256:
        raise ValueError("证据文件大小或 SHA-256 与数据库记录不一致")
    return path
