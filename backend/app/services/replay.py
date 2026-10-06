import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.collectors.base import NormalizedJob, tracked_content_hash, write_evidence
from app.core.config import settings
from app.models.collection import CollectionArtifact, CollectionRun
from app.models.source import Source
from app.schemas.replay import ReplayJob, ReplayScenario, ReplaySnapshot
from app.services.collection import CollectionConflictError, _ingest_job

SCENARIO_ROOT = Path("replay/scenarios")
SCHEMA_PATH = Path("templates/replay.schema.json")


def _safe_path(relative: str, allowed_root: Path) -> Path:
    if Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError("回放文件路径不安全")
    evidence_root = Path(settings.evidence_root).resolve()
    resolved = (evidence_root / relative).resolve()
    allowed = (evidence_root / allowed_root).resolve()
    if resolved != allowed and allowed not in resolved.parents:
        raise ValueError("回放文件超出允许目录")
    return resolved


def _bytes_and_hash(relative: str, allowed_root: Path) -> tuple[bytes, str]:
    path = _safe_path(relative, allowed_root)
    body = path.read_bytes()
    return body, hashlib.sha256(body).hexdigest()


def _load_manifest(path: Path) -> tuple[dict, list[str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    schema = json.loads((Path(settings.evidence_root) / SCHEMA_PATH).read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(payload), key=lambda error: list(error.path))
    return payload, [error.message for error in errors]


def list_replay_scenarios() -> list[ReplayScenario]:
    root = (Path(settings.evidence_root) / SCENARIO_ROOT).resolve()
    scenarios: list[ReplayScenario] = []
    for manifest_path in sorted(root.glob("*/replay.json")):
        try:
            manifest, errors = _load_manifest(manifest_path)
        except (OSError, json.JSONDecodeError) as exc:
            scenarios.append(ReplayScenario(
                id=f"{manifest_path.parent.name}:invalid", step_id="invalid", name="无效回放清单",
                source_code="unknown", kind="invalid", expected="无法读取清单", declared_fields=[],
                provenance_file="", provenance_sha256="", snapshot_file=None, snapshot_sha256=None,
                failure_reason=None, valid=False, validation_error=str(exc),
            ))
            continue
        provenance = manifest.get("provenance", {})
        try:
            _, actual = _bytes_and_hash(provenance.get("snapshotFile", ""), Path("raw"))
            if actual != provenance.get("sha256"):
                errors.append("原始真实快照 SHA-256 不匹配")
        except (OSError, ValueError) as exc:
            errors.append(f"原始真实快照不可用：{exc}")
        for step in manifest.get("steps", []):
            step_errors = list(errors)
            snapshot_file = step.get("snapshotFile")
            if step.get("kind") == "snapshot" and snapshot_file:
                try:
                    body, actual = _bytes_and_hash(snapshot_file, SCENARIO_ROOT)
                    if actual != step.get("sha256"):
                        step_errors.append("回放快照 SHA-256 不匹配")
                    snapshot = ReplaySnapshot.model_validate_json(body)
                    if snapshot.source_id != provenance.get("sourceId"):
                        step_errors.append("回放快照 sourceId 与 provenance 不一致")
                except (OSError, ValueError, ValidationError) as exc:
                    step_errors.append(f"回放快照不可用：{exc}")
            scenario_id = f"{manifest_path.parent.name}:{step.get('stepId', 'invalid')}"
            scenarios.append(ReplayScenario(
                id=scenario_id,
                step_id=step.get("stepId", "invalid"),
                name=step.get("expected", step.get("stepId", "回放场景")),
                source_code=provenance.get("sourceId", "unknown"),
                kind=step.get("kind", "invalid"),
                expected=step.get("expected", ""),
                declared_fields=[change.get("field", "") for change in step.get("changes", [])],
                provenance_file=provenance.get("snapshotFile", ""),
                provenance_sha256=provenance.get("sha256", ""),
                snapshot_file=snapshot_file,
                snapshot_sha256=step.get("sha256"),
                failure_reason=step.get("failureReason"),
                valid=not step_errors,
                validation_error="；".join(step_errors) or None,
            ))
    return scenarios


def get_replay_scenario(scenario_id: str) -> ReplayScenario | None:
    return next((scenario for scenario in list_replay_scenarios() if scenario.id == scenario_id), None)


def _artifact(db: Session, run: CollectionRun, source_file: Path, filename: str, artifact_type: str, metadata: dict):
    body = source_file.read_bytes()
    relative = Path("replay/runs") / str(run.id) / filename
    write_evidence(Path(settings.evidence_root), relative, body)
    artifact = CollectionArtifact(
        run_id=run.id, artifact_type=artifact_type, relative_path=relative.as_posix(),
        request_url=f"replay://{metadata['scenario_id']}", content_type="application/json",
        byte_size=len(body), sha256=hashlib.sha256(body).hexdigest(),
        request_headers={}, response_headers={}, artifact_metadata=metadata,
    )
    db.add(artifact)
    db.flush()
    return artifact


def _normalized(job: ReplayJob) -> NormalizedJob:
    if job.status not in {None, "open", "closed"}:
        raise ValueError("回放岗位 status 只能是 open、closed 或 null")
    if job.status == "closed" and not (job.explicit_closed_evidence or "").strip():
        raise ValueError("回放明确关闭必须包含 explicitClosedEvidence")
    return NormalizedJob(
        external_identity=job.identity, title=job.title, company=job.company, city=job.city,
        requirements=job.requirements, deadline_raw=job.deadline, deadline_at=None,
        recruitment_status=job.status, detail_url=job.detail_url,
        explicit_closed=job.status == "closed", closed_evidence_text=job.explicit_closed_evidence,
        content_hash=tracked_content_hash(job.requirements, job.deadline, job.status),
    )


def run_replay(db: Session, scenario_id: str, triggered_by_user_id: uuid.UUID) -> CollectionRun:
    scenario = get_replay_scenario(scenario_id)
    if scenario is None:
        raise LookupError("回放场景不存在")
    if not scenario.valid:
        raise ValueError(scenario.validation_error or "回放场景校验失败")
    source = db.scalar(select(Source).where(Source.code == scenario.source_code, Source.enabled.is_(True)))
    if source is None:
        raise ValueError("回放来源未初始化或已禁用")
    run = CollectionRun(
        source_id=source.id, triggered_by_user_id=triggered_by_user_id, mode="replay", status="running",
        request_metadata={"scenario_id": scenario.id, "step_id": scenario.step_id, "kind": scenario.kind},
    )
    db.add(run)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise CollectionConflictError(f"{source.name} 已有正在执行的采集或回放") from exc
    db.refresh(run)
    manifest_path = _safe_path(f"replay/scenarios/{scenario.id.split(':', 1)[0]}/replay.json", SCENARIO_ROOT)
    try:
        _artifact(db, run, manifest_path, "manifest.json", "replay_manifest", {
            "scenario_id": scenario.id, "official_schema": "templates/replay.schema.json",
            "provenance_file": scenario.provenance_file, "provenance_sha256": scenario.provenance_sha256,
        })
        if scenario.kind == "source_failure":
            run.status = "failed"
            run.error_code = "REPLAY_SOURCE_FAILURE"
            run.error_message = scenario.failure_reason
            # 来源级失败没有具体岗位失败，failed_count 保持 0。
        else:
            snapshot_path = _safe_path(scenario.snapshot_file or "", SCENARIO_ROOT)
            snapshot_artifact = _artifact(db, run, snapshot_path, "snapshot.json", "replay_snapshot", {
                "scenario_id": scenario.id, "source_file": scenario.snapshot_file,
                "source_sha256": scenario.snapshot_sha256, "declared_fields_for_review_only": scenario.declared_fields,
            })
            snapshot = ReplaySnapshot.model_validate_json(snapshot_path.read_bytes())
            run.fetched_count = len(snapshot.jobs)
            now = datetime.now(timezone.utc)
            for replay_job in snapshot.jobs:
                try:
                    result = _ingest_job(
                        db, run=run, source=source, normalized=_normalized(replay_job),
                        list_artifact=snapshot_artifact, detail_artifact=snapshot_artifact,
                        observed_at=now, origin="replay", existing_only=True,
                    )
                    run.valid_count += 1
                    if result == "changed":
                        run.changed_count += 1
                    else:
                        run.unchanged_count += 1
                except ValueError as exc:
                    run.failed_count += 1
                    run.error_message = str(exc)[:4000]
            if run.valid_count == 0:
                run.status = "failed"
                run.error_code = "REPLAY_NO_VALID_JOBS"
            elif run.failed_count:
                run.status = "partial"
                run.error_code = "REPLAY_PARTIAL_JOB_FAILURE"
            else:
                run.status = "success"
    except Exception as exc:
        db.rollback()
        run = db.get(CollectionRun, run.id)
        run.status = "failed"
        run.error_code = "REPLAY_EXECUTION_FAILED"
        run.error_message = str(exc)[:4000]
    run.finished_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(run)
    return run
