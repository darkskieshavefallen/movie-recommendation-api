"""Unit tests for MovieService."""

from unittest.mock import AsyncMock, Mock

import pytest

from app.core.exceptions import MovieNotFoundError
from app.models.movie import Movie
from app.repositories.movie import MovieRepository
from app.schemas.movie import MovieCreate, MovieRead, MovieUpdate
from app.services.movie import MovieService


@pytest.fixture
def mock_repository():
    """Create a mock MovieRepository."""
    return Mock(spec=MovieRepository)


@pytest.fixture
def mock_session():
    """Create a mock AsyncSession."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def movie_service(mock_repository, mock_session):
    """Create a MovieService instance with mocked dependencies."""
    return MovieService(repository=mock_repository, session=mock_session)


# Tests for create_movie()


async def test_create_movie_success(movie_service, mock_repository, mock_session):
    """Test successful movie creation."""
    # Arrange
    movie_data = MovieCreate(
        title="The Matrix",
        release_year=1999,
        description="A hacker discovers reality is a simulation",
    )

    orm_movie = Movie(
        id=1,
        title="The Matrix",
        release_year=1999,
        description="A hacker discovers reality is a simulation",
    )

    mock_repository.add = AsyncMock(return_value=orm_movie)

    # Act
    result = await movie_service.create_movie(movie_data)

    # Assert
    assert isinstance(result, MovieRead)
    assert result.title == "The Matrix"
    assert result.release_year == 1999
    assert result.description == "A hacker discovers reality is a simulation"

    mock_repository.add.assert_awaited_once_with(
        title="The Matrix",
        release_year=1999,
        description="A hacker discovers reality is a simulation",
    )
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(orm_movie)
    mock_session.rollback.assert_not_awaited()


async def test_create_movie_rollback_on_error(
    movie_service, mock_repository, mock_session
):
    """Test that rollback is called when repository raises an exception."""
    # Arrange
    movie_data = MovieCreate(
        title="The Matrix",
        release_year=1999,
        description="A hacker discovers reality is a simulation",
    )

    mock_repository.add = AsyncMock(side_effect=Exception("Database error"))

    # Act & Assert
    with pytest.raises(Exception, match="Database error"):
        await movie_service.create_movie(movie_data)

    mock_repository.add.assert_awaited_once()
    mock_session.commit.assert_not_awaited()
    mock_session.refresh.assert_not_awaited()
    mock_session.rollback.assert_awaited_once()


# Tests for get_movie()


async def test_get_movie_found(movie_service, mock_repository, mock_session):
    """Test retrieving an existing movie."""
    # Arrange
    orm_movie = Movie(
        id=1,
        title="The Matrix",
        release_year=1999,
        description="A hacker discovers reality is a simulation",
    )

    mock_repository.get_by_id = AsyncMock(return_value=orm_movie)

    # Act
    result = await movie_service.get_movie(movie_id=1)

    # Assert
    assert isinstance(result, MovieRead)
    assert result.id == 1
    assert result.title == "The Matrix"

    mock_repository.get_by_id.assert_awaited_once_with(1)
    # Read-only operation should not modify transaction
    mock_session.commit.assert_not_awaited()
    mock_session.rollback.assert_not_awaited()
    mock_session.refresh.assert_not_awaited()


async def test_get_movie_not_found(movie_service, mock_repository, mock_session):
    """Test retrieving a non-existent movie raises MovieNotFoundError."""
    # Arrange
    mock_repository.get_by_id = AsyncMock(return_value=None)

    # Act & Assert
    with pytest.raises(MovieNotFoundError) as exc_info:
        await movie_service.get_movie(movie_id=999)

    assert exc_info.value.movie_id == 999
    mock_repository.get_by_id.assert_awaited_once_with(999)
    # Read-only operation should not modify transaction even on error
    mock_session.commit.assert_not_awaited()
    mock_session.rollback.assert_not_awaited()
    mock_session.refresh.assert_not_awaited()


# Tests for list_movies()


async def test_list_movies_success(movie_service, mock_repository, mock_session):
    """Test listing movies with default pagination."""
    # Arrange
    orm_movies = [
        Movie(id=1, title="The Matrix", release_year=1999, description="Sci-fi"),
        Movie(id=2, title="Inception", release_year=2010, description="Dream heist"),
    ]

    mock_repository.get_all = AsyncMock(return_value=orm_movies)

    # Act
    result = await movie_service.list_movies()

    # Assert
    assert len(result) == 2
    assert all(isinstance(movie, MovieRead) for movie in result)
    assert result[0].title == "The Matrix"
    assert result[1].title == "Inception"

    mock_repository.get_all.assert_awaited_once_with(offset=0, limit=100)
    # Read-only operation should not modify transaction
    mock_session.commit.assert_not_awaited()
    mock_session.rollback.assert_not_awaited()
    mock_session.refresh.assert_not_awaited()


async def test_list_movies_with_pagination(movie_service, mock_repository, mock_session):
    """Test listing movies with custom pagination."""
    # Arrange
    orm_movies = [
        Movie(id=3, title="Interstellar", release_year=2014, description="Space"),
    ]

    mock_repository.get_all = AsyncMock(return_value=orm_movies)

    # Act
    result = await movie_service.list_movies(offset=10, limit=5)

    # Assert
    assert len(result) == 1
    assert result[0].title == "Interstellar"

    mock_repository.get_all.assert_awaited_once_with(offset=10, limit=5)
    # Read-only operation should not modify transaction
    mock_session.commit.assert_not_awaited()
    mock_session.rollback.assert_not_awaited()
    mock_session.refresh.assert_not_awaited()


async def test_list_movies_empty(movie_service, mock_repository, mock_session):
    """Test listing movies when no movies exist."""
    # Arrange
    mock_repository.get_all = AsyncMock(return_value=[])

    # Act
    result = await movie_service.list_movies()

    # Assert
    assert result == []
    mock_repository.get_all.assert_awaited_once_with(offset=0, limit=100)
    # Read-only operation should not modify transaction
    mock_session.commit.assert_not_awaited()
    mock_session.rollback.assert_not_awaited()
    mock_session.refresh.assert_not_awaited()


# Tests for update_movie()


async def test_update_movie_success(movie_service, mock_repository, mock_session):
    """Test successful movie update."""
    # Arrange
    movie_data = MovieUpdate(
        title="The Matrix Reloaded",
        release_year=2003,
        description="Updated description",
    )

    orm_movie = Movie(
        id=1,
        title="The Matrix Reloaded",
        release_year=2003,
        description="Updated description",
    )

    mock_repository.update = AsyncMock(return_value=orm_movie)

    # Act
    result = await movie_service.update_movie(movie_id=1, movie=movie_data)

    # Assert
    assert isinstance(result, MovieRead)
    assert result.title == "The Matrix Reloaded"

    mock_repository.update.assert_awaited_once_with(
        movie_id=1,
        title="The Matrix Reloaded",
        release_year=2003,
        description="Updated description",
    )
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(orm_movie)
    mock_session.rollback.assert_not_awaited()


async def test_update_movie_not_found(movie_service, mock_repository, mock_session):
    """Test updating a non-existent movie raises MovieNotFoundError."""
    # Arrange
    movie_data = MovieUpdate(
        title="The Matrix Reloaded",
        release_year=2003,
        description="Updated description",
    )

    mock_repository.update = AsyncMock(return_value=None)

    # Act & Assert
    with pytest.raises(MovieNotFoundError) as exc_info:
        await movie_service.update_movie(movie_id=999, movie=movie_data)

    assert exc_info.value.movie_id == 999
    mock_repository.update.assert_awaited_once()
    mock_session.commit.assert_not_awaited()
    mock_session.rollback.assert_awaited_once()


async def test_update_movie_rollback_on_error(
    movie_service, mock_repository, mock_session
):
    """Test that rollback is called when update fails."""
    # Arrange
    movie_data = MovieUpdate(
        title="The Matrix Reloaded",
        release_year=2003,
        description="Updated description",
    )

    mock_repository.update = AsyncMock(side_effect=Exception("Database error"))

    # Act & Assert
    with pytest.raises(Exception, match="Database error"):
        await movie_service.update_movie(movie_id=1, movie=movie_data)

    mock_repository.update.assert_awaited_once()
    mock_session.commit.assert_not_awaited()
    mock_session.rollback.assert_awaited_once()


# Tests for delete_movie()


async def test_delete_movie_success(movie_service, mock_repository, mock_session):
    """Test successful movie deletion."""
    # Arrange
    mock_repository.delete = AsyncMock(return_value=True)

    # Act
    await movie_service.delete_movie(movie_id=1)

    # Assert
    mock_repository.delete.assert_awaited_once_with(1)
    mock_session.commit.assert_awaited_once()
    mock_session.rollback.assert_not_awaited()


async def test_delete_movie_not_found(movie_service, mock_repository, mock_session):
    """Test deleting a non-existent movie raises MovieNotFoundError."""
    # Arrange
    mock_repository.delete = AsyncMock(return_value=False)

    # Act & Assert
    with pytest.raises(MovieNotFoundError) as exc_info:
        await movie_service.delete_movie(movie_id=999)

    assert exc_info.value.movie_id == 999
    mock_repository.delete.assert_awaited_once_with(999)
    mock_session.commit.assert_not_awaited()
    mock_session.rollback.assert_awaited_once()


async def test_delete_movie_rollback_on_error(
    movie_service, mock_repository, mock_session
):
    """Test that rollback is called when delete fails."""
    # Arrange
    mock_repository.delete = AsyncMock(side_effect=Exception("Database error"))

    # Act & Assert
    with pytest.raises(Exception, match="Database error"):
        await movie_service.delete_movie(movie_id=1)

    mock_repository.delete.assert_awaited_once()
    mock_session.commit.assert_not_awaited()
    mock_session.rollback.assert_awaited_once()
