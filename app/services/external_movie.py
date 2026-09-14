"""Application service for read-only external movie search."""

from app.integrations.tmdb import TmdbMovieClient
from app.schemas.external_movie import (
    ExternalMovieSearchQuery,
    ExternalMovieSearchResponse,
)


class ExternalMovieService:
    """Coordinate external movie searches without using local persistence."""

    def __init__(self, client: TmdbMovieClient) -> None:
        """Initialize the service with an external catalog client."""
        self._client = client

    async def search_movies(
        self,
        search: ExternalMovieSearchQuery,
    ) -> ExternalMovieSearchResponse:
        """Return normalized external matches without modifying PostgreSQL."""
        return await self._client.search_movies(search)
