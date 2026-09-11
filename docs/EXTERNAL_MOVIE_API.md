# External movie catalog decision and contract

Updated: 2026-09-12. Provider facts and terms were checked against the official sources linked below.

## Decision

Sprint 17 will use The Movie Database (TMDB) API v3 for read-only movie search. The application will call one provider operation, `GET /3/search/movie`, and translate its response into the application's own schema. No provider payload will cross the integration boundary unchanged.

This decision covers a catalog-search-only application with no ML or AI component. TMDB's current API terms prohibit using the TMDB APIs or TMDB content in connection with a machine-learning or AI-based application. Before any ML or AI component is added to this application or its connected deployment, the project must obtain written TMDB permission that covers the combined use, replace TMDB with a provider whose terms permit it, or remove and fully separate the TMDB integration from the ML/AI application. Merely preventing TMDB data from entering the model is not sufficient.

## Provider comparison

| Area | TMDB API v3 | OMDb API |
| --- | --- | --- |
| Authentication | API Read Access Token in `Authorization: Bearer <token>`; an `api_key` query parameter is also supported | API key in the `apikey` query parameter |
| Free access | Free for non-commercial use with required attribution | Free key with a documented limit of 1,000 requests per day |
| Rate limits | Approximate upper limit around 40 requests per second; TMDB says it can change and clients must respect `429` | The official free-key page gives a daily quota but does not document a per-second limit or `Retry-After` behavior |
| Search data | Search results already include ID, localized and original title, overview, release date, language, popularity, votes, genre IDs, and image paths | Search results provide IMDb ID, title, year, type, and poster; richer data needs a lookup by ID/title |
| Errors and availability | Documents HTTP/status codes including `401`, `429`, `500`, `502`, `503`, and `504`; no SLA | Error details are less explicit in the API reference; the terms disclaim availability and the official site does not publish an SLA |
| Attribution and terms | Requires an approved TMDB logo and a prominent notice; non-commercial use is free, commercial use needs an agreement, cached content is limited to six months, and ML/AI use is restricted | Site content is marked CC BY-NC 4.0; the terms limit use to personal, non-commercial purposes and the Poster API is patron-only |

TMDB is selected because its search result already contains every field needed by the current application, its authentication avoids placing the token in the URL, and its error contract supports clear application-owned failure handling. Its documentation is also more complete for an educational async client. OMDb remains a possible fallback if TMDB's access or terms become incompatible with the search-only scope.

## Provider request

The integration client will make this request:

```text
GET https://api.themoviedb.org/3/search/movie
Authorization: Bearer <TMDB read access token>
Accept: application/json

query=<trimmed user query>
include_adult=false
language=en-US
page=1
```

Only the first provider page is required in Sprint 17. Search, details, images, genres, and discovery must not be combined speculatively. `GET /3/movie/{movie_id}` is not needed because the search payload already supplies the minimal application fields.

The base URL, read access token, and timeout will be application settings in ANT-19. The token remains in the request header, local environment, and deployment secret storage; it must not appear in source control, logs, exception text, or query strings.

## Application search contract

The planned public operation is:

```text
GET /external/movies/search?query=<movie title>
```

`query` is trimmed before use and must contain between 1 and 200 characters. Missing, empty, whitespace-only, or overlong values fail validation before any provider request.

The provider-independent response has one stable shape for zero, one, or many matches:

```json
{
  "query": "Alien",
  "results": [
    {
      "external_id": "348",
      "title": "Alien",
      "release_year": 1979,
      "description": "During its return to Earth, the commercial spaceship Nostromo intercepts a distress signal..."
    }
  ]
}
```

`external_id` is an opaque string owned by the external-catalog boundary. It is not a local PostgreSQL movie ID. `release_year` and `description` are nullable because the provider can omit release dates or overview text. Search is read-only and does not create or update local movie records.

## Field mapping

| TMDB field | Application field | Rule |
| --- | --- | --- |
| `id` | `external_id` | Required integer converted to a decimal string |
| `title` | `title` | Required non-empty string |
| `release_date` | `release_year` | First four digits converted to an integer; missing or empty becomes `null` |
| `overview` | `description` | Trimmed string; missing or empty becomes `null` |

`original_title`, `original_language`, `adult`, `genre_ids`, image paths, popularity, and vote fields are intentionally ignored. This keeps the contract aligned with the existing local movie shape and avoids exposing TMDB-specific concepts. If a required result field has the wrong type or the response envelope is invalid, the whole upstream response is treated as malformed instead of returning partially trusted data.

## Failure contract

Integration code will raise application-owned exceptions. The API layer will map them to stable responses without returning the TMDB body, token, URL query, or HTTPX exception text.

| Situation | Internal classification | Public behavior |
| --- | --- | --- |
| Missing, blank, or invalid application query | Request validation | `422 Unprocessable Entity`; provider is not called |
| Valid search with no TMDB matches | Successful empty result | `200 OK` with the normalized query and `results: []` |
| TMDB `401` or `403` | Provider authentication/configuration failure | `502 Bad Gateway` with a generic external-provider message |
| TMDB `429` | Provider rate limit | `503 Service Unavailable`; a valid `Retry-After` may be forwarded |
| Client timeout or TMDB `504` | Provider timeout | `504 Gateway Timeout` |
| Connection failure or TMDB `500`, `502`, or `503` | Provider unavailable | `503 Service Unavailable` |
| Invalid JSON, invalid envelope, or invalid required result fields | Invalid provider response | `502 Bad Gateway` |
| Other unexpected provider `4xx` | Provider request failure | `502 Bad Gateway` |

These mappings distinguish problems the caller can fix from failures at the external boundary. Logs may include the provider status and application error category, but never credentials or raw response bodies.

## Attribution and operating boundaries

Before the endpoint is exposed outside local development, the product must include an approved TMDB logo and this required notice in an About or Credits surface:

> This product uses TMDB and the TMDB APIs but is not endorsed, certified, or otherwise approved by TMDB.

The learning project is non-commercial. Commercial use requires a separate agreement with TMDB. Cached TMDB content must not be retained longer than six months. There is no provider SLA, so timeouts and unavailable responses are part of the normal integration contract. Terms, attribution requirements, and rate-limit guidance must be checked again before deployment or any expansion beyond read-only search. Adding any ML/AI component is blocked until one of the permission, provider-replacement, or full-separation options in the decision section is completed and documented.

## Official sources

### TMDB

- [Getting started](https://developer.themoviedb.org/docs/getting-started)
- [Application authentication](https://developer.themoviedb.org/docs/authentication-application)
- [Movie search](https://developer.themoviedb.org/reference/search-movie)
- [Search result and details workflow](https://developer.themoviedb.org/docs/search-and-query-for-details)
- [Errors](https://developer.themoviedb.org/docs/errors)
- [Rate limiting](https://developer.themoviedb.org/docs/rate-limiting)
- [FAQ, free use, SLA, and attribution](https://developer.themoviedb.org/docs/faq)
- [API Terms of Use](https://www.themoviedb.org/api-terms-of-use)

### OMDb

- [API reference and license notice](https://www.omdbapi.com/)
- [Official OpenAPI/Swagger description](https://www.omdbapi.com/swagger.json)
- [API key plans and free daily limit](https://www.omdbapi.com/apikey.aspx)
- [Terms of Use](https://www.omdbapi.com/legal.htm)
