"""Contract tests for integration database safety and setup."""

import asyncio
import os

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from tests.integration.database import (
    CI_DATABASE_NAME,
    LOCAL_DATABASE_NAME,
    validate_integration_database_url,
)

pytestmark = pytest.mark.integration


async def insert_legacy_movies(database_url: URL) -> None:
    """Insert rows accepted immediately before the ANT-38 migration."""
    engine = create_async_engine(database_url)
    try:
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    "INSERT INTO movies "
                    "(title, release_year, description, genres) VALUES "
                    "('   ', 2000, NULL, '{}'), "
                    "('Too old', 1800, NULL, '{}'), "
                    "('Too new', 2200, NULL, '{}'), "
                    "('Legacy valid', 1999, NULL, '{}')"
                )
            )
    finally:
        await engine.dispose()


async def read_migration_result(
    database_url: URL,
) -> tuple[list[tuple[str, int]], dict[str, bool]]:
    """Read retained rows and validation state after the real upgrade."""
    engine = create_async_engine(database_url)
    try:
        async with engine.connect() as connection:
            rows = list(
                (
                    await connection.execute(
                        text(
                            "SELECT title, release_year FROM movies "
                            "ORDER BY id"
                        )
                    )
                ).tuples()
            )
            constraints = dict(
                (
                    await connection.execute(
                        text(
                            "SELECT conname, convalidated "
                            "FROM pg_constraint "
                            "WHERE conrelid = 'movies'::regclass "
                            "AND conname LIKE 'ck_movies_%'"
                        )
                    )
                ).tuples()
            )
        return rows, constraints
    finally:
        await engine.dispose()


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


def test_constraint_migration_cleans_only_invalid_legacy_rows(
    migrated_database: None,
    integration_database_url: URL,
) -> None:
    """Upgrade a populated previous revision without blocking application startup."""
    config = Config("alembic.ini")
    command.downgrade(config, "8f3a2d7c1b4e")
    try:
        asyncio.run(insert_legacy_movies(integration_database_url))

        command.upgrade(config, "head")

        rows, constraints = asyncio.run(
            read_migration_result(integration_database_url)
        )
        assert rows == [("Legacy valid", 1999)]
        assert constraints == {
            "ck_movies_release_year_range": True,
            "ck_movies_title_length": True,
        }
    finally:
        command.upgrade(config, "head")


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
