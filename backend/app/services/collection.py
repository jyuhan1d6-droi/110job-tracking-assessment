import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.collectors.base import (
    CapturedResponse,
    CollectionRequestError,
    EvidenceHttpClient,
    ExplicitClosureDetected,
    NormalizedJob,
    tracked_content_hash,
    write_evidence,
)
from app.collectors.careers_360 import Careers360Collector, parse_detail, parse_list
from app.core.config import settings
from app.models.collection import CollectionArtifact, CollectionRun
from app.models.job import Job, JobChangeSet, JobFieldChange, JobObservation
from app.models.source import Source
from app.services.watch_events import create_watch_events_for_change_set


class CollectionConflictError(RuntimeError):
    pass


def _save_artifact(
    db: Session,
    *,
    run: CollectionRun,
    response: CapturedResponse,
    filename: str,
    artifact_type: str,
    source_code: str = "360-careers",
    request_headers: dict[str, str] | None = None,
) -> CollectionArtifact:
    relative = Path("raw") / source_code / str(run.id) / filename
    write_evidence(Path(settings.evidence_root), relative, response.body)
    artifact = CollectionArtifact(
        run_id=run.id,
        artifact_type=artifact_type,
        relative_path=relative.as_posix(),
        request_url=response.request_url,
        content_type=response.content_type,
        http_status=response.status_code,
        byte_size=len(response.body),
        sha256=response.sha256,
        captured_at=response.captured_at,
        request_headers=request_headers or {
            "accept": "application/json",
            "x-requested-with": "XMLHttpRequest",
            "user-agent": Careers360Collector.headers["User-Agent"],
        },
        response_headers=response.response_headers,
        artifact_metadata={"retry_count": response.retry_count},
    )
    db.add(artifact)
    db.flush()
    return artifact


