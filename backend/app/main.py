from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.core.config import settings

app = FastAPI(
    title="岗位搜索与变更追踪 API",
    version="0.1.0",
    docs_url="/api/docs" if settings.app_env != "production" else None,
    openapi_url="/api/openapi.json" if settings.app_env != "production" else None,
)
app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
