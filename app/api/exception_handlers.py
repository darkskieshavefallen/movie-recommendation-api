import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.exceptions import MovieNotFoundError

logger = logging.getLogger(__name__)


async def movie_not_found_exception_handler(
    request: Request,
    exc: MovieNotFoundError,
) -> JSONResponse:
    """Handle missing movie errors."""
    logger.warning(
        "Movie not found: method=%s path=%s error=%s",
        request.method,
        request.url.path,
        str(exc),
    )

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


async def general_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.exception(
        "Unhandled exception: method=%s path=%s",
        request.method,
        request.url.path,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register application exception handlers."""
    app.add_exception_handler(
        MovieNotFoundError,
        movie_not_found_exception_handler,
    )
    app.add_exception_handler(
        Exception,
        general_exception_handler,
    )
