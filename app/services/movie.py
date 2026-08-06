import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import MovieNotFoundError
from app.repositories.movie import MovieRepository
from app.schemas.movie import MovieCreate, MovieRead, MovieUpdate

logger = logging.getLogger(__name__)


class MovieService:
    """Service for working with movies."""

    def __init__(
        self,
        repository: MovieRepository,
        session: AsyncSession,
    ) -> None:
        """Initialize the service with its dependencies."""
        self._repository = repository
        self._session = session

    async def create_movie(
        self,
        movie: MovieCreate,
    ) -> MovieRead:
        """Create a new movie and return it."""
        try:
            orm_movie = await self._repository.add(
                title=movie.title,
                release_year=movie.release_year,
                description=movie.description,
            )

            await self._session.commit()
            await self._session.refresh(orm_movie)

            logger.info(
                "Movie created successfully: id=%s title=%s",
                orm_movie.id,
                orm_movie.title,
            )

            return MovieRead.model_validate(orm_movie)

        except Exception:
            await self._session.rollback()
            logger.exception(
                "Failed to create movie: title=%s",
                movie.title,
            )
            raise

    async def update_movie(
        self,
        movie_id: int,
        movie: MovieUpdate,
    ) -> MovieRead:
        """Update an existing movie and return it."""
        try:
            orm_movie = await self._repository.update(
                movie_id=movie_id,
                title=movie.title,
                release_year=movie.release_year,
                description=movie.description,
            )

            if orm_movie is None:
                raise MovieNotFoundError(movie_id)

            await self._session.commit()
            await self._session.refresh(orm_movie)

            logger.info(
                "Movie updated successfully: id=%s title=%s",
                movie_id,
                orm_movie.title,
            )

            return MovieRead.model_validate(orm_movie)

        except MovieNotFoundError:
            raise
        except Exception:
            await self._session.rollback()
            logger.exception("Failed to update movie: id=%s", movie_id)
            raise

    async def delete_movie(self, movie_id: int) -> None:
        """Delete an existing movie."""
        try:
            deleted = await self._repository.delete(movie_id)

            if not deleted:
                raise MovieNotFoundError(movie_id)

            await self._session.commit()

            logger.info("Movie deleted successfully: id=%s", movie_id)

        except MovieNotFoundError:
            raise
        except Exception:
            await self._session.rollback()
            logger.exception("Failed to delete movie: id=%s", movie_id)
            raise

    async def get_movie(
        self,
        movie_id: int,
    ) -> MovieRead:
        """Return a movie by its ID."""
        orm_movie = await self._repository.get_by_id(movie_id)

        if orm_movie is None:
            raise MovieNotFoundError(movie_id)

        return MovieRead.model_validate(orm_movie)

    async def list_movies(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> list[MovieRead]:
        """Return a paginated list of movies."""
        orm_movies = await self._repository.get_all(
            offset=offset,
            limit=limit,
        )

        return [
            MovieRead.model_validate(movie)
            for movie in orm_movies
        ]
