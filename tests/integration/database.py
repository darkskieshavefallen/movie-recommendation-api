"""Safety validation for the disposable integration database."""

from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError

LOCAL_DATABASE_NAME = "movie_recommendation_integration_test"
CI_DATABASE_NAME = "movie_recommendation_integration_ci"
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
CI_HOST = "postgres"


def validate_integration_database_url(
    raw_url: str | None,
    *,
    application_database_url: str | None,
    is_ci: bool,
) -> URL:
    """Return a parsed URL only when it satisfies the destructive-test contract."""
    if raw_url is None or not raw_url.strip():
        raise ValueError("INTEGRATION_DATABASE_URL must be set explicitly")

    try:
        url = make_url(raw_url)
    except ArgumentError as error:
        raise ValueError("INTEGRATION_DATABASE_URL must be a valid URL") from error

    if url.drivername != "postgresql+asyncpg":
        raise ValueError("integration database must use postgresql+asyncpg")
    if not all((url.username, url.password, url.host, url.database)):
        raise ValueError("integration database URL must be unambiguous")
    if url.query:
        raise ValueError("integration database URL must not contain query options")

    expected_host = CI_HOST if is_ci else None
    expected_database = CI_DATABASE_NAME if is_ci else LOCAL_DATABASE_NAME
    if (is_ci and url.host != expected_host) or (
        not is_ci and url.host not in LOCAL_HOSTS
    ):
        raise ValueError("integration database host is not approved")
    if url.database != expected_database:
        raise ValueError("integration database name is not approved")

    if application_database_url:
        try:
            application_url = make_url(application_database_url)
        except ArgumentError:
            application_url = None
        if application_url is not None and url == application_url:
            raise ValueError("integration and application databases must differ")

    return url
