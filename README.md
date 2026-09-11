![Python](https://img.shields.io/badge/Python-3.13-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.x-red)
[![CI](https://github.com/darkskieshavefallen/movie-recommendation-api/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/darkskieshavefallen/movie-recommendation-api/actions/workflows/ci.yml)
![License](https://img.shields.io/badge/license-MIT-green)

# Movie Recommendation API

> A learning project focused on building a production-ready REST API using FastAPI, PostgreSQL, SQLAlchemy Async, and modern Python development practices.

Currently implements movie CRUD. External movie API integration and the recommendation engine are planned.

---

## Features

- Async REST API built with FastAPI
- Layered architecture (API → Service → Repository)
- Dependency Injection using FastAPI
- Global exception handling
- Centralized logging to stdout, configurable through `LOG_LEVEL`
- Request validation
- PostgreSQL with SQLAlchemy 2.x Async ORM
- Database migrations with Alembic
- Data validation using Pydantic v2
- Centralized configuration with pydantic-settings
- Automatic OpenAPI & Swagger documentation
- Code quality with Ruff
- Service, dependency, and entrypoint tests using pytest

---

## Tech Stack

- Python 3.13
- FastAPI
- PostgreSQL
- SQLAlchemy 2.x (Async ORM)
- Alembic
- Pydantic v2
- pydantic-settings
- asyncpg
- HTTPX
- pytest
- Ruff

---

## Architecture

```text
                HTTP Request
                     │
                     ▼
              FastAPI Routers
                     │
                     ▼
                 Services
                     │
                     ▼
              Repositories
                     │
                     ▼
                PostgreSQL


        Domain Exceptions
               │
               ▼
      Exception Handlers
               │
               ▼
          HTTP Responses
```

---

## Project Structure

```text
app/
├── api/
│   ├── dependencies.py
│   ├── exception_handlers.py
│   ├── health.py
│   └── movies.py
│
├── core/
│   ├── database.py
│   ├── exceptions.py
│   ├── logging.py
│   └── settings.py
│
├── integrations/
├── models/
├── repositories/
├── schemas/
├── services/

tests/
alembic/
```

---

## Run with Docker Compose

Prerequisites: Git, a TMDB API Read Access Token, and Docker Desktop running (macOS/Windows), or Docker Engine with the Compose plugin (Linux). Port 8000 must be free. The first build needs Internet access to download images and Python dependencies. Local Python, a virtual environment, and a local PostgreSQL server are not required.

```bash
git clone https://github.com/darkskieshavefallen/movie-recommendation-api.git
cd movie-recommendation-api
cp .env.example .env
# Replace TMDB_READ_ACCESS_TOKEN in .env with your own token.
docker compose up --build
```

Run all Compose commands from the repository root.

Compose starts PostgreSQL, waits for its healthcheck, applies Alembic migrations, and then starts Uvicorn. A migration failure stops API startup. Open [Swagger UI](http://localhost:8000/docs).

Docker Compose requires `TMDB_READ_ACCESS_TOKEN` from the shell environment or the local `.env` file; the value is passed to the container at runtime and is not stored in the image or Compose file. Compose provides safe defaults for `TMDB_BASE_URL`, `TMDB_TIMEOUT_SECONDS`, `APP_TITLE`, `APP_VERSION`, and `LOG_LEVEL`. The container receives its own `DATABASE_URL` with host `db`. Keep the local URL pointing to `localhost`; no switching is needed. `.env` is excluded from the build context.

This is a development setup: the Docker database uses the explicit `movie_app` / `movie_app_dev` credentials from Compose. It is separate from any PostgreSQL database installed on your computer. PostgreSQL has no published host port; API is available only on `127.0.0.1:8000`.

```bash
# Start in the background and inspect services/logs.
docker compose up --build -d
docker compose ps
docker compose logs -f api

# Check the running API and its database connection.
curl --fail http://localhost:8000/health
curl --fail http://localhost:8000/health/db
curl --fail http://localhost:8000/movies/

# Stop and remove containers; retain the database volume.
docker compose down

# Recreate containers using the existing database.
docker compose up -d
```

Data is stored in the named `postgres_data` volume (normally `movie-recommendation-api_postgres_data`). Keep the same Compose project name to reuse it. `docker compose down` retains this volume; `docker compose down --volumes` deletes its data. Rebuild after source changes with `docker compose up --build -d`; there are no bind mounts or automatic reload in this setup.

If `docker` is not found on macOS, restart your terminal after installing Docker Desktop or add its CLI directory to the current shell:

```bash
export PATH="$HOME/.docker/bin:/Applications/Docker.app/Contents/Resources/bin:$PATH"
```

If Docker cannot connect to its engine, start Docker Desktop. If port 8000 is occupied by local Uvicorn, stop that process before starting Compose.

## Run Locally without Docker

Prerequisites: Python 3.13 and a running PostgreSQL server. Run the commands below from the repository root.

### 1. Clone the repository

```bash
git clone https://github.com/darkskieshavefallen/movie-recommendation-api.git
cd movie-recommendation-api
```

### 2. Create a virtual environment

```bash
python3.13 -m venv .venv
```

### 3. Activate the virtual environment

**Windows**

```bash
.venv\Scripts\activate
```

**Linux/macOS**

```bash
source .venv/bin/activate
```

### 4. Install dependencies

```bash
python -m pip install -e ".[dev]"
```

### 5. Create a local configuration file

```bash
cp .env.example .env
```

Create a PostgreSQL login role and a database owned by that role using your PostgreSQL administrator account. For example, in `psql` (only if they do not already exist):

```sql
CREATE ROLE movie_app WITH LOGIN PASSWORD 'replace_with_your_local_password';
CREATE DATABASE movie_recommendation OWNER movie_app;
```

Set `DATABASE_URL` in `.env` to match your role, password, host, port, and database:

```text
postgresql+asyncpg://movie_app:<your-password>@localhost:5432/movie_recommendation
```

URL-encode special characters in the password. Keep `.env` local. Settings load it relative to the working directory; migrations create tables, but do not create the PostgreSQL role or database.

Request a TMDB API Read Access Token from your TMDB account settings and replace the safe `TMDB_READ_ACCESS_TOKEN` placeholder. `TMDB_BASE_URL` must be an HTTPS URL without embedded credentials, query, or fragment. `TMDB_TIMEOUT_SECONDS` must be a finite positive number. Missing or invalid required values stop application startup with a Pydantic validation error that names the affected setting.

### 6. Apply database migrations

```bash
alembic upgrade head
```

### 7. Run the application

```bash
python -m uvicorn app.main:app --reload
```

---

## Available Endpoints

| Method | Endpoint | Description |
|---------|----------|-------------|
| GET | `/health` | Application health check (does not access PostgreSQL) |
| GET | `/health/db` | Database connectivity check (`SELECT 1`) |
| GET | `/movies/` | List movies with offset/limit pagination |
| GET | `/movies/{id}` | Get movie by ID |
| POST | `/movies/` | Create a movie |
| PUT | `/movies/{id}` | Update a movie |
| DELETE | `/movies/{id}` | Delete a movie |

---

## API Documentation

### Swagger UI

```text
http://localhost:8000/docs
```

### ReDoc

```text
http://localhost:8000/redoc
```

---

## Development Principles

- Layered architecture
- Thin API routers
- Business logic in services
- Data access in repositories
- Dependency Injection
- Domain exceptions separated from HTTP
- Async-first approach
- Type hints everywhere
- PEP 8 compliant code
- Small, focused commits

---

## Checks and Current Sprint

Run unit tests and lint checks from the repository root (Linux/macOS):

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check .
```

To run checks inside the built image without invoking startup migrations:

```bash
docker compose run --rm --no-deps --entrypoint python api -m pytest -q
docker compose run --rm --no-deps --entrypoint python api -m ruff check .
```

On Windows, use `.venv\Scripts\python.exe`. If cache writes are restricted, add `-p no:cacheprovider` to pytest and `--no-cache` to Ruff.

Verified on 2026-09-08: all 16 tests pass and Ruff checks pass. Update/delete explicitly roll back the lookup transaction before re-raising `MovieNotFoundError`; the API handler remains responsible for logging the 404. FastAPI dependencies use `Annotated`; a request-level test verifies the shared session and dependency cleanup. OpenAPI is unchanged after the dependency refactor. The unit tests do not require a live database. A separate Docker smoke check verified fresh startup, automatic migrations, health endpoints, Swagger, CRUD, and persistence after container recreation; see [verification results](docs/DOCKER_VERIFICATION.md).

The Docker sprint (ANT-5–ANT-11) was merged into `main` through [PR #8](https://github.com/darkskieshavefallen/movie-recommendation-api/pull/8).

### Continuous integration and image publishing (ANT-12–ANT-17)

The pipeline runs these stages in order:

1. Install the development dependencies on Python 3.13, then run Ruff and pytest.
2. Build the Dockerfile once and tag the image with the exact checked-out commit SHA.
3. Start that image with an isolated PostgreSQL service, verify the Alembic revision, and check `/health` plus `/health/db`.
4. On pushes to `main` only, transfer the verified image to a separate job and publish it to GHCR without rebuilding.

The CI badge at the top of this README reports the latest `main` workflow. Pull request checks validate stages 1–3 and skip publication. The first complete `main` delivery, including stage 4 and a pull-by-digest verification, succeeded after [PR #9](https://github.com/darkskieshavefallen/movie-recommendation-api/pull/9) was merged. Detailed evidence is recorded in [CI verification](docs/CI_VERIFICATION.md).

[GitHub Actions workflow](.github/workflows/ci.yml) runs on pull requests targeting `main` and pushes to `main`. Its `checks` job uses a fresh GitHub-hosted Ubuntu runner with Python 3.13. Steps check out the repository, install dependencies with `python -m pip install -e ".[dev]"`, and run Ruff followed by pytest using the commands above. A failed step fails the job; failures are not ignored.

The job's `env` block provides explicit non-sensitive application settings, including a fake TMDB URL and token, so CI needs no `.env` file or repository secrets and never contacts the real provider. The database URL is also a placeholder: existing unit tests mock database access and require no PostgreSQL service or migrations.

After Ruff and pytest pass, the same job builds the repository's Dockerfile with `docker build --tag "$CI_IMAGE" .`; the root `.dockerignore` filters the build context. `CI_IMAGE` is set to `movie-recommendation-api:<full-commit-sha>` using `git rev-parse HEAD` and passed to subsequent steps through `GITHUB_ENV`. For a pull request, the checked-out commit is normally GitHub's temporary merge commit, so the tag identifies the code actually tested.

The workflow checks that the image is present in the runner's local Docker image store with `docker image inspect`. The smoke check in the same job then reuses `$CI_IMAGE` without rebuilding. Build or inspection failures fail CI. On pull requests the local image disappears with the runner; on pushes to `main` the verified image continues to the publish job.

The [CI Compose file](.github/compose.ci.yml) starts the built API image and PostgreSQL 16 in a unique `movie-ci-<run-id>-<attempt>` project, with its own network and disposable database volume. It uses explicit CI credentials, reads no `.env`, publishes no host ports, and preserves the image's migration entrypoint. The development `docker-compose.yml` is not used or changed.

`docker compose up --no-build --wait --wait-timeout 120` waits for database and API healthchecks. The [verification script](.github/scripts/verify-smoke.sh) compares the database's `alembic_version` rows with the image's Alembic heads, then requires HTTP 200 from both `/health` and `/health/db` inside the API container. HTTP requests have five-second timeouts; startup and verification steps also have workflow time limits. Any failure fails CI. Failure logs are printed to the Actions log before cleanup; an `always()` step removes the CI project's containers, network, and database volume on success or failure. This smoke check verifies startup and connectivity, not full CRUD behavior.

For pull requests, CI stops after the smoke check and never authenticates to a registry or publishes an image. After a successful push to `main`, the checks job exports that same verified local image as a short-lived workflow artifact. A separate `publish` job downloads and loads it, verifies its Docker image ID, and pushes it without rebuilding to:

```text
ghcr.io/darkskieshavefallen/movie-recommendation-api:sha-<full-commit-sha>
```

Only the `publish` job receives `packages: write`; it logs in to GHCR with the workflow's `GITHUB_TOKEN`, so no personal token or repository secret is required. Publication is skipped when any prerequisite fails. The job summary records the tag and immutable registry digest as `<image>@sha256:<digest>`. The transfer artifact expires after one day. Deployment and a `latest` tag are outside this sprint step.

### Run an exact published image

The development command `docker compose up --build` still builds local source through [docker-compose.yml](docker-compose.yml). To verify a published artifact instead, use [docker-compose.ghcr.yml](docker-compose.ghcr.yml) through the bounded helper below. It contains `image:` and `pull_policy: always`, has no `build:` directive, and accepts only this repository's full `sha-<commit>` tag or registry digest:

```bash
bash .github/scripts/verify-published-image.sh \
  ghcr.io/darkskieshavefallen/movie-recommendation-api:sha-<full-commit-sha>

# The immutable digest reported by the publish job is also accepted:
bash .github/scripts/verify-published-image.sh \
  ghcr.io/darkskieshavefallen/movie-recommendation-api@sha256:<registry-digest>
```

The script must run from a machine with Docker and Internet access, and `TMDB_READ_ACCESS_TOKEN` must be available in its shell environment. Public GHCR packages can be pulled anonymously. For a private package, first authenticate with a GitHub personal access token (classic) that has `read:packages`; use your GitHub username and supply the token through stdin so it is not written in the command:

```bash
printf '%s' "$CR_PAT" | docker login ghcr.io \
  --username <github-username> --password-stdin
```

The helper creates a unique `movie-ghcr-verify-<pid>` Compose project, pulls the selected API image, starts it with a disposable PostgreSQL database, runs the existing Alembic-head and `/health` plus `/health/db` checks, and removes its containers, network, and volume on success or failure. The API is temporarily available on `127.0.0.1:18000`; set `API_PORT` before the command if that port is occupied. Failure logs are printed before cleanup. The normal development project's containers and `postgres_data` volume use a different project name and are not touched.

The first real pull was verified after the Sprint 16 merge. [Main run 34481819321](https://github.com/darkskieshavefallen/movie-recommendation-api/actions/runs/34481819321) published:

```text
ghcr.io/darkskieshavefallen/movie-recommendation-api:sha-64746bbb1ea442e0ea7dff14581ab173c6a87d00
ghcr.io/darkskieshavefallen/movie-recommendation-api@sha256:aca66f496b9eeead4fed2a17baf6f65aaecb6a87c9db9cb7ecf1c7b9b404e190
```

The helper pulled the immutable digest without a local build, started PostgreSQL and the API, confirmed Alembic revision `474e3311e20a`, received HTTP 200 from `/health` and `/health/db`, and removed its containers, network, and disposable volume.

### Current sprint: external movie catalog

Sprint 17 adds provider-independent, read-only movie search. ANT-18 selects TMDB API v3 and defines the smallest application contract, field mapping, error behavior, attribution requirements, and usage boundaries in [the external catalog decision](docs/EXTERNAL_MOVIE_API.md). ANT-19 adds validated provider settings and runtime-only token injection. ANT-20 defines the validated application schemas for search terms, normalized matches, and a stable result envelope. ANT-21 adds a reusable asynchronous TMDB client that translates mocked provider payloads into those schemas; provider error mapping and the endpoint remain later sprint tasks.

See [project context](docs/PROJECT_CONTEXT.md) for the agreed sequence and Docker decisions, and [AGENTS.md](AGENTS.md) for contributor instructions.

---

## Roadmap

- [x] Project setup
- [x] Application configuration
- [x] PostgreSQL integration
- [x] SQLAlchemy Async ORM
- [x] Alembic migrations
- [x] ORM models
- [x] Pydantic schemas
- [x] Repository layer
- [x] Service layer
- [x] Dependency Injection
- [x] REST API endpoints
- [x] Validation and exception handling
- [x] Update movie endpoint
- [x] Delete movie endpoint
- [x] Initial service unit tests
- [x] Resolve transaction-contract test failures
- [ ] Integration tests
- [x] Logging
- [x] Docker
- [x] CI checks, Docker build, and PostgreSQL smoke pipeline
- [x] GHCR publication and pull verification
- [ ] Server deployment
- [ ] External movie API integration
- [ ] Recommendation engine
- [ ] React frontend

---

## License

This project is licensed under the MIT License.
