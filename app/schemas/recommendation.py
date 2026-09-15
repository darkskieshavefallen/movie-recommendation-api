"""Public data shapes produced by local recommendation ranking."""

from pydantic import BaseModel, Field

DEFAULT_RECOMMENDATION_LIMIT = 5
MIN_RECOMMENDATION_LIMIT = 1
MAX_RECOMMENDATION_LIMIT = 20


class MovieRecommendation(BaseModel):
    """One ranked local movie with an explanation of its match."""

    movie_id: int
    title: str
    release_year: int
    matching_genres: list[str] = Field(min_length=1, max_length=10)


class MovieRecommendations(BaseModel):
    """Recommendations associated with one local source movie."""

    source_movie_id: int
    recommendations: list[MovieRecommendation]
