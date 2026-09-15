from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status

from app.api.dependencies import get_movie_service, get_recommendation_service
from app.schemas.movie import MovieCreate, MovieRead, MovieUpdate
from app.schemas.recommendation import (
    DEFAULT_RECOMMENDATION_LIMIT,
    MAX_RECOMMENDATION_LIMIT,
    MIN_RECOMMENDATION_LIMIT,
    MovieRecommendations,
)
from app.services.movie import MovieService
from app.services.recommendation import RecommendationService

router = APIRouter(
    prefix="/movies",
    tags=["Movies"],
)


@router.get(
    "/",
    response_model=list[MovieRead],
)
async def list_movies(
    service: Annotated[MovieService, Depends(get_movie_service)],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[MovieRead]:
    """Return a paginated list of movies."""
    return await service.list_movies(
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{movie_id}/recommendations",
    response_model=MovieRecommendations,
    summary="Recommend similar local movies",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "The source movie was not found.",
        },
    },
)
async def recommend_movies(
    movie_id: Annotated[int, Path(ge=1)],
    service: Annotated[
        RecommendationService,
        Depends(get_recommendation_service),
    ],
    limit: Annotated[
        int,
        Query(
            ge=MIN_RECOMMENDATION_LIMIT,
            le=MAX_RECOMMENDATION_LIMIT,
        ),
    ] = DEFAULT_RECOMMENDATION_LIMIT,
) -> MovieRecommendations:
    """Return deterministic recommendations from the local catalog."""
    return await service.recommend_movies(movie_id, limit=limit)


@router.get(
    "/{movie_id}",
    response_model=MovieRead,
)
async def get_movie(
    movie_id: Annotated[int, Path(ge=1)],
    service: Annotated[MovieService, Depends(get_movie_service)],
) -> MovieRead:
    """Return a movie by its ID."""
    return await service.get_movie(movie_id)


@router.put(
    "/{movie_id}",
    response_model=MovieRead,
)
async def update_movie(
    movie_id: Annotated[int, Path(ge=1)],
    movie: MovieUpdate,
    service: Annotated[MovieService, Depends(get_movie_service)],
) -> MovieRead:
    """Update an existing movie."""
    return await service.update_movie(movie_id, movie)


@router.delete(
    "/{movie_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_movie(
    movie_id: Annotated[int, Path(ge=1)],
    service: Annotated[MovieService, Depends(get_movie_service)],
) -> None:
    """Delete an existing movie."""
    await service.delete_movie(movie_id)


@router.post(
    "/",
    response_model=MovieRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_movie(
    movie: MovieCreate,
    service: Annotated[MovieService, Depends(get_movie_service)],
) -> MovieRead:
    """Create a new movie."""
    return await service.create_movie(movie)
