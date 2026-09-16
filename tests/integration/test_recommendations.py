"""Local recommendation tests through HTTP and real PostgreSQL."""

import httpx
import pytest

pytestmark = pytest.mark.integration


async def create_movie(
    client: httpx.AsyncClient,
    *,
    title: str,
    release_year: int,
    genres: list[str],
) -> dict[str, object]:
    """Persist one controlled recommendation candidate through the API."""
    response = await client.post(
        "/movies/",
        json={
            "title": title,
            "release_year": release_year,
            "description": None,
            "genres": genres,
        },
    )
    assert response.status_code == 201
    return response.json()


async def test_recommendations_rank_persisted_movies_and_explain_matches(
    client: httpx.AsyncClient,
) -> None:
    source = await create_movie(
        client,
        title="Source Orbit",
        release_year=2000,
        genres=["drama", "science fiction"],
    )
    near_later = await create_movie(
        client,
        title="Near Later",
        release_year=2002,
        genres=["science fiction", "drama"],
    )
    near_earlier = await create_movie(
        client,
        title="Near Earlier",
        release_year=1998,
        genres=["drama", "science fiction"],
    )
    far_match = await create_movie(
        client,
        title="Far Match",
        release_year=2005,
        genres=["drama", "science fiction", "thriller"],
    )
    one_genre = await create_movie(
        client,
        title="One Genre",
        release_year=2001,
        genres=["science fiction"],
    )
    no_match = await create_movie(
        client,
        title="No Match",
        release_year=2000,
        genres=["comedy"],
    )

    response = await client.get(
        f"/movies/{source['id']}/recommendations?limit=20"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["source_movie_id"] == source["id"]
    assert [item["movie_id"] for item in body["recommendations"]] == [
        near_later["id"],
        near_earlier["id"],
        far_match["id"],
        one_genre["id"],
    ]
    assert [item["matching_genres"] for item in body["recommendations"]] == [
        ["drama", "science fiction"],
        ["drama", "science fiction"],
        ["drama", "science fiction"],
        ["science fiction"],
    ]
    returned_ids = {item["movie_id"] for item in body["recommendations"]}
    assert source["id"] not in returned_ids
    assert no_match["id"] not in returned_ids

    limited = await client.get(
        f"/movies/{source['id']}/recommendations?limit=2"
    )
    assert [item["movie_id"] for item in limited.json()["recommendations"]] == [
        near_later["id"],
        near_earlier["id"],
    ]


async def test_recommendations_cover_empty_unknown_and_invalid_requests(
    client: httpx.AsyncClient,
) -> None:
    source = await create_movie(
        client,
        title="Genre-free Source",
        release_year=2000,
        genres=[],
    )
    await create_movie(
        client,
        title="Unrelated Movie",
        release_year=2001,
        genres=["drama"],
    )

    empty_response = await client.get(
        f"/movies/{source['id']}/recommendations"
    )
    unknown_response = await client.get("/movies/999999/recommendations")
    invalid_response = await client.get(
        f"/movies/{source['id']}/recommendations?limit=21"
    )

    assert empty_response.status_code == 200
    assert empty_response.json() == {
        "source_movie_id": source["id"],
        "recommendations": [],
    }
    assert unknown_response.status_code == 404
    assert invalid_response.status_code == 422
