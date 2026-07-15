from fastapi import FastAPI

app = FastAPI(
    title="Movie Recommendation API",
    description="Backend service for movie recommendations.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.get(
    "/health",
    summary="Health check",
)
def health_check() -> dict[str, str]:
    return {"status": "ok"}