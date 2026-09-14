"""Shared fixtures for pytest tests."""

import os

os.environ.update(
    {
        "APP_TITLE": "Test API",
        "APP_VERSION": "test",
        "DATABASE_URL": "postgresql+asyncpg://test:test@localhost/test",
        "LOG_LEVEL": "INFO",
        "TMDB_BASE_URL": "https://tmdb.invalid/3",
        "TMDB_READ_ACCESS_TOKEN": "test-fake-tmdb-read-access-token",
        "TMDB_TIMEOUT_SECONDS": "5",
    }
)
