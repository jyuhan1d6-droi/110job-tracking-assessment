from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    session_hours: int = 24
    session_cookie_name: str = "job_tracker_session"
    session_cookie_secure: bool = False
    seed_jobseeker1_password: str = "exam-jobseeker1"
    seed_jobseeker2_password: str = "exam-jobseeker2"
    seed_maintainer_password: str = "exam-maintainer"
    database_url: str = "postgresql+psycopg://job_tracker:change-me-for-production@postgres:5432/job_tracker"
    evidence_root: str = "/evidence/runtime"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
