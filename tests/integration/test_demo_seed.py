"""Demo catalog seed tests against real PostgreSQL storage."""

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.demo_catalog import DEMO_MOVIES
from app.repositories.movie import MovieRepository
from app.services.demo_catalog import DemoCatalogService

pytestmark = pytest.mark.integration


async def test_demo_seed_is_idempotent_and_preserves_user_edits(
    client: httpx.AsyncClient,
    db_session: AsyncSession,
) -> None:
    service = DemoCatalogService(
        repository=MovieRepository(db_session),
        session=db_session,
    )

    first_result = await service.seed()
    first_catalog = (await client.get("/movies/?limit=100")).json()

    assert first_result.created == len(DEMO_MOVIES)
    assert first_result.skipped == 0
    assert len(first_catalog) == len(DEMO_MOVIES)
    assert {
        (movie["title"], movie["release_year"], tuple(movie["genres"]))
        for movie in first_catalog
    } == {
        (movie.title, movie.release_year, movie.genres)
        for movie in DEMO_MOVIES
    }
    assert all(movie["description"] is None for movie in first_catalog)

    second_result = await service.seed()

    assert second_result.created == 0
    assert second_result.skipped == len(DEMO_MOVIES)
    assert len((await client.get("/movies/?limit=100")).json()) == len(DEMO_MOVIES)

    orbit = next(movie for movie in first_catalog if movie["title"] == "Orbit of Glass")
    edited_payload = {
        "title": orbit["title"],
        "release_year": orbit["release_year"],
        "description": "A user-authored description.",
        "genres": ["Drama", "Mystery"],
    }
    update_response = await client.put(
        f"/movies/{orbit['id']}",
        json=edited_payload,
    )

    assert update_response.status_code == 200
    third_result = await service.seed()
    persisted_edit = (await client.get(f"/movies/{orbit['id']}")).json()

    assert third_result.created == 0
    assert third_result.skipped == len(DEMO_MOVIES)
    assert persisted_edit["description"] == "A user-authored description."
    assert persisted_edit["genres"] == ["drama", "mystery"]
    assert len((await client.get("/movies/?limit=100")).json()) == len(DEMO_MOVIES)
