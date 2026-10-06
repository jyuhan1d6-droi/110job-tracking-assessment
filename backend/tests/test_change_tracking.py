import uuid
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.collectors.base import NormalizedJob, tracked_content_hash
from app.db.session import engine
from app.models.collection import CollectionArtifact, CollectionRun
from app.models.job import Job, JobChangeSet, JobFieldChange, JobObservation
from app.models.source import Source
from app.models.user import User
from app.models.watch import JobWatch, WatchEvent
from app.services.collection import _ingest_job, normalized_explicit_closure
from app.services.watch_events import create_watch_events_for_change_set, get_watch_event, list_watch_events


def normalized(*, requirements: str, deadline: str | None, status: str | None = None) -> NormalizedJob:
    return NormalizedJob(
        external_identity="test-source:stable-id",
        title="测试岗位",
        company="测试公司",
        city="北京",
        requirements=requirements,
        deadline_raw=deadline,
        deadline_at=None,
        recruitment_status=status,
        detail_url="https://example.test/job/stable-id",
        content_hash=tracked_content_hash(requirements, deadline, status),
    )


def test_tracked_field_changes_a_b_a_and_explicit_close_are_persisted():
    connection = engine.connect()
    transaction = connection.begin()
    db = Session(bind=connection, autoflush=True, expire_on_commit=False)
    try:
        user = User(
            username=f"change-test-{uuid.uuid4()}",
            password_hash="hash",
            display_name="Change test",
            role="maintainer",
        )
        source = Source(
            code=f"change-source-{uuid.uuid4()}",
            name="Change source",
            source_type="company_careers",
            entry_url="https://example.test/jobs",
            collector_key="change_test",
            request_interval_ms=0,
            timeout_seconds=10,
            max_retries=0,
        )
        db.add_all([user, source])
        db.flush()

        def make_run_and_artifacts(
            index: int, *, new: int = 0, changed: int = 0, unchanged: int = 0,
            mode: str = "live",
        ):
            run = CollectionRun(
                source_id=source.id,
                triggered_by_user_id=user.id,
                mode=mode,
                status="success",
                fetched_count=1,
                valid_count=1,
                new_count=new,
                changed_count=changed,
                unchanged_count=unchanged,
                failed_count=0,
                request_metadata={},
            )
            db.add(run)
            db.flush()
            artifacts = []
            for kind in ("list_json", "detail_json"):
                artifact = CollectionArtifact(
                    run_id=run.id,
                    artifact_type=kind,
                    relative_path=f"test/{run.id}/{kind}.json",
                    request_url="https://example.test",
                    byte_size=2,
                    sha256=str(index) * 64,
                    request_headers={},
                    response_headers={},
                    artifact_metadata={},
                )
                db.add(artifact)
                artifacts.append(artifact)
            db.flush()
            return run, artifacts[0], artifacts[1]

        start = datetime.now(timezone.utc)
        state_a = normalized(requirements="要求 A", deadline="2026-12-01")
        run1, list1, detail1 = make_run_and_artifacts(1, new=1)
        assert _ingest_job(
            db, run=run1, source=source, normalized=state_a,
            list_artifact=list1, detail_artifact=detail1, observed_at=start,
        ) == "new"
        job = db.scalar(select(Job).where(Job.source_id == source.id))
        second_user = User(
            username=f"change-test-second-{uuid.uuid4()}", password_hash="hash",
            display_name="Second watcher", role="job_seeker",
        )
        db.add(second_user)
        db.flush()
        first_watch = JobWatch(user_id=user.id, job_id=job.id, watched_at=start + timedelta(seconds=30))
        second_watch = JobWatch(user_id=second_user.id, job_id=job.id, watched_at=start + timedelta(seconds=30))
        db.add_all([first_watch, second_watch])
        db.flush()

        def event_count(*watches):
            return db.scalar(
                select(func.count()).select_from(WatchEvent).where(
                    WatchEvent.watch_id.in_([watch.id for watch in watches])
                )
            )

        assert event_count(first_watch, second_watch) == 0

        hash_only_difference = replace(state_a, content_hash="f" * 64)
        run_hash, list_hash, detail_hash = make_run_and_artifacts(5, unchanged=1)
        assert _ingest_job(
            db, run=run_hash, source=source, normalized=hash_only_difference,
            list_artifact=list_hash, detail_artifact=detail_hash,
            observed_at=start + timedelta(seconds=45),
        ) == "unchanged"
        assert db.scalar(select(JobChangeSet).where(JobChangeSet.run_id == run_hash.id)) is None
        assert event_count(first_watch, second_watch) == 0
        live_seen_before_replay = job.last_live_seen_at

        replay_state = replace(
            state_a,
            title="baseArtifact 中的历史标题",
            company="baseArtifact 中的历史公司",
            city="baseArtifact 中的历史城市",
            detail_url="https://example.test/base-artifact/job",
        )
        run_replay, list_replay, detail_replay = make_run_and_artifacts(
            6, unchanged=1, mode="replay"
        )
        replayed_at = start + timedelta(seconds=50)
        assert _ingest_job(
            db, run=run_replay, source=source, normalized=replay_state,
            list_artifact=list_replay, detail_artifact=detail_replay,
            observed_at=replayed_at, origin="replay", existing_only=True,
        ) == "unchanged"
        assert job.title == "测试岗位"
        assert job.company == "测试公司"
        assert job.city == "北京"
        assert job.detail_url == "https://example.test/job/stable-id"
        assert job.last_live_seen_at == live_seen_before_replay
        assert job.last_replay_seen_at == replayed_at
        assert db.scalar(select(JobChangeSet).where(JobChangeSet.run_id == run_replay.id)) is None

        state_b = normalized(requirements="要求 B", deadline="2027-01-01", status="open")
        run2, list2, detail2 = make_run_and_artifacts(2, changed=1)
        assert _ingest_job(
            db, run=run2, source=source, normalized=state_b,
            list_artifact=list2, detail_artifact=detail2, observed_at=start + timedelta(minutes=1),
        ) == "changed"
        change2 = db.scalar(select(JobChangeSet).where(JobChangeSet.run_id == run2.id))
        fields2 = set(db.scalars(select(JobFieldChange.field_name).where(JobFieldChange.change_set_id == change2.id)))
        assert fields2 == {"requirements", "deadline", "recruitment_status"}
        assert event_count(first_watch, second_watch) == 2
        assert create_watch_events_for_change_set(db, change2) == 0
        first_event = db.scalar(select(WatchEvent).where(WatchEvent.watch_id == first_watch.id))
        detail = get_watch_event(db, user.id, first_event.id)
        assert detail is not None
        assert detail.change_count == 3
        assert get_watch_event(db, second_user.id, first_event.id) is None

        first_watch.unwatched_at = start + timedelta(minutes=1, seconds=30)
        db.flush()

        run3, list3, detail3 = make_run_and_artifacts(3, changed=1)
        assert _ingest_job(
            db, run=run3, source=source, normalized=state_a,
            list_artifact=list3, detail_artifact=detail3, observed_at=start + timedelta(minutes=2),
        ) == "changed"
        assert db.scalar(
            select(func.count()).select_from(JobChangeSet).where(JobChangeSet.job_id == job.id)
        ) == 2
        assert event_count(first_watch, second_watch) == 3

        refollow = JobWatch(user_id=user.id, job_id=job.id, watched_at=start + timedelta(minutes=2, seconds=30))
        db.add(refollow)
        db.flush()

        closed = normalized_explicit_closure(job, "来源明确显示：该职位已下架")
        run4, list4, detail4 = make_run_and_artifacts(4, changed=1)
        assert _ingest_job(
            db, run=run4, source=source, normalized=closed,
            list_artifact=list4, detail_artifact=detail4, observed_at=start + timedelta(minutes=3),
        ) == "changed"
        observation = db.scalar(select(JobObservation).where(JobObservation.run_id == run4.id))
        assert observation.recruitment_status == "closed"
        assert observation.explicit_closed is True
        assert observation.closed_evidence_text == "来源明确显示：该职位已下架"
        close_fields = set(
            db.scalars(
                select(JobFieldChange.field_name)
                .join(JobChangeSet)
                .where(JobChangeSet.run_id == run4.id)
            )
        )
        assert close_fields == {"recruitment_status"}
        assert event_count(first_watch, second_watch, refollow) == 5
        assert list_watch_events(db, user.id, 1, 20).total == 2
        assert list_watch_events(db, second_user.id, 1, 20).total == 3

        invalid_closed = replace(
            state_a,
            recruitment_status="closed",
            content_hash=tracked_content_hash(state_a.requirements, state_a.deadline_raw, "closed"),
        )
        with pytest.raises(ValueError, match="明确来源证据"):
            _ingest_job(
                db, run=run4, source=source, normalized=invalid_closed,
                list_artifact=list4, detail_artifact=detail4, observed_at=start + timedelta(minutes=4),
            )
    finally:
        db.close()
        transaction.rollback()
        connection.close()
