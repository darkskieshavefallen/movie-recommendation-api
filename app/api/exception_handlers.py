from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.exceptions import MovieNotFoundError


async def movie_not_found_exception_handler(
    request: Request,
    exc: MovieNotFoundError,
) -> JSONResponse:
    """Handle missing movie errors."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register application exception handlers."""
    app.add_exception_handler(
        MovieNotFoundError,
        movie_not_found_exception_handler,
    )
