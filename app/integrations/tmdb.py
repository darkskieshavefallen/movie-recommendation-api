"""Asynchronous TMDB client and provider payload models."""

from types import TracebackType
from typing import Annotated, Self

import httpx
from pydantic import BaseModel, ConfigDict, StrictInt, StringConstraints

from app.core.settings import Settings
from app.schemas.external_movie import (
    ExternalMovieSearchQuery,
    ExternalMovieSearchResponse,
    ExternalMovieSearchResult,
)

TmdbRequiredText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
]


class TmdbMovieResult(BaseModel):
    """Provider payload for one TMDB movie search result."""

    id: StrictInt
    title: TmdbRequiredText
    release_date: str | None = None
    overview: str | None = None

    model_config = ConfigDict(extra="ignore")


class TmdbMovieSearchResponse(BaseModel):
    """Provider payload envelope returned by TMDB movie search."""

    results: list[TmdbMovieResult]

    model_config = ConfigDict(extra="ignore")


class TmdbMovieClient:
    """Search TMDB and translate its payload into application models."""

    def __init__(
        self,
        settings: Settings,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        """Create one reusable HTTP client from validated application settings."""
        self._http_client = httpx.AsyncClient(
            base_url=str(settings.tmdb_base_url),
            headers={
                "Authorization": (
                    "Bearer "
                    f"{settings.tmdb_read_access_token.get_secret_value()}"
                ),
                "Accept": "application/json",
            },
            timeout=settings.tmdb_timeout_seconds,
            transport=transport,
        )

    async def __aenter__(self) -> Self:
        """Enter the managed client lifecycle."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close the underlying HTTP client when leaving the context."""
        await self.aclose()

    async def aclose(self) -> None:
        """Release HTTP connections held by this client."""
        await self._http_client.aclose()

    async def search_movies(
        self,
        search: ExternalMovieSearchQuery,
    ) -> ExternalMovieSearchResponse:
        """Search the first TMDB result page and normalize every match."""
        response = await self._http_client.get(
            "search/movie",
            params={
                "query": search.query,
                "include_adult": "false",
                "language": "en-US",
                "page": "1",
            },
        )
        response.raise_for_status()

        provider_response = TmdbMovieSearchResponse.model_validate(
            response.json()
        )
        return ExternalMovieSearchResponse(
            query=search.query,
            results=[
                self._normalize_result(result)
                for result in provider_response.results
            ],
        )

    @staticmethod
    def _normalize_result(result: TmdbMovieResult) -> ExternalMovieSearchResult:
        """Translate one provider-owned result into the application schema."""
        return ExternalMovieSearchResult(
            external_id=str(result.id),
            title=result.title,
            release_year=TmdbMovieClient._release_year(result.release_date),
            description=TmdbMovieClient._optional_text(result.overview),
        )

    @staticmethod
    def _release_year(release_date: str | None) -> int | None:
        """Extract a year from a TMDB date while preserving missing values."""
        if not release_date:
            return None
        year = release_date[:4]
        if len(year) != 4 or not year.isdecimal():
            raise ValueError("TMDB release date does not start with a year")
        return int(year)

    @staticmethod
    def _optional_text(value: str | None) -> str | None:
        """Normalize missing or blank optional provider text to None."""
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None
