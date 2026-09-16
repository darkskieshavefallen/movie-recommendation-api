from typing import ClassVar


class AppError(Exception):
    """Base class for application errors."""


class MovieNotFoundError(AppError):
    """Error raised when a movie cannot be found."""

    def __init__(self, movie_id: int) -> None:
        """Initialize the error with a movie identifier."""
        self.movie_id = movie_id
        super().__init__(f"Movie with id {movie_id} was not found.")


class ExternalMovieProviderError(AppError):
    """Base error for failures at the external movie provider boundary."""

    code: ClassVar[str] = "external_movie_provider_error"
    public_message: ClassVar[str] = "External movie provider request failed."

    def __init__(self, *, provider_status: int | None = None) -> None:
        """Keep only safe diagnostic context from the provider failure."""
        self.provider_status = provider_status
        super().__init__(self.public_message)


class ExternalMovieDisabledError(ExternalMovieProviderError):
    """The optional external movie catalog is not configured."""

    code = "external_movie_disabled"
    public_message = "External movie catalog is disabled."


class ExternalMovieAuthenticationError(ExternalMovieProviderError):
    """The provider rejected the configured application credential."""

    code = "external_movie_authentication_failed"
    public_message = "External movie provider authentication failed."


class ExternalMovieRateLimitError(ExternalMovieProviderError):
    """The provider refused a request because its rate limit was reached."""

    code = "external_movie_rate_limited"
    public_message = "External movie provider rate limit exceeded."

    def __init__(self, *, retry_after: str | None = None) -> None:
        """Store an already validated retry delay for the API response."""
        self.retry_after = retry_after
        super().__init__(provider_status=429)


class ExternalMovieTimeoutError(ExternalMovieProviderError):
    """The provider request did not complete within the configured timeout."""

    code = "external_movie_timeout"
    public_message = "External movie provider timed out."


class ExternalMovieUnavailableError(ExternalMovieProviderError):
    """The provider could not be reached or returned a server failure."""

    code = "external_movie_unavailable"
    public_message = "External movie provider is unavailable."


class ExternalMovieInvalidResponseError(ExternalMovieProviderError):
    """The provider returned data that violates the integration contract."""

    code = "external_movie_invalid_response"
    public_message = "External movie provider returned an invalid response."


class ExternalMovieRequestError(ExternalMovieProviderError):
    """The provider rejected an otherwise valid application request."""

    code = "external_movie_request_failed"
