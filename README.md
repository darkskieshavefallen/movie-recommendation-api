![Python](https://img.shields.io/badge/Python-3.13-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.x-009688)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)
[![CI](https://github.com/darkskieshavefallen/movie-recommendation-api/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/darkskieshavefallen/movie-recommendation-api/actions/workflows/ci.yml)
![License](https://img.shields.io/badge/license-MIT-green)

# Movie Recommendation API

[Русская версия](README.ru.md)

A learning backend built with FastAPI, async SQLAlchemy, PostgreSQL, Alembic,
Pydantic v2, and pytest. It provides local movie CRUD, an opt-in fictional demo
catalog, and deterministic local recommendations. Read-only TMDB search is an
optional capability; the local API starts and works without a TMDB token.

The React frontend is planned as a separate repository. This repository remains
the backend and HTTP contract.

## Architecture

```mermaid
flowchart LR
    UI[React frontend<br/>separate repository] -->|HTTP + configured CORS| API[FastAPI routers]
    API --> S[Services<br/>business logic + transactions]
    S --> R[Repositories<br/>data access]
    R --> DB[(PostgreSQL)]
    API --> ES[External movie service]
    ES -. only when enabled .-> TMDB[TMDB API]
```

```mermaid
flowchart TD
    Start[Application startup] --> Enabled{TMDB_ENABLED?}
    Enabled -->|false| Local[Local catalog, recommendations,<br/>health and docs available]
    Local --> Disabled[External search returns safe 503]
    Enabled -->|true| Token{Token configured?}
    Token -->|no| Refuse[Configuration validation stops startup]
    Token -->|yes| Client[Managed async TMDB client]
```

The application keeps the `API -> Service -> Repository -> PostgreSQL`
boundary. Routers own HTTP concerns, services own business logic and transaction
boundaries, and repositories never commit.

## Quick start with Docker

Prerequisites: Git and Docker Desktop or Docker Engine with the Compose plugin.
A TMDB account or token is not required for the local application core.

```bash
git clone https://github.com/darkskieshavefallen/movie-recommendation-api.git
cd movie-recommendation-api
cp .env.example .env
docker compose up --build
```

Compose starts PostgreSQL 16, waits for it to become healthy, applies all
Alembic migrations, and starts the API on `http://127.0.0.1:8000`.

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- Liveness: http://127.0.0.1:8000/health
- Database readiness: http://127.0.0.1:8000/health/db

Stop containers while retaining local data:

```bash
docker compose down
```

`docker compose down --volumes` also deletes the development database volume.

## Local Python run

Prerequisites: Python 3.13 and PostgreSQL 16.

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
cp .env.example .env
# Adjust DATABASE_URL for your local PostgreSQL instance.
.venv/bin/alembic upgrade head
.venv/bin/python -m uvicorn app.main:app --reload
```

Configuration is loaded from environment variables and the local `.env` file.
Never commit real credentials. See [.env.example](.env.example) for every
runtime setting.

## Optional TMDB search

TMDB is disabled by default. In this mode, all local routes remain available and
`GET /external/movies/search` returns `503` with a stable, safe message.

To enable read-only search, set both values in `.env`:

```dotenv
TMDB_ENABLED=true
TMDB_READ_ACCESS_TOKEN=your_real_read_access_token
```

The token is sent only in the provider Authorization header. External results
are never imported into the local database. Provider terms, attribution, error
mapping, and the ML/AI restriction are documented in
[docs/EXTERNAL_MOVIE_API.md](docs/EXTERNAL_MOVIE_API.md).

## CORS for a separate frontend

The default configuration allows the usual local Vite origin and never uses a
global origin wildcard:

```dotenv
CORS_ALLOWED_ORIGINS=["http://localhost:5173"]
```

For several frontends, provide a JSON list of explicit origins:

```dotenv
CORS_ALLOWED_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]
```

Origins with credentials, paths, query strings, fragments, duplicates, or `*`
are rejected during configuration validation.

## API summary

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Process liveness |
| `GET` | `/health/db` | PostgreSQL readiness |
| `GET` | `/movies/?offset=0&limit=100` | Stable ascending-ID page of local movies |
| `POST` | `/movies/` | Create a local movie |
| `GET` | `/movies/{movie_id}` | Read one local movie |
| `PUT` | `/movies/{movie_id}` | Replace one local movie |
| `DELETE` | `/movies/{movie_id}` | Delete one local movie |
| `GET` | `/movies/{movie_id}/recommendations?limit=5` | Deterministic local recommendations |
| `GET` | `/external/movies/search?query=Alien` | Optional read-only TMDB search |

Movie write constraints are enforced by both Pydantic and PostgreSQL:

- `title`: trimmed, 1-255 characters;
- `release_year`: 1888-2100;
- `genres`: at most 10 unique normalized values, each at most 50 characters.

Invalid request data returns `422` before repository access. Movie pages retain
the existing `offset` and `limit` parameters and are ordered by local ID, so
pagination is deterministic. Recommendations use only local PostgreSQL data and
rank by shared genre count, release-year distance, then local ID.

When upgrading from the pre-ANT-38 schema, the constraint migration removes
only incompatible disposable demo/test rows: blank titles and years outside
1888-2100. Valid existing rows are retained.

## Demo catalog

The explicit development command inserts missing fictional demo movies and does
not overwrite existing title/year pairs:

```bash
.venv/bin/python -m app.cli.seed_demo
```

It is not part of startup or migrations and refuses non-local,
production-looking database targets.

## Checks

Fast checks need no PostgreSQL or TMDB token:

```bash
.venv/bin/python -m ruff check .
.venv/bin/python -m pytest -q -m "not integration"
```

Database-backed tests require an explicitly named disposable database:

```bash
INTEGRATION_DATABASE_URL='postgresql+asyncpg://integration:integration@localhost/movie_recommendation_integration_test' \
  .venv/bin/python -m pytest -q -m integration
```

The integration suite applies real migrations and verifies the full
`HTTP -> FastAPI -> Service -> Repository -> PostgreSQL` path. Safety rules and
setup details are in
[docs/POSTGRESQL_INTEGRATION_TESTS.md](docs/POSTGRESQL_INTEGRATION_TESTS.md).

CI runs Ruff/unit tests and PostgreSQL integration tests independently. Docker
build and smoke verification start only after both jobs pass. Publishing to GHCR
is limited to successful pushes to `main`.

## Documentation

- [Current project context](docs/PROJECT_CONTEXT.md)
- [Local recommendation contract](docs/LOCAL_RECOMMENDATIONS.md)
- [External catalog decision and boundaries](docs/EXTERNAL_MOVIE_API.md)
- [PostgreSQL integration test contract](docs/POSTGRESQL_INTEGRATION_TESTS.md)
- [Docker verification](docs/DOCKER_VERIFICATION.md)
- [CI and image delivery verification](docs/CI_VERIFICATION.md)

## Roadmap

- [x] Async CRUD with PostgreSQL and Alembic
- [x] Docker, CI, and verified GHCR image delivery
- [x] Optional external catalog search
- [x] Local deterministic recommendations
- [x] PostgreSQL integration test suite
- [x] Backend stabilization for a separate frontend
- [ ] React frontend in a separate repository
- [ ] Server deployment

## License

Licensed under the [MIT License](LICENSE).
