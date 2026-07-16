from fastapi import FastAPI

from app.core.settings import get_settings

app_settings = get_settings()

app = FastAPI(
    title=app_settings.app_title,
    description="Backend service for movie recommendations.",
    version=app_settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.get("/health", summary="Health check")
def health_check() -> dict[str, str]:
    return {"status": "ok"}