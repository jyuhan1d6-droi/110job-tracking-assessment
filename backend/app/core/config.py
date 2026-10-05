from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_secret_key: str = "replace-with-a-long-random-value"
    access_token_minutes: int = 30
    database_url: str = "postgresql+psycopg://job_tracker:change-me-for-production@postgres:5432/job_tracker"
    evidence_root: str = "/evidence/runtime"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

