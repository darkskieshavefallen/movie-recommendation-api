"""Tests for demo seed target safety checks."""

import pytest

from app.cli.seed_demo import (
    DemoDatabaseTarget,
    UnsafeDemoDatabaseError,
    validate_demo_database_url,
)


@pytest.mark.parametrize(
    ("database_url", "expected"),
    [
        (
            "postgresql+asyncpg://user:secret@localhost/movie_recommendation",
            DemoDatabaseTarget("localhost", 5432, "movie_recommendation"),
        ),
        (
            "postgresql+asyncpg://user:secret@127.0.0.1:55432/catalog_demo",
            DemoDatabaseTarget("127.0.0.1", 55432, "catalog_demo"),
        ),
        (
            "postgresql+asyncpg://user:secret@db/catalog_dev",
            DemoDatabaseTarget("db", 5432, "catalog_dev"),
        ),
    ],
)
def test_validate_demo_database_url_accepts_local_targets(
    database_url,
    expected,
):
    """Loopback and the development Compose service are allowed."""
    assert validate_demo_database_url(database_url) == expected


@pytest.mark.parametrize(
    "database_url",
    [
        "postgresql+asyncpg://user:secret@database.example.com/catalog_demo",
        "postgresql+asyncpg://user:secret@localhost/postgres",
        "sqlite+aiosqlite:///catalog_demo.db",
        "not a database URL",
    ],
)
def test_validate_demo_database_url_rejects_unsafe_targets(database_url):
    """Production-like, system, non-PostgreSQL, and invalid targets fail."""
    with pytest.raises(UnsafeDemoDatabaseError):
        validate_demo_database_url(database_url)
