from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import MovieNotFoundError
from app.repositories.movie import MovieRepository
from app.schemas.movie import MovieCreate, MovieRead


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

            return MovieRead.model_validate(orm_movie)

        except Exception:
            await self._session.rollback()
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
