"""Opt-in command that seeds the configured local development database."""

import asyncio
from dataclasses import dataclass

from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

from app.core.settings import get_settings

LOCAL_DATABASE_HOSTS = frozenset({"localhost", "127.0.0.1", "::1", "db"})
SAFE_DATABASE_NAMES = frozenset({"movie_recommendation"})
SAFE_DATABASE_SUFFIXES = ("_dev", "_test", "_demo", "_ci")


class UnsafeDemoDatabaseError(ValueError):
    """Raised when the seed target does not look like a development database."""


@dataclass(frozen=True, slots=True)
class DemoDatabaseTarget:
    """Credential-free target details suitable for terminal output."""

    host: str
    port: int
    database: str


def validate_demo_database_url(database_url: str) -> DemoDatabaseTarget:
    """Allow the demo seed only for recognizable local PostgreSQL targets."""
    try:
        url = make_url(database_url)
    except ArgumentError as error:
        raise UnsafeDemoDatabaseError("the database URL is invalid") from error
    host = url.host
    database = url.database

    if url.get_backend_name() != "postgresql":
        raise UnsafeDemoDatabaseError("the database backend must be PostgreSQL")
    if host not in LOCAL_DATABASE_HOSTS:
        raise UnsafeDemoDatabaseError(
            "the database host must be localhost, a loopback address, or 'db'"
        )
    if not database or (
        database not in SAFE_DATABASE_NAMES
        and not database.endswith(SAFE_DATABASE_SUFFIXES)
    ):
        raise UnsafeDemoDatabaseError(
            "the database name must be movie_recommendation or end with "
            "_dev, _test, _demo, or _ci"
        )

    return DemoDatabaseTarget(
        host=host,
        port=url.port or 5432,
        database=database,
    )


async def seed_configured_database() -> None:
    """Validate the configured target, seed it, and print a safe summary."""
    settings = get_settings()
    target = validate_demo_database_url(settings.database_url)
    print(
        "Seeding local demo catalog in "
        f"database '{target.database}' at {target.host}:{target.port}..."
    )

    from app.core.database import engine, session_factory
    from app.repositories.movie import MovieRepository
    from app.services.demo_catalog import DemoCatalogService

    try:
        async with session_factory() as session:
            service = DemoCatalogService(
                repository=MovieRepository(session),
                session=session,
            )
            result = await service.seed()
    finally:
        await engine.dispose()

    print(
        f"Demo catalog ready: created={result.created}, "
        f"skipped={result.skipped}."
    )


def main() -> None:
    """Run the asynchronous seed command."""
    try:
        asyncio.run(seed_configured_database())
    except UnsafeDemoDatabaseError as error:
        raise SystemExit(f"Refusing to seed: {error}") from error


if __name__ == "__main__":
    main()
