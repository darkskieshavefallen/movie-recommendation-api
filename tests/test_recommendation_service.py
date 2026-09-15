"""Unit tests for deterministic local recommendation ranking."""

from unittest.mock import AsyncMock, Mock

import pytest

from app.core.exceptions import MovieNotFoundError
from app.models.movie import Movie
from app.repositories.movie import MovieRepository
from app.schemas.recommendation import MovieRecommendations
from app.services.recommendation import RecommendationService


def movie(
    movie_id: int,
    title: str,
    release_year: int,
    genres: list[str],
) -> Movie:
    """Build an in-memory local movie for ranking tests."""
    return Movie(
        id=movie_id,
        title=title,
        release_year=release_year,
        description=None,
        genres=genres,
    )


@pytest.fixture
def mock_repository():
    """Create a local movie repository mock."""
    repository = Mock(spec=MovieRepository)
    repository.get_by_id = AsyncMock()
    repository.get_recommendation_candidates = AsyncMock()
    return repository


@pytest.fixture
def recommendation_service(mock_repository):
    """Create the recommendation service."""
    return RecommendationService(mock_repository)


async def test_recommend_movies_applies_every_tie_breaker(
    recommendation_service,
    mock_repository,
):
    """Genre count, year distance, and ID determine the final order."""
    source = movie(10, "Orbit", 2000, ["drama", "science fiction"])
    mock_repository.get_by_id.return_value = source
    mock_repository.get_recommendation_candidates.return_value = [
        movie(30, "Quiet Signal", 2001, ["science fiction"]),
        movie(25, "Far Orbit", 2005, ["drama", "science fiction"]),
        movie(20, "Distant Orbit", 1998, ["drama", "science fiction"]),
        movie(40, "Summer Kitchen", 2000, ["comedy"]),
        movie(15, "Second Orbit", 2002, ["drama", "science fiction"]),
        source,
    ]

    result = await recommendation_service.recommend_movies(10, limit=4)

    assert isinstance(result, MovieRecommendations)
    assert result.source_movie_id == 10
    assert [item.movie_id for item in result.recommendations] == [15, 20, 25, 30]
    assert result.recommendations[0].matching_genres == [
        "drama",
        "science fiction",
    ]
    assert result.recommendations[3].matching_genres == ["science fiction"]
    mock_repository.get_by_id.assert_awaited_once_with(10)
    mock_repository.get_recommendation_candidates.assert_awaited_once_with(10)


async def test_recommend_movies_applies_limit(
    recommendation_service,
    mock_repository,
):
    """Only the requested number of highest-ranked candidates is returned."""
    source = movie(1, "Source", 2000, ["drama"])
    mock_repository.get_by_id.return_value = source
    mock_repository.get_recommendation_candidates.return_value = [
        movie(4, "Fourth", 2003, ["drama"]),
        movie(2, "Second", 2001, ["drama"]),
        movie(3, "Third", 2002, ["drama"]),
    ]

    result = await recommendation_service.recommend_movies(1, limit=2)

    assert [item.movie_id for item in result.recommendations] == [2, 3]


async def test_recommend_movies_returns_empty_when_source_has_no_genres(
    recommendation_service,
    mock_repository,
):
    """A source without genres needs no candidate query."""
    mock_repository.get_by_id.return_value = movie(1, "Source", 2000, [])

    result = await recommendation_service.recommend_movies(1)

    assert result.recommendations == []
    mock_repository.get_recommendation_candidates.assert_not_awaited()


async def test_recommend_movies_returns_empty_when_nothing_matches(
    recommendation_service,
    mock_repository,
):
    """Candidates without a shared genre are excluded."""
    mock_repository.get_by_id.return_value = movie(1, "Source", 2000, ["drama"])
    mock_repository.get_recommendation_candidates.return_value = [
        movie(2, "Comedy", 2000, ["comedy"]),
        movie(3, "No genres", 2000, []),
    ]

    result = await recommendation_service.recommend_movies(1)

    assert result.recommendations == []


async def test_recommend_movies_raises_for_unknown_source(
    recommendation_service,
    mock_repository,
):
    """The existing domain error is preserved for a missing source movie."""
    mock_repository.get_by_id.return_value = None

    with pytest.raises(MovieNotFoundError) as exc_info:
        await recommendation_service.recommend_movies(999)

    assert exc_info.value.movie_id == 999
    mock_repository.get_recommendation_candidates.assert_not_awaited()


@pytest.mark.parametrize("limit", [0, 21])
async def test_recommend_movies_rejects_out_of_range_limit(
    recommendation_service,
    mock_repository,
    limit,
):
    """Direct service callers cannot bypass the public 1–20 bound."""
    with pytest.raises(ValueError, match="between 1 and 20"):
        await recommendation_service.recommend_movies(1, limit=limit)

    mock_repository.get_by_id.assert_not_awaited()
