"""Reusable fixtures for tests that cross the real PostgreSQL boundary."""

import os
from collections.abc import AsyncIterator, Iterator

import httpx
import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.database import engine as application_engine
from app.main import app
from tests.integration.database import validate_integration_database_url


@pytest.fixture(scope="session")
def integration_database_url() -> URL:
    """Validate the explicit target before any fixture opens a connection."""
    return validate_integration_database_url(
        os.environ.get("INTEGRATION_DATABASE_URL"),
        application_database_url=os.environ.get("DEVELOPMENT_DATABASE_URL"),
        is_ci=os.environ.get("CI", "").lower() == "true",
    )


@pytest.fixture(scope="session")
def migrated_database(integration_database_url: URL) -> Iterator[None]:
    """Apply the real Alembic chain once before integration tests run."""
    config = Config("alembic.ini")
    command.upgrade(config, "head")
    yield


@pytest_asyncio.fixture
async def integration_engine(
    migrated_database: None,
    integration_database_url: URL,
) -> AsyncIterator[AsyncEngine]:
    """Provide a disposable engine and clean rows even after test failure."""
    engine = create_async_engine(integration_database_url)
    async with engine.begin() as connection:
        await connection.execute(text("TRUNCATE TABLE movies RESTART IDENTITY"))
    try:
        yield engine
    finally:
        async with engine.begin() as connection:
            await connection.execute(text("TRUNCATE TABLE movies RESTART IDENTITY"))
        await engine.dispose()


@pytest_asyncio.fixture
async def db_session(
    integration_engine: AsyncEngine,
) -> AsyncIterator[AsyncSession]:
    """Provide a real session for non-HTTP application entry points."""
    factory = async_sessionmaker(integration_engine, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(
    integration_engine: AsyncEngine,
) -> AsyncIterator[httpx.AsyncClient]:
    """Call the real FastAPI dependency graph in process over HTTP semantics."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://integration.test",
    ) as http_client:
        yield http_client


@pytest.fixture(scope="session", autouse=True)
def dispose_application_engine_after_suite() -> Iterator[None]:
    """Release the application's global connection pool after the test session."""
    yield
    import asyncio

    asyncio.run(application_engine.dispose())
