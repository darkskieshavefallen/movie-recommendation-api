from fastapi import FastAPI

from app.core.settings import get_settings
from app.api.health import router as health_router

app_settings = get_settings()

app = FastAPI(
    title=app_settings.app_title,
    description="Backend service for movie recommendations.",
    version=app_settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(health_router)
