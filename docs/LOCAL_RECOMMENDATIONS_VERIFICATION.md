# Local recommendation verification — ANT-30

Verified on 2026-09-16 from an empty, disposable PostgreSQL database.

## Scope and isolation

The check used a dedicated PostgreSQL cluster in `/private/tmp/ant30-pg-cluster`, port `55434`, and database `movie_recommendation_ant30_demo`. It did not read or change the normal development database, Docker volumes, or TMDB data. The API received an invalid placeholder TMDB URL and token because the verified movie, seed, and recommendation paths are local-only.

The temporary database server and API were stopped after verification. The cluster directory was retained so no PostgreSQL data was deleted automatically.

## Reproduce the empty-database setup

Choose unused paths and ports if these values already exist:

```bash
/opt/homebrew/bin/initdb \
  -D /private/tmp/ant30-pg-cluster \
  -A trust \
  --username=ant30 \
  --no-locale

/opt/homebrew/bin/pg_ctl \
  -D /private/tmp/ant30-pg-cluster \
  -l /private/tmp/ant30-pg.log \
  -o '-p 55434 -h 127.0.0.1' \
  start -w

/opt/homebrew/bin/createdb \
  -h 127.0.0.1 \
  -p 55434 \
  -U ant30 \
  movie_recommendation_ant30_demo
```

Set application configuration for the disposable database:

```bash
export DATABASE_URL='postgresql+asyncpg://ant30@127.0.0.1:55434/movie_recommendation_ant30_demo'
export TMDB_BASE_URL='https://tmdb.invalid/3'
export TMDB_READ_ACCESS_TOKEN='test-fake-token'
export TMDB_TIMEOUT_SECONDS='5'
export APP_TITLE='ANT30'
export APP_VERSION='test'
```

Apply migrations and seed the catalog explicitly:

```bash
.venv/bin/alembic upgrade head
.venv/bin/python -m app.cli.seed_demo
```

The migration result was revision `8f3a2d7c1b4e`. The database contained zero movies before the seed, and the first seed reported:

```text
Demo catalog ready: created=12, skipped=0.
```

## Verify idempotency and preservation

Start the API:

```bash
.venv/bin/python -m uvicorn app.main:app \
  --host 127.0.0.1 \
  --port 18030
```

The fresh seed assigned local ID `1` to `Orbit of Glass`. Add a marker while retaining its title, year, and genres, then repeat the seed:

```bash
curl --fail -X PUT \
  -H 'Content-Type: application/json' \
  --data '{"title":"Orbit of Glass","release_year":1998,"description":"ANT-30 preserved marker","genres":["drama","science fiction"]}' \
  http://127.0.0.1:18030/movies/1

.venv/bin/python -m app.cli.seed_demo
curl --fail http://127.0.0.1:18030/movies/1
```

The second seed reported:

```text
Demo catalog ready: created=0, skipped=12.
```

`GET /movies/1` still returned the marker, and the database still contained exactly 12 movies. The repeated seed therefore added no duplicate and did not overwrite the existing record.

## Verify recommendations

Request five recommendations for the source movie:

```bash
curl --fail \
  'http://127.0.0.1:18030/movies/1/recommendations?limit=5'
```

The response returned local IDs in this order:

```text
2, 3, 4, 5, 6
```

They corresponded to `The Quiet Signal`, `Winter at Meridian`, `Copper Sky`, `Last Train to Solace`, and `Paper Constellations`. Every item included the expected shared genre. The order follows the documented rules: shared-genre count descending, release-year distance ascending, then local ID ascending.

The remaining response cases were:

| Request | Result |
| --- | --- |
| `GET /movies/999/recommendations` | `404`, existing movie-not-found response |
| `GET /movies/1/recommendations?limit=21` | `422`, rejected before recommendation logic |
| Recommendations for a temporary movie whose only genre was `western` | `200` with an empty `recommendations` list |

The error cases can be repeated without changing data:

```bash
curl -i http://127.0.0.1:18030/movies/999/recommendations
curl -i \
  'http://127.0.0.1:18030/movies/1/recommendations?limit=21'
```

## Verify local CRUD

A disposable movie was created, read, updated, and deleted through HTTP:

```bash
curl --fail -X POST \
  -H 'Content-Type: application/json' \
  --data '{"title":"ANT-30 Prairie Solo","release_year":2024,"description":"Disposable CRUD check","genres":["western"]}' \
  http://127.0.0.1:18030/movies/

curl --fail http://127.0.0.1:18030/movies/13
curl --fail http://127.0.0.1:18030/movies/13/recommendations

curl --fail -X PUT \
  -H 'Content-Type: application/json' \
  --data '{"title":"ANT-30 Prairie Solo Updated","release_year":2025,"description":"Updated disposable CRUD check","genres":["western"]}' \
  http://127.0.0.1:18030/movies/13

curl --fail -X DELETE http://127.0.0.1:18030/movies/13
curl -i http://127.0.0.1:18030/movies/13
```

In a fresh database this disposable movie receives ID `13`. If the database already contains other records, use the ID returned by `POST` in the later commands.

| Operation | Result |
| --- | --- |
| `POST /movies/` | `201`, local ID `13` |
| `GET /movies/13` | `200`, created fields preserved |
| `PUT /movies/13` | `200`, title, year, and description updated |
| `DELETE /movies/13` | `204` |
| `GET /movies/13` after deletion | `404` |

The temporary record was removed, leaving the 12 demo movies. The modified demo description remained only inside this disposable database.

## Automated checks and boundaries

The repository checks completed with 120 tests passing and Ruff reporting no errors. Endpoint tests replace the recommendation service, while service and repository tests use controlled local objects or database mocks; they do not contact TMDB.

The demo records are application-authored local data. The seed command is opt-in and does not run during application startup, Alembic migrations, Docker entrypoint execution, or CI. Recommendation requests read PostgreSQL only and do not call TMDB, import provider content, or use an ML/AI model. Any future ML/AI work remains behind the provider-terms decision in [the external movie API document](EXTERNAL_MOVIE_API.md).

Stop the disposable services when finished:

```bash
# Stop the API with Ctrl+C, then stop PostgreSQL.
/opt/homebrew/bin/pg_ctl -D /private/tmp/ant30-pg-cluster stop -w
```
