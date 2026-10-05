from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User
from app.models.source import Source

SEED_USERS = (
    ("jobseeker1", "求职者一", "job_seeker", "seed_jobseeker1_password"),
    ("jobseeker2", "求职者二", "job_seeker", "seed_jobseeker2_password"),
    ("maintainer", "数据维护员", "maintainer", "seed_maintainer_password"),
)


def seed_users() -> int:
    created = 0
    with SessionLocal() as db:
        for username, display_name, role, password_setting in SEED_USERS:
            if db.scalar(select(User).where(User.username == username)) is not None:
                continue
            db.add(
                User(
                    username=username,
                    display_name=display_name,
                    role=role,
                    password_hash=hash_password(getattr(settings, password_setting)),
                )
            )
            created += 1
        db.commit()
    return created


def seed_sources() -> int:
    with SessionLocal() as db:
        if db.scalar(select(Source).where(Source.code == "360-careers")) is not None:
            return 0
        db.add(
            Source(
                code="360-careers",
                name="360 招聘",
                source_type="company_careers",
                entry_url="https://hr.360.cn/hr/list",
                official_evidence_url="https://hr.360.cn/hr/",
                collector_key="360_careers",
                request_interval_ms=1000,
                timeout_seconds=15,
                max_retries=2,
            )
        )
        db.commit()
        return 1


if __name__ == "__main__":
    print(f"Seeded {seed_users()} user(s).")
    print(f"Seeded {seed_sources()} source(s).")
