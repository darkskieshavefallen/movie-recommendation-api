from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status

from app.api.dependencies import get_movie_service
from app.schemas.movie import MovieCreate, MovieRead
from app.services.movie import MovieService

router = APIRouter(
    prefix="/movies",
    tags=["Movies"],
)


@router.get(
    "/",
    response_model=list[MovieRead],
)
async def list_movies(
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    service: MovieService = Depends(get_movie_service),
) -> list[MovieRead]:
    """Return a paginated list of movies."""
    return await service.list_movies(
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{movie_id}",
    response_model=MovieRead,
)
async def get_movie(
    movie_id: Annotated[int, Path(ge=1)],
    service: MovieService = Depends(get_movie_service),
) -> MovieRead:
    """Return a movie by its ID."""
    return await service.get_movie(movie_id)


@router.post(
    "/",
    response_model=MovieRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_movie(
    movie: MovieCreate,
    service: MovieService = Depends(get_movie_service),
) -> MovieRead:
    """Create a new movie."""
    return await service.create_movie(movie)
