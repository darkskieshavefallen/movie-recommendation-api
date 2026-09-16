"""Tests for public handling of external movie provider failures."""

from unittest.mock import patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api import exception_handlers
from app.api.exception_handlers import register_exception_handlers
from app.core.exceptions import (
    ExternalMovieAuthenticationError,
    ExternalMovieDisabledError,
    ExternalMovieInvalidResponseError,
    ExternalMovieRateLimitError,
    ExternalMovieRequestError,
    ExternalMovieTimeoutError,
    ExternalMovieUnavailableError,
    MovieNotFoundError,
)


@pytest.mark.parametrize(
    ("error", "expected_status", "expected_detail", "retry_after"),
    [
        (
            ExternalMovieDisabledError(),
            503,
            "External movie catalog is disabled.",
            None,
        ),
        (
            ExternalMovieAuthenticationError(provider_status=401),
            502,
            "External movie provider authentication failed.",
            None,
        ),
        (
            ExternalMovieRateLimitError(retry_after="17"),
            503,
            "External movie provider rate limit exceeded.",
            "17",
        ),
        (
            ExternalMovieTimeoutError(),
            504,
            "External movie provider timed out.",
            None,
        ),
        (
            ExternalMovieUnavailableError(provider_status=503),
            503,
            "External movie provider is unavailable.",
            None,
        ),
        (
            ExternalMovieInvalidResponseError(provider_status=200),
            502,
            "External movie provider returned an invalid response.",
            None,
        ),
        (
            ExternalMovieRequestError(provider_status=418),
            502,
            "External movie provider request failed.",
            None,
        ),
    ],
)
async def test_external_failure_has_safe_stable_response_and_log(
    error,
    expected_status,
    expected_detail,
    retry_after,
):
    """Every provider category maps without exposing query or credentials."""
    app = FastAPI()

    @app.get("/external-error")
    async def raise_external_error():
        raise error

    register_exception_handlers(app)

    with patch.object(exception_handlers.logger, "warning") as log_warning:
        async with AsyncClient(
            transport=ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://test",
        ) as client:
            response = await client.get(
                "/external-error?query=private-search-term"
            )

    assert response.status_code == expected_status
    assert response.json() == {"detail": expected_detail}
    if retry_after is None:
        assert "Retry-After" not in response.headers
    else:
        assert response.headers["Retry-After"] == retry_after

    log_warning.assert_called_once_with(
        "External movie provider failure: code=%s method=%s path=%s "
        "provider_status=%s",
        error.code,
        "GET",
        "/external-error",
        error.provider_status,
    )


async def test_movie_not_found_response_remains_unchanged():
    """The external handler does not alter existing CRUD error behavior."""
    app = FastAPI()

    @app.get("/movie-error")
    async def raise_movie_error():
        raise MovieNotFoundError(42)

    register_exception_handlers(app)

    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as client:
        response = await client.get("/movie-error")

    assert response.status_code == 404
    assert response.json() == {"detail": "Movie with id 42 was not found."}
