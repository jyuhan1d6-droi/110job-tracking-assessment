import os
import uuid
from contextlib import contextmanager

import psycopg
import pytest


def database_url() -> str:
    return os.environ["DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://", 1)


@pytest.fixture
def db():
    connection = psycopg.connect(database_url())
    try:
        yield connection
    finally:
        connection.rollback()
        connection.close()


@contextmanager
def expect_database_error(db, error_type):
    savepoint = f"sp_{uuid.uuid4().hex}"
    db.execute(f"SAVEPOINT {savepoint}")
    with pytest.raises(error_type):
        yield
    db.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
    db.execute(f"RELEASE SAVEPOINT {savepoint}")


def seed_user_and_source(db):
    user_id = uuid.uuid4()
    source_id = uuid.uuid4()
    db.execute(
        """
        INSERT INTO users (id, username, password_hash, display_name, role, is_active)
        VALUES (%s, %s, 'hash', 'Maintainer', 'maintainer', true)
        """,
        (user_id, f"maintainer-{user_id}"),
    )
    db.execute(
        """
        INSERT INTO sources (
            id, code, name, source_type, entry_url, collector_key,
            request_interval_ms, timeout_seconds, max_retries, enabled
        ) VALUES (%s, %s, 'Test source', 'recruitment_platform', 'https://example.test',
                  'test', 1000, 15, 2, true)
        """,
        (source_id, f"source-{source_id}"),
    )
    return user_id, source_id


def insert_run(db, user_id, source_id, *, status, new=0, changed=0, unchanged=0):
    run_id = uuid.uuid4()
    valid = new + changed + unchanged
    db.execute(
        """
        INSERT INTO collection_runs (
            id, source_id, triggered_by_user_id, mode, status,
            fetched_count, valid_count, new_count, changed_count,
            unchanged_count, failed_count, request_metadata
        ) VALUES (%s, %s, %s, 'live', %s, %s, %s, %s, %s, %s, 0, '{}'::jsonb)
        """,
        (run_id, source_id, user_id, status, valid, valid, new, changed, unchanged),
    )
    return run_id


def test_active_run_and_job_identity_are_unique(db):
    user_id, source_id = seed_user_and_source(db)
    run_id = insert_run(db, user_id, source_id, status="pending")

    with expect_database_error(db, psycopg.errors.UniqueViolation):
        insert_run(db, user_id, source_id, status="running")

    job_id = uuid.uuid4()
    db.execute(
        """
        INSERT INTO jobs (
            id, source_id, external_identity, title, company, city, requirements,
            deadline_provided, status_provided, detail_url, first_seen_at, last_seen_at,
            current_content_hash, created_by_run_id, updated_by_run_id, is_visible
        ) VALUES (%s, %s, 'stable-id', 'Title', 'Company', 'City', 'Requirements',
                  false, false, 'https://example.test/job', now(), now(), %s, %s, %s, true)
        """,
        (job_id, source_id, "a" * 64, run_id, run_id),
    )

    with expect_database_error(db, psycopg.errors.UniqueViolation):
        db.execute(
            """
            INSERT INTO jobs (
                id, source_id, external_identity, title, company, city, requirements,
                deadline_provided, status_provided, detail_url, first_seen_at, last_seen_at,
                current_content_hash, created_by_run_id, updated_by_run_id, is_visible
            ) VALUES (%s, %s, 'stable-id', 'Other', 'Company', 'City', 'Requirements',
                      false, false, 'https://example.test/other', now(), now(), %s, %s, %s, true)
            """,
            (uuid.uuid4(), source_id, "b" * 64, run_id, run_id),
        )

    with expect_database_error(db, psycopg.errors.ForeignKeyViolation):
        db.execute("DELETE FROM sources WHERE id = %s", (source_id,))


def test_repeated_hash_across_later_changes_is_allowed_and_close_requires_evidence(db):
    user_id, source_id = seed_user_and_source(db)
    run_initial = insert_run(db, user_id, source_id, status="success", new=1)
    run_to_b = insert_run(db, user_id, source_id, status="success", changed=1)
    run_back_to_a = insert_run(db, user_id, source_id, status="success", changed=1)
    run_invalid_close = insert_run(db, user_id, source_id, status="success", unchanged=1)

    job_id = uuid.uuid4()
    db.execute(
        """
        INSERT INTO jobs (
            id, source_id, external_identity, title, company, city, requirements,
            deadline_provided, status_provided, detail_url, first_seen_at, last_seen_at,
            current_content_hash, created_by_run_id, updated_by_run_id, is_visible
        ) VALUES (%s, %s, 'stable-id', 'Title', 'Company', 'City', 'A', false, false,
                  'https://example.test/job', now(), now(), %s, %s, %s, true)
        """,
        (job_id, source_id, "a" * 64, run_initial, run_initial),
    )

    observations = []
    for run_id, requirements, content_hash in (
        (run_to_b, "B", "b" * 64),
        (run_back_to_a, "A", "a" * 64),
    ):
        observation_id = uuid.uuid4()
        observations.append(observation_id)
        db.execute(
            """
            INSERT INTO job_observations (
                id, run_id, job_id, external_identity, title, company, city, requirements,
                deadline_provided, status_provided, detail_url, content_hash,
                explicit_closed, observed_at
            ) VALUES (%s, %s, %s, 'stable-id', 'Title', 'Company', 'City', %s,
                      false, false, 'https://example.test/job', %s, false, now())
            """,
            (observation_id, run_id, job_id, requirements, content_hash),
        )
        change_set_id = uuid.uuid4()
        db.execute(
            """
            INSERT INTO job_change_sets (
                id, job_id, run_id, observation_id, change_hash, origin
            ) VALUES (%s, %s, %s, %s, %s, 'live')
            """,
            (change_set_id, job_id, run_id, observation_id, "c" * 64),
        )

    count = db.execute(
        "SELECT count(*) FROM job_change_sets WHERE job_id = %s", (job_id,)
    ).fetchone()[0]
    assert count == 2

    with expect_database_error(db, psycopg.errors.CheckViolation):
        db.execute(
            """
            INSERT INTO job_observations (
                id, run_id, job_id, external_identity, title, company, city, requirements,
                deadline_provided, recruitment_status, status_provided, detail_url,
                content_hash, explicit_closed, observed_at
            ) VALUES (%s, %s, %s, 'stable-id', 'Title', 'Company', 'City', 'A',
                      false, 'closed', true, 'https://example.test/job', %s, false, now())
            """,
            (uuid.uuid4(), run_invalid_close, job_id, "d" * 64),
        )
