"""Service for the opt-in local development catalog seed."""

from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.demo_catalog import DEMO_MOVIES, DemoMovie
from app.repositories.movie import MovieRepository


@dataclass(frozen=True, slots=True)
class DemoCatalogSeedResult:
    """Counts returned after one seed attempt."""

    created: int
    skipped: int


class DemoCatalogService:
    """Insert missing demo movies without changing existing records."""

    def __init__(
        self,
        repository: MovieRepository,
        session: AsyncSession,
    ) -> None:
        """Initialize the service with its transaction dependencies."""
        self._repository = repository
        self._session = session

    async def seed(
        self,
        movies: Sequence[DemoMovie] = DEMO_MOVIES,
    ) -> DemoCatalogSeedResult:
        """Insert missing title/year pairs and commit them atomically."""
        identities = {(movie.title, movie.release_year) for movie in movies}
        existing = await self._repository.get_existing_identities(identities)
        missing = [
            movie
            for movie in movies
            if (movie.title, movie.release_year) not in existing
        ]

        if not missing:
            return DemoCatalogSeedResult(created=0, skipped=len(movies))

        try:
            for movie in missing:
                await self._repository.add(
                    title=movie.title,
                    release_year=movie.release_year,
                    description=None,
                    genres=list(movie.genres),
                )

            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

        return DemoCatalogSeedResult(
            created=len(missing),
            skipped=len(movies) - len(missing),
        )
