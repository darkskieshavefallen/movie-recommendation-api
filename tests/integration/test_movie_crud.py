"""Movie API tests through the real PostgreSQL persistence boundary."""

import httpx
import pytest

pytestmark = pytest.mark.integration


async def test_movie_crud_persists_normalized_values(
    client: httpx.AsyncClient,
) -> None:
    create_response = await client.post(
        "/movies/",
        json={
            "title": "Integration Horizon",
            "release_year": 2007,
            "description": "Stored through the complete stack.",
            "genres": [" Science   Fiction ", "DRAMA"],
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    movie_id = created["id"]
    assert created == {
        "id": movie_id,
        "title": "Integration Horizon",
        "release_year": 2007,
        "description": "Stored through the complete stack.",
        "genres": ["drama", "science fiction"],
    }

    get_response = await client.get(f"/movies/{movie_id}")
    list_response = await client.get("/movies/")

    assert get_response.status_code == 200
    assert get_response.json() == created
    assert list_response.status_code == 200
    assert list_response.json() == [created]

    update_response = await client.put(
        f"/movies/{movie_id}",
        json={
            "title": "Integration Horizon: Revised",
            "release_year": 2009,
            "description": None,
            "genres": [" Thriller ", "Drama"],
        },
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated == {
        "id": movie_id,
        "title": "Integration Horizon: Revised",
        "release_year": 2009,
        "description": None,
        "genres": ["drama", "thriller"],
    }
    assert (await client.get(f"/movies/{movie_id}")).json() == updated

    delete_response = await client.delete(f"/movies/{movie_id}")

    assert delete_response.status_code == 204
    assert (await client.get(f"/movies/{movie_id}")).status_code == 404
    assert (await client.get("/movies/")).json() == []


async def test_unknown_writes_rollback_without_changing_other_movies(
    client: httpx.AsyncClient,
) -> None:
    create_response = await client.post(
        "/movies/",
        json={
            "title": "Rollback Witness",
            "release_year": 2011,
            "description": "Must remain unchanged.",
            "genres": ["drama"],
        },
    )
    original = create_response.json()

    unknown_update = await client.put(
        "/movies/999999",
        json={
            "title": "Should Not Exist",
            "release_year": 2025,
            "description": None,
            "genres": ["thriller"],
        },
    )
    unknown_delete = await client.delete("/movies/999999")

    assert unknown_update.status_code == 404
    assert unknown_delete.status_code == 404
    assert (await client.get(f"/movies/{original['id']}")).json() == original
    assert (await client.get("/movies/")).json() == [original]


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        (
            "POST",
            "/movies/",
            {
                "title": "Duplicate genres",
                "release_year": 2000,
                "genres": ["Drama", " drama "],
            },
        ),
        (
            "PUT",
            "/movies/0",
            {
                "title": "Invalid identifier",
                "release_year": 2000,
                "genres": [],
            },
        ),
        (
            "POST",
            "/movies/",
            {"title": "   ", "release_year": 2000, "genres": []},
        ),
        (
            "POST",
            "/movies/",
            {"title": "x" * 256, "release_year": 2000, "genres": []},
        ),
        (
            "POST",
            "/movies/",
            {"title": "Too early", "release_year": 1887, "genres": []},
        ),
        (
            "POST",
            "/movies/",
            {"title": "Too late", "release_year": 2101, "genres": []},
        ),
    ],
)
async def test_invalid_movie_requests_do_not_persist_rows(
    client: httpx.AsyncClient,
    method: str,
    path: str,
    payload: dict[str, object],
) -> None:
    response = await client.request(method, path, json=payload)

    assert response.status_code == 422
    assert (await client.get("/movies/")).json() == []


async def test_movie_list_pagination_has_stable_id_order(
    client: httpx.AsyncClient,
) -> None:
    """Offset and limit operate on an explicit ascending local-ID order."""
    created = []
    for title in ["Third alphabetically", "First alphabetically", "Middle"]:
        response = await client.post(
            "/movies/",
            json={"title": title, "release_year": 2000, "genres": []},
        )
        assert response.status_code == 201
        created.append(response.json())

    first_page = (await client.get("/movies/?offset=0&limit=2")).json()
    second_page = (await client.get("/movies/?offset=2&limit=2")).json()

    assert [movie["id"] for movie in first_page] == [
        created[0]["id"],
        created[1]["id"],
    ]
    assert [movie["id"] for movie in second_page] == [created[2]["id"]]


async def test_local_core_and_disabled_external_catalog_coexist(
    client: httpx.AsyncClient,
) -> None:
    """Local health and catalog remain available while TMDB is disabled."""
    health = await client.get("/health")
    external = await client.get("/external/movies/search?query=Alien")

    assert health.status_code == 200
    assert external.status_code == 503
    assert external.json() == {"detail": "External movie catalog is disabled."}
