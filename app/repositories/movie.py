from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.movie import Movie


class MovieRepository:
    """Repository for working with Movie entities."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session."""
        self.session = session

    async def add(
        self,
        title: str,
        release_year: int,
        description: str | None = None,
    ) -> Movie:
        """
        Create a new movie.

        The method only adds the object to the current transaction.
        It does not commit the transaction.
        """
        movie = Movie(
            title=title,
            release_year=release_year,
            description=description,
        )

        self.session.add(movie)
        await self.session.flush()

        return movie

    async def get_by_id(self, movie_id: int) -> Movie | None:
        """
        Retrieve a movie by its identifier.

        Returns:
            Movie if found, otherwise None.
        """
        result = await self.session.execute(
            select(Movie).where(Movie.id == movie_id)
        )

        return result.scalar_one_or_none()

    async def update(
        self,
        movie_id: int,
        title: str,
        release_year: int,
        description: str | None = None,
    ) -> Movie | None:
        """
        Update an existing movie.

        The method only updates the object in the current transaction.
        It does not commit the transaction.

        Args:
            movie_id: The identifier of the movie to update.
            title: New title.
            release_year: New release year.
            description: New description.

        Returns:
            Updated Movie if found, otherwise None.
        """
        movie = await self.get_by_id(movie_id)

        if movie is None:
            return None

        movie.title = title
        movie.release_year = release_year
        movie.description = description

        await self.session.flush()

        return movie

    async def delete(self, movie_id: int) -> bool:
        """
        Delete an existing movie.

        The method only deletes the object in the current transaction.
        It does not commit the transaction.

        Args:
            movie_id: The identifier of the movie to delete.

        Returns:
            True if the movie was found and deleted, False otherwise.
        """
        movie = await self.get_by_id(movie_id)

        if movie is None:
            return False

        await self.session.delete(movie)
        await self.session.flush()

        return True

    async def get_all(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Movie]:
        """
        Retrieve a paginated list of movies.

        Args:
            offset: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of Movie ORM objects.
        """
        result = await self.session.execute(
            select(Movie)
            .offset(offset)
            .limit(limit)
        )

        return list(result.scalars().all())