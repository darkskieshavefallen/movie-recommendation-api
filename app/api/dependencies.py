from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ExternalMovieDisabledError
from app.integrations.tmdb import TmdbMovieClient
from app.repositories.movie import MovieRepository
from app.services.external_movie import ExternalMovieService
from app.services.movie import MovieService
from app.services.recommendation import RecommendationService


def get_tmdb_movie_client(request: Request) -> TmdbMovieClient:
    """Return the application-scoped external movie client."""
    client = request.app.state.tmdb_movie_client
    if client is None:
        raise ExternalMovieDisabledError()
    return client


def get_external_movie_service(
    client: Annotated[TmdbMovieClient, Depends(get_tmdb_movie_client)],
) -> ExternalMovieService:
    """Provide the service for read-only external catalog searches."""
    return ExternalMovieService(client=client)


def get_movie_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MovieRepository:
    """Provide a movie repository instance."""
    return MovieRepository(session=db)


def get_movie_service(
    repository: Annotated[MovieRepository, Depends(get_movie_repository)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MovieService:
    """Provide a movie service instance."""
    return MovieService(
        repository=repository,
        session=db,
    )


def get_recommendation_service(
    repository: Annotated[MovieRepository, Depends(get_movie_repository)],
) -> RecommendationService:
    """Provide the read-only local recommendation service."""
    return RecommendationService(repository=repository)
