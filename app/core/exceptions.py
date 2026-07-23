class AppError(Exception):
    """Base class for application errors."""


class MovieNotFoundError(AppError):
    """Error raised when a movie cannot be found."""

    def __init__(self, movie_id: int) -> None:
        """Initialize the error with a movie identifier."""
        self.movie_id = movie_id
        super().__init__(f"Movie with id {movie_id} was not found.")
