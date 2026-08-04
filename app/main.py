from fastapi import FastAPI

from app.api.exception_handlers import register_exception_handlers
from app.api.health import router as health_router
from app.api.movies import router as movies_router
from app.core.settings import get_settings

app_settings = get_settings()

app = FastAPI(
    title=app_settings.app_title,
    description="Backend service for movie recommendations.",
    version=app_settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

register_exception_handlers(app)

app.include_router(health_router)
app.include_router(movies_router)
