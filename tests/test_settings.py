"""Validation tests for application and external-provider settings."""

import math

import pytest
from pydantic import ValidationError

from app.core.settings import Settings


def valid_settings() -> dict[str, object]:
    """Return explicit values without reading a developer's local .env file."""
    return {
        "app_title": "Test API",
        "app_version": "test",
        "database_url": "postgresql+asyncpg://test:test@localhost/test",
        "log_level": "DEBUG",
        "cors_allowed_origins": ["http://localhost:5173"],
        "tmdb_enabled": True,
        "tmdb_base_url": "https://tmdb.invalid/3",
        "tmdb_read_access_token": "test-fake-tmdb-read-access-token",
        "tmdb_timeout_seconds": 5,
    }


def test_settings_accept_explicit_integration_values():
    """Existing settings and validated TMDB values load together."""
    settings = Settings(_env_file=None, **valid_settings())

    assert settings.database_url.endswith("@localhost/test")
    assert settings.log_level == "DEBUG"
    assert settings.cors_allowed_origins == ["http://localhost:5173"]
    assert settings.tmdb_enabled is True
    assert str(settings.tmdb_base_url) == "https://tmdb.invalid/3"
    assert settings.tmdb_timeout_seconds == 5
    assert "test-fake-tmdb-read-access-token" not in repr(settings)
    assert str(settings.tmdb_read_access_token) == "**********"


def test_settings_allow_disabled_tmdb_without_token(monkeypatch):
    """The local application core needs no external provider credential."""
    monkeypatch.delenv("TMDB_READ_ACCESS_TOKEN", raising=False)
    values = valid_settings()
    values["tmdb_enabled"] = False
    values.pop("tmdb_read_access_token")

    settings = Settings(_env_file=None, **values)

    assert settings.tmdb_enabled is False
    assert settings.tmdb_read_access_token is None


def test_settings_require_token_when_tmdb_is_enabled(monkeypatch):
    """An explicitly enabled integration must have a usable credential."""
    monkeypatch.delenv("TMDB_READ_ACCESS_TOKEN", raising=False)
    values = valid_settings()
    values.pop("tmdb_read_access_token")

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None, **values)

    message = str(exc_info.value)
    assert "TMDB read access token is required" in message


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("tmdb_base_url", "http://tmdb.invalid/3", "must use HTTPS"),
        ("tmdb_base_url", "https://user@tmdb.invalid/3", "must not contain"),
        ("tmdb_read_access_token", "   ", "token is required"),
        ("tmdb_timeout_seconds", 0, "greater than 0"),
        ("tmdb_timeout_seconds", math.inf, "finite number"),
        ("cors_allowed_origins", ["*"], "explicit HTTP"),
        (
            "cors_allowed_origins",
            ["http://localhost:5173", "http://localhost:5173/"],
            "must be unique",
        ),
    ],
)
def test_settings_reject_invalid_integration_values(field, value, error):
    """Invalid integration configuration fails before application startup."""
    values = valid_settings()
    values[field] = value

    with pytest.raises(ValidationError, match=error):
        Settings(_env_file=None, **values)
