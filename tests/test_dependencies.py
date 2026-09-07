"""Check dependency resolution through FastAPI without a live database."""

from typing import Annotated
from unittest.mock import AsyncMock

from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient


async def test_request_shares_session_and_cleans_up(monkeypatch):
    """Repository and service share one yielded session within each request."""
    monkeypatch.setenv("APP_TITLE", "Test API")
    monkeypatch.setenv("APP_VERSION", "test")
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test"
    )
    from app.api.dependencies import get_movie_service
    from app.api.health import router
    from app.core.database import get_db
    from app.services.movie import MovieService

    app = FastAPI()
    app.include_router(router)
    session = AsyncMock()
    events = []

    async def override_db():
        events.append("open")
        try:
            yield session
        finally:
            events.append("close")

    app.dependency_overrides[get_db] = override_db

    @app.get("/dependency-probe")
    async def probe(service: Annotated[MovieService, Depends(get_movie_service)]):
        assert service._session is session
        assert service._repository.session is session
        return {"shared": True}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/dependency-probe")
        assert response.status_code == 200
        assert response.json() == {"shared": True}
        assert events == ["open", "close"]

        response = await client.get("/health/db")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        session.execute.assert_awaited_once()
        assert str(session.execute.await_args.args[0]) == "SELECT 1"
        assert events == ["open", "close", "open", "close"]
