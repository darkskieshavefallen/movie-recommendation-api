from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.movie import MovieRepository
from app.services.movie import MovieService


def get_movie_repository(
    db: AsyncSession = Depends(get_db),
) -> MovieRepository:
    """Provide a movie repository instance."""
    return MovieRepository(session=db)


def get_movie_service(
    repository: MovieRepository = Depends(get_movie_repository),
    db: AsyncSession = Depends(get_db),
) -> MovieService:
    """Provide a movie service instance."""
    return MovieService(
        repository=repository,
        session=db,
    )
