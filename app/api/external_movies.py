"""HTTP endpoints for read-only external movie catalog search."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import get_external_movie_service
from app.schemas.external_movie import (
    ExternalMovieErrorResponse,
    ExternalMovieSearchQuery,
    ExternalMovieSearchResponse,
)
from app.services.external_movie import ExternalMovieService

router = APIRouter(
    prefix="/external/movies",
    tags=["External movies"],
)


@router.get(
    "/search",
    response_model=ExternalMovieSearchResponse,
    summary="Search the external movie catalog",
    responses={
        status.HTTP_502_BAD_GATEWAY: {
            "model": ExternalMovieErrorResponse,
            "description": "Provider authentication, request, or response failure.",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ExternalMovieErrorResponse,
            "description": "Provider unavailable or rate limited.",
        },
        status.HTTP_504_GATEWAY_TIMEOUT: {
            "model": ExternalMovieErrorResponse,
            "description": "Provider request timed out.",
        },
    },
)
async def search_external_movies(
    search: Annotated[ExternalMovieSearchQuery, Query()],
    service: Annotated[
        ExternalMovieService,
        Depends(get_external_movie_service),
    ],
) -> ExternalMovieSearchResponse:
    """Search external movies without reading or writing local movie records."""
    return await service.search_movies(search)
