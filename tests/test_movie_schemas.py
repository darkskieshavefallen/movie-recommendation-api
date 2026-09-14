"""Tests for local movie schemas."""

import pytest
from pydantic import ValidationError

from app.models.movie import Movie
from app.schemas.movie import MovieCreate, MovieRead, MovieUpdate


@pytest.mark.parametrize("schema_type", [MovieCreate, MovieUpdate])
def test_movie_write_schema_normalizes_and_sorts_genres(schema_type):
    """Create and update requests share canonical genre normalization."""
    movie = schema_type(
        title="Orbit",
        release_year=2000,
        genres=[" Science   Fiction ", "DRAMA"],
    )

    assert movie.genres == ["drama", "science fiction"]


@pytest.mark.parametrize("schema_type", [MovieCreate, MovieUpdate])
def test_movie_write_schema_defaults_to_empty_genres(schema_type):
    """Requests written before genres existed remain valid."""
    movie = schema_type(title="Orbit", release_year=2000)

    assert movie.genres == []


@pytest.mark.parametrize(
    ("genres", "error"),
    [
        (["   "], "genres must not be blank"),
        (["Drama", " drama "], "genres must be unique after normalization"),
        (["x" * 51], "genres must contain at most 50 characters"),
        (["genre-" + str(index) for index in range(11)], "at most 10 items"),
        ([1], "valid string"),
    ],
)
def test_movie_write_schema_rejects_invalid_genres(genres, error):
    """Genre validation rejects ambiguous or excessive values."""
    with pytest.raises(ValidationError, match=error):
        MovieCreate(title="Orbit", release_year=2000, genres=genres)


def test_movie_read_supports_migrated_existing_movie_without_genres():
    """A pre-existing row is represented by the migration's empty array."""
    orm_movie = Movie(
        id=1,
        title="Existing movie",
        release_year=1995,
        description=None,
        genres=[],
    )

    movie = MovieRead.model_validate(orm_movie)

    assert movie.genres == []
