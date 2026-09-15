"""add genres to movies

Revision ID: 8f3a2d7c1b4e
Revises: 474e3311e20a
Create Date: 2026-09-14 22:20:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "8f3a2d7c1b4e"
down_revision: str | Sequence[str] | None = "474e3311e20a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add normalized local genres with an empty value for existing movies."""
    op.add_column(
        "movies",
        sa.Column(
            "genres",
            postgresql.ARRAY(sa.String(length=50)),
            server_default=sa.text("'{}'::character varying[]"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Remove local genres from movies."""
    op.drop_column("movies", "genres")
