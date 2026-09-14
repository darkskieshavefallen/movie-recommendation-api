"""Tests for provider-independent external movie search schemas."""

import pytest
from pydantic import ValidationError

from app.schemas.external_movie import (
    ExternalMovieSearchQuery,
    ExternalMovieSearchResponse,
    ExternalMovieSearchResult,
)


def movie_result(external_id: str = "348") -> ExternalMovieSearchResult:
    """Build a valid normalized result for response-shape tests."""
    return ExternalMovieSearchResult(
        external_id=external_id,
        title="Alien",
        release_year=1979,
        description="A space crew encounters a hostile life-form.",
    )


def test_search_query_is_trimmed():
    """A valid search term is normalized before it reaches a provider."""
    search = ExternalMovieSearchQuery(query="  Alien  ")

    assert search.query == "Alien"


@pytest.mark.parametrize("query", ["", "   ", "x" * 201])
def test_search_query_rejects_empty_or_overlong_values(query):
    """Invalid terms fail before an external request can be made."""
    with pytest.raises(ValidationError):
        ExternalMovieSearchQuery(query=query)


def test_search_result_accepts_missing_optional_provider_data():
    """A movie remains valid when the provider omits date and description."""
    result = ExternalMovieSearchResult(external_id="348", title="Alien")

    assert result.release_year is None
    assert result.description is None


def test_search_result_rejects_malformed_optional_data():
    """Present provider data must already have the normalized application type."""
    with pytest.raises(ValidationError):
        ExternalMovieSearchResult(
            external_id="348",
            title="Alien",
            release_year="1979",
        )


@pytest.mark.parametrize("field", ["external_id", "title"])
def test_search_result_rejects_missing_required_data(field):
    """Every normalized result requires an identifier and a title."""
    data = {"external_id": "348", "title": "Alien"}
    data.pop(field)

    with pytest.raises(ValidationError):
        ExternalMovieSearchResult.model_validate(data)


@pytest.mark.parametrize("field", ["external_id", "title"])
def test_search_result_rejects_blank_required_data(field):
    """Whitespace cannot satisfy a required application field."""
    data = {"external_id": "348", "title": "Alien", field: "   "}

    with pytest.raises(ValidationError):
        ExternalMovieSearchResult.model_validate(data)


def test_search_result_rejects_provider_specific_fields():
    """Raw provider details cannot leak into the application contract."""
    with pytest.raises(ValidationError):
        ExternalMovieSearchResult(
            external_id="348",
            title="Alien",
            popularity=123.4,
        )


@pytest.mark.parametrize("result_count", [0, 1, 3])
def test_search_response_has_one_shape_for_any_result_count(result_count):
    """Zero, one, and many matches share the same response envelope."""
    response = ExternalMovieSearchResponse(
        query="  Alien  ",
        results=[movie_result(str(index)) for index in range(result_count)],
    )

    payload = response.model_dump()
    assert payload["query"] == "Alien"
    assert isinstance(payload["results"], list)
    assert len(payload["results"]) == result_count
