# Local recommendation contract

Updated: 2026-09-14.

## Scope

Sprint 18 adds deterministic recommendations between movies stored in the application's own PostgreSQL catalog. The feature uses manually curated local genres and release years. It does not call TMDB, import TMDB results, store TMDB identifiers or content, or use an ML/AI model.

The rule is intentionally small enough to inspect and test. A recommendation explains which genres matched, and the same database state and request always produce the same order.

## Public operation

The planned endpoint is:

```text
GET /movies/{movie_id}/recommendations?limit=5
```

`movie_id` is the positive integer identifier of an existing local movie. `limit` is optional, defaults to `5`, and must be an integer from `1` through `20`. FastAPI rejects an invalid path identifier or limit with `422 Unprocessable Entity` before recommendation logic runs.

A successful response has this application-owned shape:

```json
{
  "source_movie_id": 10,
  "recommendations": [
    {
      "movie_id": 15,
      "title": "Second Orbit",
      "release_year": 2002,
      "matching_genres": [
        "drama",
        "science fiction"
      ]
    }
  ]
}
```

`movie_id` values in this response are local PostgreSQL movie identifiers. `matching_genres` contains the canonical genres shared with the source movie and explains why the candidate was included. The endpoint reads local records only and does not modify them.

## Local genre representation

Movie create, read, and update contracts will expose `genres` as a JSON array of canonical strings. An empty array is valid and is the default for existing movies and requests that omit the field.

Genre input follows these rules:

1. A movie may contain at most 10 genres.
2. Each genre must be a string containing 1–50 characters after normalization.
3. Normalization trims leading and trailing whitespace, collapses consecutive internal whitespace to one space, and converts text to lowercase.
4. The final list is sorted lexicographically so storage, responses, and comparisons are deterministic.
5. Blank values and non-string values are rejected.
6. Values that become duplicates after normalization are rejected rather than silently discarded. For example, `"Drama"` and `" drama "` conflict.

Examples:

```text
[" Science   Fiction ", "Drama"] -> ["drama", "science fiction"]
[]                              -> []
["Drama", " drama "]           -> validation error
["   "]                         -> validation error
```

These genres are authored for the local catalog. They are not copied from a TMDB response. The database representation is an implementation detail for ANT-26; it must preserve this public list contract and give every pre-existing row an empty list.

## Ranking rule

For an existing source movie, the service loads local candidates and applies these steps in order:

1. Exclude the source movie itself.
2. Compute the intersection between the source and candidate genre sets.
3. Exclude candidates with no shared genre.
4. Sort by the number of shared genres, descending.
5. When that count is equal, sort by the absolute release-year difference from the source, ascending.
6. When both values are equal, sort by local movie ID, ascending.
7. Return the first `limit` candidates.

Release-year proximity never outweighs genre overlap. The local ID is a stable, unique final tie-breaker; database row order and title collation cannot change the result.

## Defined outcomes

| Situation | Result |
| --- | --- |
| Source movie exists and has matches | `200 OK` with ranked recommendations |
| Source movie does not exist | Existing `MovieNotFoundError` contract: `404 Not Found` |
| Source movie has no genres | `200 OK` with `"recommendations": []` |
| No candidate shares a genre | `200 OK` with `"recommendations": []` |
| Source movie is the only matching record | The source is excluded; the list is empty |
| Fewer matches exist than requested | Return every eligible match without padding |
| `limit` is missing | Use `5` |
| `limit` is below 1, above 20, or not an integer | `422 Unprocessable Entity` |

## Worked ranking example

Assume the local database contains these manually authored records:

| ID | Title | Year | Genres |
| --- | --- | --- | --- |
| 10 | Orbit | 2000 | `drama`, `science fiction` |
| 20 | Distant Orbit | 1998 | `drama`, `science fiction` |
| 15 | Second Orbit | 2002 | `drama`, `science fiction` |
| 25 | Far Orbit | 2005 | `drama`, `science fiction` |
| 30 | Quiet Signal | 2001 | `science fiction` |
| 40 | Summer Kitchen | 2000 | `comedy` |

For source movie `10`:

| Candidate | Shared genres | Shared count | Year difference | Decision |
| --- | --- | --- | --- | --- |
| 15 | `drama`, `science fiction` | 2 | 2 | First: tied signals, lower ID |
| 20 | `drama`, `science fiction` | 2 | 2 | Second: tied signals, higher ID |
| 25 | `drama`, `science fiction` | 2 | 5 | Third: same shared count, larger year difference |
| 30 | `science fiction` | 1 | 1 | Fourth: fewer shared genres despite a closer year |
| 40 | none | 0 | 0 | Excluded |

The request below returns candidates `15`, `20`, and `25` in that order:

```text
GET /movies/10/recommendations?limit=3
```

Candidates `15`, `20`, and `25` have the same shared-genre count, so the year difference places `25` after the two closer movies. Candidates `15` and `20` also have the same year difference, so local ID orders that remaining tie. Candidate `30` confirms that a closer release year never outweighs fewer shared genres.

## Layer responsibilities

- The router validates `movie_id` and `limit`, then converts the service result to the public response schema.
- The service owns source lookup, exclusion, ranking, and the result limit.
- The repository reads local movie records and does not commit transactions.
- Genre normalization belongs in application schemas so create and update requests share one contract.
- The recommendation read path does not commit, write, or contact an external integration.

Implementation begins in ANT-26 with persistent local genres. Ranking and the endpoint remain separate tasks so their behavior can be reviewed independently.
