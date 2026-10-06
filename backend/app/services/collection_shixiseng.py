import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.collectors.base import CollectionRequestError, EvidenceHttpClient, ExplicitClosureDetected
from app.collectors.shixiseng import ShixisengCollector, has_private_use_characters, parse_detail, parse_list
from app.models.collection import CollectionRun
from app.models.job import Job
from app.models.source import Source
from app.services.collection import (
    CollectionConflictError,
    _ingest_job,
    _save_artifact,
    normalized_explicit_closure,
)

TARGET_VALID_JOBS = 10
MAX_LIST_PAGES = 3


def collect_shixiseng(
    db: Session, *, triggered_by_user_id: uuid.UUID, existing_run: CollectionRun | None = None
) -> CollectionRun:
    source = db.scalar(select(Source).where(Source.code == "shixiseng", Source.enabled.is_(True)))
    if source is None:
        raise ValueError("实习僧来源未初始化或已禁用")
    if existing_run is None:
        run = CollectionRun(
            source_id=source.id, triggered_by_user_id=triggered_by_user_id, mode="live", status="running",
            request_metadata={"collector": "shixiseng", "list_pages": 0, "request_count": 0, "retry_count": 0},
        )
        db.add(run)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise CollectionConflictError("实习僧已有正在执行的采集") from exc
        db.refresh(run)
    else:
        run = existing_run
        if run.source_id != source.id or run.mode != "live" or run.status != "pending":
            raise ValueError("预创建采集运行状态无效")
        run.status = "running"
        run.request_metadata = {"collector": "shixiseng", "list_pages": 0, "request_count": 0, "retry_count": 0}
        db.commit()

    client = EvidenceHttpClient(
        timeout_seconds=source.timeout_seconds,
        max_retries=source.max_retries,
        interval_ms=source.request_interval_ms,
    )
    collector = ShixisengCollector(client)
    errors: list[str] = []
    list_pages = 0
    candidate_count = 0
    try:
        candidates: list[tuple[str, str, object]] = []
        seen_ids: set[str] = set()
        for page in range(1, MAX_LIST_PAGES + 1):
            response = collector.fetch_list(page)
            artifact = _save_artifact(
                db,
                run=run,
                response=response,
                filename=f"list-page-{page:03d}.html",
                artifact_type="list_html",
                source_code="shixiseng",
                request_headers={
                    "accept": ShixisengCollector.headers["Accept"],
                    "user-agent": ShixisengCollector.headers["User-Agent"],
                },
            )
            list_pages += 1
            for job_id, title in parse_list(response.body):
                if job_id in seen_ids:
                    continue
                seen_ids.add(job_id)
                candidates.append((job_id, title, artifact))
        candidate_count = len(candidates)
        run.fetched_count = candidate_count

        for job_id, listed_title, list_artifact in candidates:
            if run.valid_count >= TARGET_VALID_JOBS:
                break
            if has_private_use_characters(listed_title):
                continue
            try:
                detail_response = collector.fetch_detail(job_id)
                detail_artifact = _save_artifact(
                    db,
                    run=run,
                    response=detail_response,
                    filename=f"detail-{job_id}.html",
                    artifact_type="detail_html",
                    source_code="shixiseng",
                    request_headers={
                        "accept": ShixisengCollector.headers["Accept"],
                        "user-agent": ShixisengCollector.headers["User-Agent"],
                    },
                )
                try:
                    normalized = parse_detail(detail_response.body, job_id)
                except ExplicitClosureDetected as exc:
                    existing = db.scalar(
                        select(Job).where(
                            Job.source_id == source.id,
                            Job.external_identity == f"shixiseng:{job_id}",
                        )
                    )
                    if existing is None:
                        raise ValueError("首次观察即关闭且缺少岗位字段，未建立岗位") from exc
                    normalized = normalized_explicit_closure(existing, str(exc))
                result = _ingest_job(
                    db,
                    run=run,
                    source=source,
                    normalized=normalized,
                    list_artifact=list_artifact,
                    detail_artifact=detail_artifact,
                    observed_at=detail_response.captured_at,
                )
                run.valid_count += 1
                if result == "new":
                    run.new_count += 1
                elif result == "changed":
                    run.changed_count += 1
                else:
                    run.unchanged_count += 1
            except (CollectionRequestError, ValueError, json.JSONDecodeError) as exc:
                run.failed_count += 1
                errors.append(f"{job_id}: {exc}")

        if run.valid_count == 0:
            run.status = "failed"
            run.error_code = "NO_VALID_JOBS"
        elif run.valid_count < TARGET_VALID_JOBS or run.failed_count:
            run.status = "partial"
            run.error_code = "PARTIAL_JOB_FAILURE" if run.failed_count else "INSUFFICIENT_VALID_JOBS"
        else:
            run.status = "success"
        run.error_message = "\n".join(errors)[:4000] or None
    except (CollectionRequestError, ValueError) as exc:
        run.status = "failed"
        run.error_code = "SOURCE_REQUEST_FAILED"
        run.error_message = str(exc)[:4000]
    except Exception as exc:
        db.rollback()
        run = db.get(CollectionRun, run.id)
        if run is None:
            raise
        run.status = "failed"
        run.error_code = "COLLECTION_INTERNAL_ERROR"
        run.error_message = str(exc)[:4000]
    finally:
        client.close()
        run.finished_at = datetime.now(timezone.utc)
        run.request_metadata = {
            "collector": "shixiseng",
            "list_pages": list_pages,
            "candidate_count": candidate_count,
            "target_valid_jobs": TARGET_VALID_JOBS,
            "selection_policy": "public_text_without_private_use_font_characters",
            "request_count": client.request_count,
            "retry_count": client.retry_count,
        }
        db.commit()
        db.refresh(run)
    return run
