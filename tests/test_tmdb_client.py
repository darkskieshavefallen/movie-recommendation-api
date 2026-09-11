"""Unit tests for the asynchronous TMDB movie client."""

import httpx
import pytest
from pydantic import ValidationError

from app.core.settings import Settings
from app.integrations.tmdb import TmdbMovieClient
from app.schemas.external_movie import (
    ExternalMovieSearchQuery,
    ExternalMovieSearchResponse,
)


def tmdb_settings() -> Settings:
    """Build explicit settings that cannot read a developer's local environment."""
    return Settings(
        _env_file=None,
        app_title="Test API",
        app_version="test",
        database_url="postgresql+asyncpg://test:test@localhost/test",
        tmdb_base_url="https://tmdb.invalid/3",
        tmdb_read_access_token="test-fake-tmdb-token",
        tmdb_timeout_seconds=7,
    )


async def test_search_movies_builds_request_and_normalizes_results(caplog):
    """Configured request data produces only application-owned result fields."""
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/3/search/movie"
        assert dict(request.url.params) == {
            "query": "Alien",
            "include_adult": "false",
            "language": "en-US",
            "page": "1",
        }
        assert request.headers["Authorization"] == "Bearer test-fake-tmdb-token"
        assert request.headers["Accept"] == "application/json"
        assert request.extensions["timeout"] == {
            "connect": 7.0,
            "read": 7.0,
            "write": 7.0,
            "pool": 7.0,
        }
        return httpx.Response(
            200,
            json={
                "page": 1,
                "results": [
                    {
                        "id": 348,
                        "title": " Alien ",
                        "release_date": "1979-05-25",
                        "overview": "  A space crew encounters a hostile life-form.  ",
                        "popularity": 123.4,
                    },
                    {
                        "id": 126889,
                        "title": "Alien: Covenant",
                        "release_date": "",
                        "overview": "   ",
                    },
                ],
                "total_pages": 1,
            },
        )

    transport = httpx.MockTransport(handler)
    async with TmdbMovieClient(
        tmdb_settings(), transport=transport
    ) as client:
        result = await client.search_movies(
            ExternalMovieSearchQuery(query=" Alien ")
        )

    assert isinstance(result, ExternalMovieSearchResponse)
    assert result.model_dump() == {
        "query": "Alien",
        "results": [
            {
                "external_id": "348",
                "title": "Alien",
                "release_year": 1979,
                "description": "A space crew encounters a hostile life-form.",
            },
            {
                "external_id": "126889",
                "title": "Alien: Covenant",
                "release_year": None,
                "description": None,
            },
        ],
    }
    assert "test-fake-tmdb-token" not in caplog.text
    assert "/3/search/movie" not in caplog.text


async def test_search_movies_returns_empty_application_response():
    """An empty provider result is a successful search response."""
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"results": []})
    )

    async with TmdbMovieClient(
        tmdb_settings(), transport=transport
    ) as client:
        result = await client.search_movies(
            ExternalMovieSearchQuery(query="Unknown title")
        )

    assert result.model_dump() == {"query": "Unknown title", "results": []}


@pytest.mark.parametrize(
    "payload",
    [
        {"results": [{"id": 348}]},
        {"results": [{"id": "348", "title": "Alien"}]},
        {"results": [{"id": 348, "title": "Alien", "release_date": "bad"}]},
        {},
    ],
)
async def test_search_movies_rejects_malformed_provider_payload(payload):
    """Malformed envelopes and result fields never become application data."""
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=payload)
    )

    async with TmdbMovieClient(
        tmdb_settings(), transport=transport
    ) as client:
        with pytest.raises((ValidationError, ValueError)):
            await client.search_movies(ExternalMovieSearchQuery(query="Alien"))


async def test_context_manager_closes_http_client():
    """Leaving the context releases the reusable HTTPX client."""
    client = TmdbMovieClient(
        tmdb_settings(),
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json={"results": []})
        ),
    )

    async with client:
        assert not client._http_client.is_closed

    assert client._http_client.is_closed
