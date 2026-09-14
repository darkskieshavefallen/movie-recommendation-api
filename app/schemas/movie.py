from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

MAX_GENRES = 10
MAX_GENRE_LENGTH = 50


class MovieFields(BaseModel):
    """Fields shared by movie write and read schemas."""

    title: str
    release_year: int
    description: str | None = None
    genres: list[str] = Field(default_factory=list, max_length=MAX_GENRES)

    @field_validator("genres", mode="before")
    @classmethod
    def normalize_genres(cls, value: Any) -> Any:
        """Normalize genre strings and reject ambiguous input."""
        if not isinstance(value, list):
            return value
        if any(not isinstance(genre, str) for genre in value):
            return value

        normalized_genres: list[str] = []
        for genre in value:
            normalized_genre = " ".join(genre.split()).lower()
            if not normalized_genre:
                raise ValueError("genres must not be blank")
            if len(normalized_genre) > MAX_GENRE_LENGTH:
                raise ValueError(
                    f"genres must contain at most {MAX_GENRE_LENGTH} characters"
                )

            normalized_genres.append(normalized_genre)

        if len(set(normalized_genres)) != len(normalized_genres):
            raise ValueError("genres must be unique after normalization")

        return sorted(normalized_genres)


class MovieCreate(MovieFields):
    """Schema for creating a movie."""


class MovieUpdate(MovieFields):
    """Schema for updating a movie."""


class MovieRead(MovieFields):
    """Schema for reading movie data."""

    id: int

    model_config = ConfigDict(from_attributes=True)