def _change_hash(job: Job, normalized: NormalizedJob) -> str:
    value = json.dumps(
        {
            "job_id": str(job.id),
            "requirements": normalized.requirements,
            "deadline": normalized.deadline_raw,
            "status": normalized.recruitment_status,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def compare_tracked_fields(job: Job, normalized: NormalizedJob) -> list[tuple[str, str | None, str | None]]:
    pairs = (
        ("requirements", job.requirements, normalized.requirements),
        ("deadline", job.deadline_raw, normalized.deadline_raw),
        ("recruitment_status", job.recruitment_status, normalized.recruitment_status),
    )
    return [(field, before, after) for field, before, after in pairs if before != after]


def normalized_explicit_closure(job: Job, evidence_text: str) -> NormalizedJob:
    evidence = evidence_text.strip()
    if not evidence:
        raise ValueError("明确关闭必须包含来源证据文本")
    return NormalizedJob(
        external_identity=job.external_identity,
        title=job.title,
        company=job.company,
        city=job.city,
        requirements=job.requirements,
        deadline_raw=job.deadline_raw,
        deadline_at=job.deadline_at,
        recruitment_status="closed",
        explicit_closed=True,
        closed_evidence_text=evidence,
        detail_url=job.detail_url,
        content_hash=tracked_content_hash(job.requirements, job.deadline_raw, "closed"),
    )


def _ingest_job(
    db: Session,
    *,
    run: CollectionRun,
    source: Source,
    normalized: NormalizedJob,
    list_artifact: CollectionArtifact,
    detail_artifact: CollectionArtifact,
    observed_at: datetime,
    origin: str = "live",
    existing_only: bool = False,
) -> str:
    if origin not in {"live", "replay"}:
        raise ValueError("不支持的入库来源")
    if normalized.recruitment_status == "closed" and (
        not normalized.explicit_closed or not normalized.closed_evidence_text
    ):
        raise ValueError("只有带明确来源证据的岗位才能记录为关闭")
    if normalized.explicit_closed and normalized.recruitment_status != "closed":
        raise ValueError("explicit_closed 只能与 closed 状态同时使用")
    job = db.scalar(
        select(Job).where(
            Job.source_id == source.id,
            Job.external_identity == normalized.external_identity,
        )
    )
    changes = compare_tracked_fields(job, normalized) if job else []
    if job is None:
        if existing_only:
            raise ValueError("回放只能更新已经真实采集的岗位")
        job = Job(
            source_id=source.id,
            external_identity=normalized.external_identity,
            title=normalized.title,
            company=normalized.company,
            city=normalized.city,
            requirements=normalized.requirements,
            deadline_raw=normalized.deadline_raw,
            deadline_at=normalized.deadline_at,
            deadline_provided=normalized.deadline_raw is not None,
            recruitment_status=normalized.recruitment_status,
            status_provided=normalized.recruitment_status is not None,
            detail_url=normalized.detail_url,
            first_seen_at=observed_at,
            last_seen_at=observed_at,
            last_live_seen_at=observed_at if origin == "live" else None,
            current_content_hash=normalized.content_hash,
            created_by_run_id=run.id,
            updated_by_run_id=run.id,
            is_visible=True,
        )
        db.add(job)
        db.flush()
        result = "new"
    else:
        result = "changed" if changes else "unchanged"
        if origin == "live":
            job.title = normalized.title
            job.company = normalized.company
            job.city = normalized.city
        job.requirements = normalized.requirements
        job.deadline_raw = normalized.deadline_raw
        job.deadline_at = normalized.deadline_at
        job.deadline_provided = normalized.deadline_raw is not None
        job.recruitment_status = normalized.recruitment_status
        job.status_provided = normalized.recruitment_status is not None
        if origin == "live":
            job.detail_url = normalized.detail_url
        job.last_seen_at = observed_at
        if origin == "live":
            job.last_live_seen_at = observed_at
        else:
            job.last_replay_seen_at = observed_at
        job.current_content_hash = normalized.content_hash
        job.updated_by_run_id = run.id
        if result == "changed":
            job.last_changed_at = observed_at

    observation = JobObservation(
        run_id=run.id,
        job_id=job.id,
        external_identity=normalized.external_identity,
        title=normalized.title,
        company=normalized.company,
        city=normalized.city,
        requirements=normalized.requirements,
        deadline_raw=normalized.deadline_raw,
        deadline_at=normalized.deadline_at,
        deadline_provided=normalized.deadline_raw is not None,
        recruitment_status=normalized.recruitment_status,
        status_provided=normalized.recruitment_status is not None,
        detail_url=normalized.detail_url,
        content_hash=normalized.content_hash,
        list_artifact_id=list_artifact.id,
        detail_artifact_id=detail_artifact.id,
        explicit_closed=normalized.explicit_closed,
        closed_evidence_text=normalized.closed_evidence_text,
        observed_at=observed_at,
    )
    db.add(observation)
    db.flush()

    if result == "changed":
        if not changes:
            raise RuntimeError("不能为没有实际字段变化的岗位创建 change set")
        change_set = JobChangeSet(
            job_id=job.id,
            run_id=run.id,
            observation_id=observation.id,
            change_hash=_change_hash(job, normalized),
            origin=origin,
            detected_at=observed_at,
        )
        db.add(change_set)
        db.flush()
        for field_name, before_text, after_text in changes:
            db.add(
                JobFieldChange(
                    change_set_id=change_set.id,
                    field_name=field_name,
                    before_text=before_text,
                    after_text=after_text,
                )
            )
        db.flush()
        create_watch_events_for_change_set(db, change_set)
    return result


def collect_360_careers(
    db: Session, *, triggered_by_user_id: uuid.UUID, existing_run: CollectionRun | None = None
) -> CollectionRun:
    source = db.scalar(select(Source).where(Source.code == "360-careers", Source.enabled.is_(True)))
    if source is None:
        raise ValueError("360 招聘来源未初始化或已禁用")
    if existing_run is None:
        run = CollectionRun(
            source_id=source.id, triggered_by_user_id=triggered_by_user_id, mode="live", status="running",
            request_metadata={"collector": "360_careers", "list_pages": 0, "request_count": 0, "retry_count": 0},
        )
        db.add(run)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise CollectionConflictError("360 招聘已有正在执行的采集") from exc
        db.refresh(run)
    else:
        run = existing_run
        if run.source_id != source.id or run.mode != "live" or run.status != "pending":
            raise ValueError("预创建采集运行状态无效")
        run.status = "running"
        run.request_metadata = {"collector": "360_careers", "list_pages": 0, "request_count": 0, "retry_count": 0}
        db.commit()

    client = EvidenceHttpClient(
        timeout_seconds=source.timeout_seconds,
        max_retries=source.max_retries,
        interval_ms=source.request_interval_ms,
    )
    collector = Careers360Collector(client)
    errors: list[str] = []
    try:
        list_response = collector.fetch_list()
        list_artifact = _save_artifact(
            db, run=run, response=list_response, filename="list-page-001.json", artifact_type="list_json"
        )
        listings = parse_list(list_response.json())
        run.fetched_count = len(listings)

        seen_ids: set[str] = set()
        for listing in listings:
            job_id = str(listing.get("id") or "").strip()
            if not job_id or job_id in seen_ids:
                run.failed_count += 1
                errors.append("列表含空或重复岗位 ID")
                continue
            seen_ids.add(job_id)
            try:
                detail_response = collector.fetch_detail(job_id)
                detail_artifact = _save_artifact(
                    db,
                    run=run,
                    response=detail_response,
                    filename=f"detail-{job_id}.json",
                    artifact_type="detail_json",
                )
                try:
                    normalized = parse_detail(detail_response.json())
                except ExplicitClosureDetected as exc:
                    existing = db.scalar(
                        select(Job).where(
                            Job.source_id == source.id,
                            Job.external_identity == f"360-careers:{job_id}",
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
        elif run.failed_count:
            run.status = "partial"
            run.error_code = "PARTIAL_JOB_FAILURE"
        else:
            run.status = "success"
        run.error_message = "\n".join(errors)[:4000] or None
    except (CollectionRequestError, ValueError, json.JSONDecodeError) as exc:
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
            "collector": "360_careers",
            "list_pages": 1 if run.fetched_count else 0,
            "request_count": client.request_count,
            "retry_count": client.retry_count,
        }
        db.commit()
        db.refresh(run)
    return run
