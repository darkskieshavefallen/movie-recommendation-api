from functools import lru_cache
from typing import Annotated
from urllib.parse import urlsplit

from pydantic import Field, HttpUrl, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_title: str
    app_version: str
    database_url: str
    log_level: str = "INFO"
    cors_allowed_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173"]
    )
    tmdb_enabled: bool = False
    tmdb_base_url: HttpUrl = HttpUrl("https://api.themoviedb.org/3")
    tmdb_read_access_token: SecretStr | None = None
    tmdb_timeout_seconds: Annotated[
        float,
        Field(gt=0, allow_inf_nan=False),
    ] = 5

    @field_validator("cors_allowed_origins")
    @classmethod
    def validate_cors_allowed_origins(cls, values: list[str]) -> list[str]:
        """Accept only explicit HTTP origins and reject the global wildcard."""
        normalized: list[str] = []
        for value in values:
            origin = value.strip().rstrip("/")
            parsed = urlsplit(origin)
            if (
                origin == "*"
                or parsed.scheme not in {"http", "https"}
                or not parsed.hostname
                or parsed.username
                or parsed.password
                or parsed.path
                or parsed.query
                or parsed.fragment
            ):
                raise ValueError(
                    "CORS origins must be explicit HTTP(S) origins without "
                    "credentials, path, query, or fragment"
                )
            normalized.append(origin)

        if len(set(normalized)) != len(normalized):
            raise ValueError("CORS origins must be unique")
        return normalized

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

    @field_validator("tmdb_read_access_token", mode="before")
    @classmethod
    def normalize_tmdb_read_access_token(
        cls,
        value: SecretStr | str | None,
    ) -> SecretStr | None:
        """Normalize an optional credential while keeping it secret."""
        if value is None:
            return None
        token = (
            value.get_secret_value()
            if isinstance(value, SecretStr)
            else value
        ).strip()
        return SecretStr(token) if token else None

    @model_validator(mode="after")
    def validate_enabled_tmdb_configuration(self) -> "Settings":
        """Require a credential only when the external catalog is enabled."""
        if self.tmdb_enabled and self.tmdb_read_access_token is None:
            raise ValueError(
                "TMDB read access token is required when TMDB is enabled"
            )
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
