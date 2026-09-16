"""Contract tests for integration database safety and setup."""

import os

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from tests.integration.database import (
    CI_DATABASE_NAME,
    LOCAL_DATABASE_NAME,
    validate_integration_database_url,
)

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    ("raw_url", "is_ci"),
    [
        (None, False),
        ("not a URL", False),
        (f"postgresql://u:p@localhost/{LOCAL_DATABASE_NAME}", False),
        (f"postgresql+asyncpg://u:p@db/{LOCAL_DATABASE_NAME}", False),
        ("postgresql+asyncpg://u:p@localhost/movie_recommendation", False),
        (f"postgresql+asyncpg://u:p@localhost/{CI_DATABASE_NAME}", True),
    ],
)
def test_unsafe_database_urls_are_rejected(
    raw_url: str | None,
    is_ci: bool,
) -> None:
    with pytest.raises(ValueError):
        validate_integration_database_url(
            raw_url,
            application_database_url=None,
            is_ci=is_ci,
        )


def test_application_database_url_is_rejected() -> None:
    url = f"postgresql+asyncpg://u:p@localhost/{LOCAL_DATABASE_NAME}"

    with pytest.raises(ValueError, match="must differ"):
        validate_integration_database_url(
            url,
            application_database_url=url,
            is_ci=False,
        )


async def test_approved_database_is_migrated(
    integration_engine: AsyncEngine,
) -> None:
    async with integration_engine.connect() as connection:
        revision = await connection.scalar(
            text("SELECT version_num FROM alembic_version")
        )
        movie_table = await connection.scalar(
            text("SELECT to_regclass('public.movies')")
        )
        constraints = set(
            (
                await connection.execute(
                    text(
                        "SELECT conname FROM pg_constraint "
                        "WHERE conrelid = 'movies'::regclass"
                    )
                )
            ).scalars()
        )

    assert revision == "c3d9a6f4b2e1"
    assert movie_table == "movies"
    assert "ck_movies_title_length" in constraints
    assert "ck_movies_release_year_range" in constraints
    assert os.environ["TMDB_BASE_URL"] == "https://tmdb.invalid/3"
