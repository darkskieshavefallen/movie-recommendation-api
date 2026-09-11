"""Provider-independent schemas for external movie search."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, StrictInt, StringConstraints

SearchQuery = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=200),
]
RequiredText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
]


class ExternalMovieSearchQuery(BaseModel):
    """Validated input for an external movie search."""

    query: SearchQuery

    model_config = ConfigDict(extra="forbid")


class ExternalMovieSearchResult(BaseModel):
    """Application-owned representation of an external movie match."""

    external_id: RequiredText
    title: RequiredText
    release_year: StrictInt | None = None
    description: RequiredText | None = None

    model_config = ConfigDict(extra="forbid")


class ExternalMovieSearchResponse(BaseModel):
    """Stable response envelope for external movie search results."""

    query: SearchQuery
    results: list[ExternalMovieSearchResult]

    model_config = ConfigDict(extra="forbid")
