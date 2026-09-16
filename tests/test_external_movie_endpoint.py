"""Endpoint tests for read-only external movie catalog search."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app import main as main_module
from app.api.dependencies import get_tmdb_movie_client
from app.api.exception_handlers import register_exception_handlers
from app.api.external_movies import router
from app.core.exceptions import (
    ExternalMovieAuthenticationError,
    ExternalMovieDisabledError,
    ExternalMovieInvalidResponseError,
    ExternalMovieRateLimitError,
    ExternalMovieRequestError,
    ExternalMovieTimeoutError,
    ExternalMovieUnavailableError,
)
from app.integrations.tmdb import TmdbMovieClient
from app.schemas.external_movie import (
    ExternalMovieSearchQuery,
    ExternalMovieSearchResponse,
    ExternalMovieSearchResult,
)


@pytest.fixture
def mock_tmdb_client():
    """Return an async client mock that cannot make network requests."""
    return AsyncMock(spec=TmdbMovieClient)


@pytest.fixture
def endpoint_app(mock_tmdb_client):
    """Build an isolated endpoint app with the integration dependency replaced."""
    app = FastAPI()
    app.include_router(router)
    register_exception_handlers(app)
    app.dependency_overrides[get_tmdb_movie_client] = lambda: mock_tmdb_client
    return app


async def get(endpoint_app, path: str):
    """Send one request to the isolated ASGI application."""
    async with AsyncClient(
        transport=ASGITransport(app=endpoint_app, raise_app_exceptions=False),
        base_url="http://test",
    ) as client:
        return await client.get(path)


async def test_search_endpoint_normalizes_query_and_returns_results(
    endpoint_app,
    mock_tmdb_client,
):
    """A valid query reaches the integration and returns its application model."""
    mock_tmdb_client.search_movies.return_value = ExternalMovieSearchResponse(
        query="Alien",
        results=[
            ExternalMovieSearchResult(
                external_id="348",
                title="Alien",
                release_year=1979,
                description="A space crew encounters a hostile life-form.",
            )
        ],
    )

    response = await get(endpoint_app, "/external/movies/search?query=%20Alien%20")

    assert response.status_code == 200
    assert response.json() == {
        "query": "Alien",
        "results": [
            {
                "external_id": "348",
                "title": "Alien",
                "release_year": 1979,
                "description": "A space crew encounters a hostile life-form.",
            }
        ],
    }
    mock_tmdb_client.search_movies.assert_awaited_once_with(
        ExternalMovieSearchQuery(query="Alien")
    )


async def test_search_endpoint_returns_empty_results(
    endpoint_app,
    mock_tmdb_client,
):
    """No provider matches remains a successful response."""
    mock_tmdb_client.search_movies.return_value = ExternalMovieSearchResponse(
        query="Unknown title",
        results=[],
    )

    response = await get(
        endpoint_app,
        "/external/movies/search?query=Unknown%20title",
    )

    assert response.status_code == 200
    assert response.json() == {"query": "Unknown title", "results": []}


async def test_search_endpoint_returns_503_when_catalog_is_disabled():
    """The optional endpoint fails safely without constructing a TMDB client."""
    app = FastAPI()
    app.state.tmdb_movie_client = None
    app.include_router(router)
    register_exception_handlers(app)

    response = await get(app, "/external/movies/search?query=Alien")

    assert response.status_code == 503
    assert response.json() == {"detail": str(ExternalMovieDisabledError())}


@pytest.mark.parametrize(
    "path",
    [
        "/external/movies/search",
        "/external/movies/search?query=%20%20%20",
        f"/external/movies/search?query={'x' * 201}",
    ],
)
async def test_search_endpoint_rejects_invalid_query_before_provider(
    endpoint_app,
    mock_tmdb_client,
    path,
):
    """Missing, blank, and overlong terms fail without an integration call."""
    response = await get(endpoint_app, path)

    assert response.status_code == 422
    mock_tmdb_client.search_movies.assert_not_awaited()


@pytest.mark.parametrize(
    ("error", "expected_status"),
    [
        (ExternalMovieAuthenticationError(provider_status=401), 502),
        (ExternalMovieInvalidResponseError(provider_status=200), 502),
        (ExternalMovieRequestError(provider_status=400), 502),
        (ExternalMovieRateLimitError(retry_after="17"), 503),
        (ExternalMovieUnavailableError(provider_status=503), 503),
        (ExternalMovieTimeoutError(), 504),
    ],
)
async def test_search_endpoint_uses_provider_error_handlers(
    endpoint_app,
    mock_tmdb_client,
    error,
    expected_status,
):
    """Domain failures use the public mappings registered in ANT-22."""
    mock_tmdb_client.search_movies.side_effect = error

    response = await get(endpoint_app, "/external/movies/search?query=Alien")

    assert response.status_code == expected_status
    assert response.json() == {"detail": str(error)}


def test_openapi_documents_external_search_contract(endpoint_app):
    """OpenAPI describes input, success, validation, and provider failures."""
    operation = endpoint_app.openapi()["paths"]["/external/movies/search"]["get"]
    query_parameter = next(
        parameter
        for parameter in operation["parameters"]
        if parameter["name"] == "query"
    )

    assert query_parameter["required"] is True
    assert query_parameter["description"] == (
        "Movie title to search for in the external catalog."
    )
    assert query_parameter["schema"]["minLength"] == 1
    assert query_parameter["schema"]["maxLength"] == 200
    assert set(operation["responses"]) == {"200", "422", "502", "503", "504"}
    assert operation["responses"]["200"]["content"]["application/json"][
        "schema"
    ] == {"$ref": "#/components/schemas/ExternalMovieSearchResponse"}


async def test_lifespan_exposes_one_client_and_closes_it(monkeypatch):
    """Application startup owns one client until shutdown completes."""
    client = MagicMock(spec=TmdbMovieClient)
    client.__aenter__.return_value = client
    client.__aexit__.return_value = None
    client_factory = MagicMock(return_value=client)
    monkeypatch.setattr(main_module, "TmdbMovieClient", client_factory)
    monkeypatch.setattr(main_module.app_settings, "tmdb_enabled", True)
    app = FastAPI()

    async with main_module.lifespan(app):
        assert app.state.tmdb_movie_client is client
        client.__aexit__.assert_not_awaited()

    client_factory.assert_called_once_with(main_module.app_settings)
    client.__aenter__.assert_awaited_once_with()
    client.__aexit__.assert_awaited_once_with(None, None, None)


async def test_lifespan_skips_client_when_catalog_is_disabled(monkeypatch):
    """Local startup succeeds without a provider token or HTTP client."""
    client_factory = MagicMock()
    monkeypatch.setattr(main_module, "TmdbMovieClient", client_factory)
    monkeypatch.setattr(main_module.app_settings, "tmdb_enabled", False)
    app = FastAPI()

    async with main_module.lifespan(app):
        assert app.state.tmdb_movie_client is None

    client_factory.assert_not_called()
