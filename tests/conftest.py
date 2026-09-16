"""Shared fixtures for pytest tests."""

import os

os.environ.update(
    {
        "APP_TITLE": "Test API",
        "APP_VERSION": "test",
        "DATABASE_URL": os.environ.get(
            "INTEGRATION_DATABASE_URL",
            "postgresql+asyncpg://test:test@localhost/test",
        ),
        "LOG_LEVEL": "INFO",
        "CORS_ALLOWED_ORIGINS": '["http://localhost:5173"]',
        "TMDB_ENABLED": "false",
        "TMDB_BASE_URL": "https://tmdb.invalid/3",
        "TMDB_READ_ACCESS_TOKEN": "test-fake-tmdb-read-access-token",
        "TMDB_TIMEOUT_SECONDS": "5",
    }
)
