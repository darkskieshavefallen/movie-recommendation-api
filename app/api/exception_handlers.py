import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    ExternalMovieAuthenticationError,
    ExternalMovieDisabledError,
    ExternalMovieInvalidResponseError,
    ExternalMovieProviderError,
    ExternalMovieRateLimitError,
    ExternalMovieRequestError,
    ExternalMovieTimeoutError,
    ExternalMovieUnavailableError,
    MovieNotFoundError,
)

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


async def external_movie_provider_exception_handler(
    request: Request,
    exc: ExternalMovieProviderError,
) -> JSONResponse:
    """Map external movie failures to stable responses without provider details."""
    status_by_error = {
        ExternalMovieDisabledError: status.HTTP_503_SERVICE_UNAVAILABLE,
        ExternalMovieAuthenticationError: status.HTTP_502_BAD_GATEWAY,
        ExternalMovieRateLimitError: status.HTTP_503_SERVICE_UNAVAILABLE,
        ExternalMovieTimeoutError: status.HTTP_504_GATEWAY_TIMEOUT,
        ExternalMovieUnavailableError: status.HTTP_503_SERVICE_UNAVAILABLE,
        ExternalMovieInvalidResponseError: status.HTTP_502_BAD_GATEWAY,
        ExternalMovieRequestError: status.HTTP_502_BAD_GATEWAY,
    }
    response_status = status_by_error.get(
        type(exc), status.HTTP_502_BAD_GATEWAY
    )
    headers = None
    if isinstance(exc, ExternalMovieRateLimitError) and exc.retry_after:
        headers = {"Retry-After": exc.retry_after}

    logger.warning(
        "External movie provider failure: code=%s method=%s path=%s "
        "provider_status=%s",
        exc.code,
        request.method,
        request.url.path,
        exc.provider_status,
    )

    return JSONResponse(
        status_code=response_status,
        content={"detail": str(exc)},
        headers=headers,
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
        ExternalMovieProviderError,
        external_movie_provider_exception_handler,
    )
    app.add_exception_handler(
        Exception,
        general_exception_handler,
    )
