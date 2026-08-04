from pydantic import BaseModel, ConfigDict


class MovieCreate(BaseModel):
    """Schema for creating a movie."""

    title: str
    release_year: int
    description: str | None = None


class MovieUpdate(BaseModel):
    """Schema for updating a movie."""

    title: str
    release_year: int
    description: str | None = None


class MovieRead(BaseModel):
    """Schema for reading movie data."""

    id: int
    title: str
    release_year: int
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)