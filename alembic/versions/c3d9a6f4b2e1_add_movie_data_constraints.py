"""add movie data constraints

Revision ID: c3d9a6f4b2e1
Revises: 8f3a2d7c1b4e
Create Date: 2026-09-16 22:00:00.000000

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d9a6f4b2e1"
down_revision: str | Sequence[str] | None = "8f3a2d7c1b4e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Reject blank titles and release years outside the public API range."""
    op.create_check_constraint(
        "ck_movies_title_length",
        "movies",
        "length(btrim(title)) BETWEEN 1 AND 255",
    )
    op.create_check_constraint(
        "ck_movies_release_year_range",
        "movies",
        "release_year BETWEEN 1888 AND 2100",
    )


def downgrade() -> None:
    """Remove the movie value constraints."""
    op.drop_constraint(
        "ck_movies_release_year_range",
        "movies",
        type_="check",
    )
    op.drop_constraint(
        "ck_movies_title_length",
        "movies",
        type_="check",
    )
