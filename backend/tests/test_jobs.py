import uuid
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.session import engine
from app.main import app
from app.models.collection import CollectionRun
from app.models.job import Job
from app.models.source import Source
from app.models.user import User
from app.services.jobs import get_job_detail, list_cities, search_jobs


def test_jobs_api_requires_login():
    client = TestClient(app)
    assert client.get("/api/jobs").status_code == 401
    assert client.get("/api/jobs/cities").status_code == 401
    assert client.get("/api/jobs/summary").status_code == 401


def test_search_and_pagination_rules_with_transactional_data():
    connection = engine.connect()
    transaction = connection.begin()
    db = Session(bind=connection, autoflush=True, expire_on_commit=False)
    marker = uuid.uuid4().hex
    marker_city = f"测试城市-{marker}"
    try:
        user = User(
            username=f"jobs-test-{marker}", password_hash="hash", display_name="Jobs test", role="maintainer"
        )
        source = Source(
            code=f"jobs-source-{marker}", name="测试来源", source_type="company_careers",
            entry_url="https://example.test/jobs", collector_key="jobs_test",
            request_interval_ms=0, timeout_seconds=10, max_retries=0,
        )
        db.add_all([user, source])
        db.flush()
        run = CollectionRun(
            source_id=source.id, triggered_by_user_id=user.id, mode="live", status="success",
            fetched_count=5, valid_count=5, new_count=5, changed_count=0,
            unchanged_count=0, failed_count=0, request_metadata={},
        )
        db.add(run)
        db.flush()
        now = datetime.now(timezone.utc)

        def add_job(index: int, title: str, city: str, requirements: str, *, visible: bool = True) -> Job:
            job = Job(
                source_id=source.id, external_identity=f"test:{marker}:{index}", title=title,
                company="测试公司", city=city, requirements=requirements,
                deadline_provided=False, status_provided=False,
                detail_url=f"https://example.test/jobs/{index}", first_seen_at=now,
                last_seen_at=now, current_content_hash=f"{index:x}" * 64,
                created_by_run_id=run.id, updated_by_run_id=run.id, is_visible=visible,
            )
            db.add(job)
            return job

        first = add_job(1, f"{marker} Python 后端", marker_city, "熟悉 PostgreSQL")
        add_job(2, f"{marker} 同名岗位", marker_city, "要求包含 Python")
        add_job(3, f"{marker} 同名岗位", "其他城市", "普通要求")
        add_job(4, f"{marker} 100%_可靠", marker_city, "特殊字符")
        add_job(5, f"{marker} 隐藏岗位", marker_city, "Python", visible=False)
        db.flush()

        by_marker = search_jobs(db, keyword=marker, city=None, page=1, page_size=20)
        assert by_marker.total == 4
        assert len({item.id for item in by_marker.items}) == 4

        by_requirements = search_jobs(db, keyword="Python", city=marker_city, page=1, page_size=20)
        assert by_requirements.total == 2

        and_miss = search_jobs(db, keyword="PostgreSQL", city="其他城市", page=1, page_size=20)
        assert and_miss.total == 0

        literal_wildcards = search_jobs(db, keyword="100%_", city=marker_city, page=1, page_size=20)
        assert literal_wildcards.total == 1

        page1 = search_jobs(db, keyword=marker, city=None, page=1, page_size=2)
        page2 = search_jobs(db, keyword=marker, city=None, page=2, page_size=2)
        assert page1.total_pages == 2
        assert not ({item.id for item in page1.items} & {item.id for item in page2.items})

        blank_filters = search_jobs(db, keyword="   ", city="   ", page=1, page_size=100)
        assert blank_filters.filters.keyword == ""
        assert blank_filters.filters.city == ""

        assert marker_city in list_cities(db)
        detail = get_job_detail(db, first.id)
        assert detail is not None
        assert detail.requirements == "熟悉 PostgreSQL"
        assert detail.deadline_provided is False
        assert detail.status_provided is False
    finally:
        db.close()
        transaction.rollback()
        connection.close()
