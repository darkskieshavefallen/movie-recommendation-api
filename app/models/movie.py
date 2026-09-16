from sqlalchemy import CheckConstraint, String, Text, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Movie(Base):
    """ORM model for movies."""

    __tablename__ = "movies"
    __table_args__ = (
        CheckConstraint(
            "length(btrim(title)) BETWEEN 1 AND 255",
            name="ck_movies_title_length",
        ),
        CheckConstraint(
            "release_year BETWEEN 1888 AND 2100",
            name="ck_movies_release_year_range",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    release_year: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    genres: Mapped[list[str]] = mapped_column(
        ARRAY(String(50)),
        nullable=False,
        default=list,
        server_default=text("'{}'::character varying[]"),
    )
