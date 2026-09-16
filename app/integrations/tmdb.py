"""Asynchronous TMDB client and provider payload models."""

from types import TracebackType
from typing import Annotated, Self

import httpx
from pydantic import BaseModel, ConfigDict, StrictInt, StringConstraints

from app.core.exceptions import (
    ExternalMovieAuthenticationError,
    ExternalMovieInvalidResponseError,
    ExternalMovieRateLimitError,
    ExternalMovieRequestError,
    ExternalMovieTimeoutError,
    ExternalMovieUnavailableError,
)
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
MAX_RETRY_AFTER_DIGITS = 10


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
        token = settings.tmdb_read_access_token
        if token is None:
            raise ValueError("TMDB client requires an enabled integration token")
        self._http_client = httpx.AsyncClient(
            base_url=str(settings.tmdb_base_url),
            headers={
                "Authorization": (
                    "Bearer "
                    f"{token.get_secret_value()}"
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
        try:
            response = await self._http_client.get(
                "search/movie",
                params={
                    "query": search.query,
                    "include_adult": "false",
                    "language": "en-US",
                    "page": "1",
                },
            )
        except httpx.TimeoutException:
            raise ExternalMovieTimeoutError() from None
        except httpx.RequestError:
            raise ExternalMovieUnavailableError() from None

        self._raise_for_provider_status(response)

        try:
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
        except ValueError:
            raise ExternalMovieInvalidResponseError(
                provider_status=response.status_code
            ) from None

    @staticmethod
    def _raise_for_provider_status(response: httpx.Response) -> None:
        """Translate provider HTTP statuses without retaining its response body."""
        status_code = response.status_code
        if status_code in {401, 403}:
            raise ExternalMovieAuthenticationError(
                provider_status=status_code
            )
        if status_code == 429:
            raise ExternalMovieRateLimitError(
                retry_after=TmdbMovieClient._retry_after(
                    response.headers.get("Retry-After")
                )
            )
        if status_code == 504:
            raise ExternalMovieTimeoutError(provider_status=status_code)
        if status_code >= 500:
            raise ExternalMovieUnavailableError(provider_status=status_code)
        if status_code >= 400:
            raise ExternalMovieRequestError(provider_status=status_code)

    @staticmethod
    def _retry_after(value: str | None) -> str | None:
        """Allow only a non-negative integer delay from Retry-After."""
        if value is None:
            return None
        normalized = value.strip()
        if (
            len(normalized) <= MAX_RETRY_AFTER_DIGITS
            and normalized.isascii()
            and normalized.isdecimal()
        ):
            return str(int(normalized))
        return None

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
