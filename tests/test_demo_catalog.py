"""Tests for the manually authored demo catalog and its seed service."""

from unittest.mock import AsyncMock, Mock

import pytest

from app.demo_catalog import DEMO_MOVIES, DemoMovie
from app.repositories.movie import MovieRepository
from app.schemas.movie import MovieCreate
from app.services.demo_catalog import DemoCatalogService


def test_demo_catalog_is_small_unique_and_canonical():
    """The bundled local data satisfies the public movie genre contract."""
    identities = {(movie.title, movie.release_year) for movie in DEMO_MOVIES}

    assert 10 <= len(DEMO_MOVIES) <= 20
    assert len(identities) == len(DEMO_MOVIES)

    for movie in DEMO_MOVIES:
        validated = MovieCreate(
            title=movie.title,
            release_year=movie.release_year,
            genres=list(movie.genres),
        )
        assert validated.genres == list(movie.genres)
        assert validated.genres
        assert validated.description is None


@pytest.fixture
def mock_repository():
    """Create a repository mock for the seed service."""
    repository = Mock(spec=MovieRepository)
    repository.get_existing_identities = AsyncMock()
    repository.add = AsyncMock()
    return repository


@pytest.fixture
def mock_session():
    """Create a transaction mock for the seed service."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def seed_service(mock_repository, mock_session):
    """Create the demo catalog seed service."""
    return DemoCatalogService(mock_repository, mock_session)


async def test_seed_creates_only_missing_movies(
    seed_service,
    mock_repository,
    mock_session,
):
    """Existing identities are skipped while missing movies are inserted."""
    existing_movie, new_movie = DEMO_MOVIES[:2]
    mock_repository.get_existing_identities.return_value = {
        (existing_movie.title, existing_movie.release_year)
    }

    result = await seed_service.seed((existing_movie, new_movie))

    assert result.created == 1
    assert result.skipped == 1
    mock_repository.add.assert_awaited_once_with(
        title=new_movie.title,
        release_year=new_movie.release_year,
        description=None,
        genres=list(new_movie.genres),
    )
    mock_session.commit.assert_awaited_once()
    mock_session.rollback.assert_not_awaited()


async def test_seed_rerun_does_not_overwrite_existing_movies(
    seed_service,
    mock_repository,
    mock_session,
):
    """A complete existing catalog is left untouched on a later run."""
    identities = {(movie.title, movie.release_year) for movie in DEMO_MOVIES}
    mock_repository.get_existing_identities.return_value = identities

    result = await seed_service.seed()

    assert result.created == 0
    assert result.skipped == len(DEMO_MOVIES)
    mock_repository.add.assert_not_awaited()
    mock_session.commit.assert_not_awaited()
    mock_session.rollback.assert_not_awaited()


async def test_seed_rolls_back_when_an_insert_fails(
    seed_service,
    mock_repository,
    mock_session,
):
    """The service owns rollback for a failed seed transaction."""
    movie = DemoMovie("Failure case", 2000, ("drama",))
    mock_repository.get_existing_identities.return_value = set()
    mock_repository.add.side_effect = RuntimeError("database error")

    with pytest.raises(RuntimeError, match="database error"):
        await seed_service.seed((movie,))

    mock_session.commit.assert_not_awaited()
    mock_session.rollback.assert_awaited_once()
