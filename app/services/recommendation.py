"""Deterministic recommendation logic for the local movie catalog."""

from app.core.exceptions import MovieNotFoundError
from app.repositories.movie import MovieRepository
from app.schemas.recommendation import (
    DEFAULT_RECOMMENDATION_LIMIT,
    MAX_RECOMMENDATION_LIMIT,
    MIN_RECOMMENDATION_LIMIT,
    MovieRecommendation,
    MovieRecommendations,
)


class RecommendationService:
    """Rank local movies using shared genres and release years."""

    def __init__(self, repository: MovieRepository) -> None:
        """Initialize the service with local database access."""
        self._repository = repository

    async def recommend_movies(
        self,
        source_movie_id: int,
        limit: int = DEFAULT_RECOMMENDATION_LIMIT,
    ) -> MovieRecommendations:
        """Return deterministic, explainable recommendations for one movie."""
        if not MIN_RECOMMENDATION_LIMIT <= limit <= MAX_RECOMMENDATION_LIMIT:
            raise ValueError(
                "recommendation limit must be between "
                f"{MIN_RECOMMENDATION_LIMIT} and {MAX_RECOMMENDATION_LIMIT}"
            )

        source = await self._repository.get_by_id(source_movie_id)
        if source is None:
            raise MovieNotFoundError(source_movie_id)
        if not source.genres:
            return MovieRecommendations(
                source_movie_id=source_movie_id,
                recommendations=[],
            )

        source_genres = set(source.genres)
        ranked: list[tuple[tuple[int, int, int], MovieRecommendation]] = []

        candidates = await self._repository.get_recommendation_candidates(
            source_movie_id
        )
        for candidate in candidates:
            if candidate.id == source_movie_id:
                continue

            matching_genres = sorted(source_genres.intersection(candidate.genres))
            if not matching_genres:
                continue

            recommendation = MovieRecommendation(
                movie_id=candidate.id,
                title=candidate.title,
                release_year=candidate.release_year,
                matching_genres=matching_genres,
            )
            sort_key = (
                -len(matching_genres),
                abs(candidate.release_year - source.release_year),
                candidate.id,
            )
            ranked.append((sort_key, recommendation))

        ranked.sort(key=lambda item: item[0])

        return MovieRecommendations(
            source_movie_id=source_movie_id,
            recommendations=[
                recommendation
                for _, recommendation in ranked[:limit]
            ],
        )
