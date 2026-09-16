"""Endpoint tests for local movie genres."""

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_movie_service
from app.api.movies import router
from app.schemas.movie import MovieCreate, MovieRead, MovieUpdate
from app.services.movie import MovieService


@pytest.fixture
def mock_movie_service():
    """Return an async movie service mock."""
    return AsyncMock(spec=MovieService)


@pytest.fixture
def endpoint_app(mock_movie_service):
    """Build an isolated movie API with its service replaced."""
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_movie_service] = lambda: mock_movie_service
    return app


async def request(endpoint_app, method: str, path: str, json=None):
    """Send one request to the isolated ASGI application."""
    async with AsyncClient(
        transport=ASGITransport(app=endpoint_app),
        base_url="http://test",
    ) as client:
        return await client.request(method, path, json=json)


async def test_create_movie_endpoint_normalizes_and_returns_genres(
    endpoint_app,
    mock_movie_service,
):
    """POST passes canonical genres to the service and returns them."""
    mock_movie_service.create_movie.return_value = MovieRead(
        id=1,
        title="Orbit",
        release_year=2000,
        genres=["drama", "science fiction"],
    )

    response = await request(
        endpoint_app,
        "POST",
        "/movies/",
        json={
            "title": "Orbit",
            "release_year": 2000,
            "genres": [" Science   Fiction ", "DRAMA"],
        },
    )

    assert response.status_code == 201
    assert response.json()["genres"] == ["drama", "science fiction"]
    mock_movie_service.create_movie.assert_awaited_once_with(
        MovieCreate(
            title="Orbit",
            release_year=2000,
            genres=["drama", "science fiction"],
        )
    )


async def test_update_movie_endpoint_normalizes_and_returns_genres(
    endpoint_app,
    mock_movie_service,
):
    """PUT applies the same genre contract as create."""
    mock_movie_service.update_movie.return_value = MovieRead(
        id=1,
        title="Orbit",
        release_year=2001,
        genres=["adventure", "drama"],
    )

    response = await request(
        endpoint_app,
        "PUT",
        "/movies/1",
        json={
            "title": "Orbit",
            "release_year": 2001,
            "genres": [" Drama ", "Adventure"],
        },
    )

    assert response.status_code == 200
    assert response.json()["genres"] == ["adventure", "drama"]
    mock_movie_service.update_movie.assert_awaited_once_with(
        1,
        MovieUpdate(
            title="Orbit",
            release_year=2001,
            genres=["adventure", "drama"],
        ),
    )


async def test_get_movie_endpoint_returns_empty_genres_for_existing_movie(
    endpoint_app,
    mock_movie_service,
):
    """GET exposes the empty value assigned to rows predating genres."""
    mock_movie_service.get_movie.return_value = MovieRead(
        id=1,
        title="Existing movie",
        release_year=1995,
    )

    response = await request(endpoint_app, "GET", "/movies/1")

    assert response.status_code == 200
    assert response.json()["genres"] == []


@pytest.mark.parametrize(
    "payload",
    [
        {"title": "   ", "release_year": 2000},
        {"title": "x" * 256, "release_year": 2000},
        {"title": "Too early", "release_year": 1887},
        {"title": "Too late", "release_year": 2101},
    ],
)
async def test_invalid_movie_fields_return_422_before_service(
    endpoint_app,
    mock_movie_service,
    payload,
):
    """API validation owns title/year failures instead of PostgreSQL."""
    response = await request(endpoint_app, "POST", "/movies/", json=payload)

    assert response.status_code == 422
    mock_movie_service.create_movie.assert_not_awaited()
