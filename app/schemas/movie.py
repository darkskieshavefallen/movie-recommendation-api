from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

MAX_GENRES = 10
MAX_GENRE_LENGTH = 50
MAX_TITLE_LENGTH = 255
MIN_RELEASE_YEAR = 1888
MAX_RELEASE_YEAR = 2100


class MovieFields(BaseModel):
    """Fields shared by movie write and read schemas."""

    title: str = Field(min_length=1, max_length=MAX_TITLE_LENGTH)
    release_year: int = Field(ge=MIN_RELEASE_YEAR, le=MAX_RELEASE_YEAR)
    description: str | None = None
    genres: list[str] = Field(default_factory=list, max_length=MAX_GENRES)

    @field_validator("title", mode="before")
    @classmethod
    def normalize_title(cls, value: Any) -> Any:
        """Trim a string title before enforcing its public length bounds."""
        return value.strip() if isinstance(value, str) else value

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
