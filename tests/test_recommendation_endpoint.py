"""Endpoint tests for local movie recommendations."""

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_recommendation_service
from app.api.exception_handlers import register_exception_handlers
from app.api.movies import router
from app.core.exceptions import MovieNotFoundError
from app.schemas.recommendation import (
    MovieRecommendation,
    MovieRecommendations,
)
from app.services.recommendation import RecommendationService


@pytest.fixture
def mock_recommendation_service():
    """Return an async recommendation service mock."""
    return AsyncMock(spec=RecommendationService)


@pytest.fixture
def endpoint_app(mock_recommendation_service):
    """Build an isolated movie API with recommendation logic replaced."""
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router)
    app.dependency_overrides[get_recommendation_service] = (
        lambda: mock_recommendation_service
    )
    return app


async def get(endpoint_app: FastAPI, path: str):
    """Send one GET request to the isolated ASGI application."""
    async with AsyncClient(
        transport=ASGITransport(app=endpoint_app),
        base_url="http://test",
    ) as client:
        return await client.get(path)


async def test_recommendation_endpoint_returns_ordered_explanations(
    endpoint_app,
    mock_recommendation_service,
):
    """The endpoint preserves service order and uses the default limit."""
    mock_recommendation_service.recommend_movies.return_value = (
        MovieRecommendations(
            source_movie_id=10,
            recommendations=[
                MovieRecommendation(
                    movie_id=15,
                    title="Second Orbit",
                    release_year=2002,
                    matching_genres=["drama", "science fiction"],
                ),
                MovieRecommendation(
                    movie_id=30,
                    title="Quiet Signal",
                    release_year=2001,
                    matching_genres=["science fiction"],
                ),
            ],
        )
    )

    response = await get(endpoint_app, "/movies/10/recommendations")

    assert response.status_code == 200
    assert response.json() == {
        "source_movie_id": 10,
        "recommendations": [
            {
                "movie_id": 15,
                "title": "Second Orbit",
                "release_year": 2002,
                "matching_genres": ["drama", "science fiction"],
            },
            {
                "movie_id": 30,
                "title": "Quiet Signal",
                "release_year": 2001,
                "matching_genres": ["science fiction"],
            },
        ],
    }
    mock_recommendation_service.recommend_movies.assert_awaited_once_with(
        10,
        limit=5,
    )


async def test_recommendation_endpoint_forwards_custom_limit(
    endpoint_app,
    mock_recommendation_service,
):
    """A valid explicit limit reaches the service unchanged."""
    mock_recommendation_service.recommend_movies.return_value = (
        MovieRecommendations(source_movie_id=7, recommendations=[])
    )

    response = await get(endpoint_app, "/movies/7/recommendations?limit=2")

    assert response.status_code == 200
    mock_recommendation_service.recommend_movies.assert_awaited_once_with(
        7,
        limit=2,
    )


async def test_recommendation_endpoint_returns_empty_success(
    endpoint_app,
    mock_recommendation_service,
):
    """No eligible local candidate remains a successful response."""
    mock_recommendation_service.recommend_movies.return_value = (
        MovieRecommendations(source_movie_id=4, recommendations=[])
    )

    response = await get(endpoint_app, "/movies/4/recommendations")

    assert response.status_code == 200
    assert response.json() == {
        "source_movie_id": 4,
        "recommendations": [],
    }


async def test_recommendation_endpoint_maps_unknown_source_to_404(
    endpoint_app,
    mock_recommendation_service,
):
    """The existing movie-not-found handler owns the public error shape."""
    mock_recommendation_service.recommend_movies.side_effect = (
        MovieNotFoundError(999)
    )

    response = await get(endpoint_app, "/movies/999/recommendations")

    assert response.status_code == 404
    assert response.json() == {"detail": "Movie with id 999 was not found."}


@pytest.mark.parametrize(
    "path",
    [
        "/movies/0/recommendations",
        "/movies/not-an-id/recommendations",
        "/movies/1/recommendations?limit=0",
        "/movies/1/recommendations?limit=21",
        "/movies/1/recommendations?limit=not-an-integer",
    ],
)
async def test_recommendation_endpoint_rejects_invalid_input(
    endpoint_app,
    mock_recommendation_service,
    path,
):
    """FastAPI rejects invalid identifiers and limits before the service."""
    response = await get(endpoint_app, path)

    assert response.status_code == 422
    mock_recommendation_service.recommend_movies.assert_not_awaited()


def test_openapi_documents_recommendation_contract(endpoint_app):
    """OpenAPI describes the success, missing source, and validation cases."""
    operation = endpoint_app.openapi()["paths"][
        "/movies/{movie_id}/recommendations"
    ]["get"]
    parameters = {
        parameter["name"]: parameter for parameter in operation["parameters"]
    }

    assert parameters["movie_id"]["required"] is True
    assert parameters["movie_id"]["schema"]["minimum"] == 1
    assert parameters["limit"]["required"] is False
    assert parameters["limit"]["schema"] == {
        "type": "integer",
        "maximum": 20,
        "minimum": 1,
        "default": 5,
        "title": "Limit",
    }
    assert set(operation["responses"]) == {"200", "404", "422"}
    assert operation["responses"]["200"]["content"]["application/json"][
        "schema"
    ] == {"$ref": "#/components/schemas/MovieRecommendations"}
