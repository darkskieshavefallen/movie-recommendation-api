from functools import lru_cache
from typing import Annotated

from pydantic import Field, HttpUrl, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_title: str
    app_version: str
    database_url: str
    log_level: str = "INFO"
    tmdb_base_url: HttpUrl
    tmdb_read_access_token: SecretStr
    tmdb_timeout_seconds: Annotated[
        float,
        Field(gt=0, allow_inf_nan=False),
    ]

    @field_validator("tmdb_base_url")
    @classmethod
    def validate_tmdb_base_url(cls, value: HttpUrl) -> HttpUrl:
        """Require a safe provider base URL without URL-level credentials."""
        if value.scheme != "https":
            raise ValueError("TMDB base URL must use HTTPS")
        if value.username or value.password or value.query or value.fragment:
            raise ValueError(
                "TMDB base URL must not contain credentials, query, or fragment"
            )
        return value

    @field_validator("tmdb_read_access_token")
    @classmethod
    def validate_tmdb_read_access_token(cls, value: SecretStr) -> SecretStr:
        """Reject a missing-value equivalent while keeping the token secret."""
        token = value.get_secret_value().strip()
        if not token:
            raise ValueError("TMDB read access token must not be empty")
        return SecretStr(token)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
